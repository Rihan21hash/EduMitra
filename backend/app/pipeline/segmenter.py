import re
from typing import List, Dict, Any, Optional

# Abbreviations that should NOT cause sentence splitting
ABBREVIATIONS = {
    "e.g.", "i.e.", "fig.", "figs.", "etc.", "vs.", "dr.", "prof.", "mr.", "mrs.", "ms.",
    "viz.", "al.", "approx.", "est.", "vol.", "dept.", "eq.", "eqs.", "ref.", "refs."
}

class Segment:
    def __init__(self, index: int, text: str, segment_type: str = "text", raw_prefix: str = "", raw_suffix: str = ""):
        self.index = index
        self.text = text.strip()
        self.segment_type = segment_type  # 'heading' | 'list_item' | 'text'
        self.raw_prefix = raw_prefix
        self.raw_suffix = raw_suffix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "text": self.text,
            "segment_type": self.segment_type,
            "raw_prefix": self.raw_prefix,
            "raw_suffix": self.raw_suffix
        }

    def __repr__(self) -> str:
        return f"Segment(idx={self.index}, type={self.segment_type}, text={repr(self.text)})"

class StreamSegmenter:
    """
    Splits streaming English text into natural translation segments (headings, list items, sentences).
    - Preserves formulas ($...$, $$...$$), code blocks, inline code.
    - Prevents splits on decimals (e.g. 9.8) and common abbreviations (e.g., i.e., Fig.).
    - Merges micro-segments (< 6 words) and forces flush at ~60 words.
    - Preserves sequential ordering with indexes.
    """
    def __init__(self, min_words: int = 5, max_words: int = 60):
        self.min_words = min_words
        self.max_words = max_words
        self.buffer = ""
        self.current_index = 0
        self.in_code_block = False

    def _word_count(self, text: str) -> int:
        return len(re.findall(r'\S+', text))

    def feed(self, chunk: str) -> List[Segment]:
        """Feed new streamed tokens and yield any complete segments."""
        if not chunk:
            return []

        self.buffer += chunk
        return self._extract_segments(is_final=False)

    def flush(self) -> List[Segment]:
        """Flush any remaining text at end of stream."""
        return self._extract_segments(is_final=True)

    def _extract_segments(self, is_final: bool = False) -> List[Segment]:
        segments: List[Segment] = []

        while self.buffer:
            # Check for multi-line blocks or line boundaries
            lines = self.buffer.split("\n")
            if len(lines) == 1 and not is_final:
                # Still accumulating first line; check if sentence boundary exists inside
                extracted = self._try_split_sentence(lines[0], is_final=False)
                if extracted:
                    seg_text, remainder = extracted
                    segments.append(self._create_segment(seg_text))
                    self.buffer = remainder
                    continue
                # If buffer exceeds max words, force flush at word boundary
                if self._word_count(self.buffer) >= self.max_words:
                    seg_text, remainder = self._force_flush_words(self.buffer)
                    if seg_text:
                        segments.append(self._create_segment(seg_text))
                        self.buffer = remainder
                        continue
                break

            # If we have complete lines or is_final
            if len(lines) > 1:
                first_line = lines[0]
                remainder = "\n".join(lines[1:])
                stripped_line = first_line.strip()

                # 1. Code fence boundary tracking
                if stripped_line.startswith("```"):
                    self.in_code_block = not self.in_code_block
                    # Keep entire code fence as segment or wait for block closure
                    segments.append(self._create_segment(first_line, segment_type="code_fence"))
                    self.buffer = remainder
                    continue

                if self.in_code_block:
                    # Inside code block, keep lines intact
                    segments.append(self._create_segment(first_line, segment_type="code"))
                    self.buffer = remainder
                    continue

                # 2. Heading line
                heading_match = re.match(r'^(#{1,6}\s+)(.+)$', stripped_line)
                if heading_match:
                    prefix = heading_match.group(1)
                    title = heading_match.group(2)
                    segments.append(self._create_segment(title, segment_type="heading", raw_prefix=prefix, raw_suffix="\n\n"))
                    self.buffer = remainder
                    continue

                # 3. List item line
                list_match = re.match(r'^(\s*[-*•]|\s*\d+\.)\s+(.+)$', stripped_line)
                if list_match:
                    prefix = list_match.group(1) + " "
                    item_text = list_match.group(2)
                    segments.append(self._create_segment(item_text, segment_type="list_item", raw_prefix=prefix, raw_suffix="\n"))
                    self.buffer = remainder
                    continue

                # 4. Empty line (paragraph break)
                if not stripped_line:
                    self.buffer = remainder
                    continue

                # 5. Regular text line: check if complete sentence or merge
                extracted = self._try_split_sentence(first_line, is_final=True)
                if extracted:
                    seg_text, sub_rem = extracted
                    segments.append(self._create_segment(seg_text))
                    if sub_rem.strip():
                        self.buffer = sub_rem + "\n" + remainder
                    else:
                        self.buffer = remainder
                    continue
                else:
                    # Line doesn't have internal sentence break; check length
                    if self._word_count(first_line) >= self.min_words or not remainder:
                        segments.append(self._create_segment(first_line))
                        self.buffer = remainder
                        continue
                    else:
                        # Micro-line: wait for more text
                        if is_final:
                            segments.append(self._create_segment(first_line))
                            self.buffer = remainder
                        break
            else:
                # Exactly 1 line left and is_final
                stripped = self.buffer.strip()
                if stripped:
                    segments.append(self._create_segment(stripped))
                self.buffer = ""
                break

        return segments

    def _create_segment(self, text: str, segment_type: str = "text", raw_prefix: str = "", raw_suffix: str = "") -> Segment:
        seg = Segment(
            index=self.current_index,
            text=text,
            segment_type=segment_type,
            raw_prefix=raw_prefix,
            raw_suffix=raw_suffix
        )
        self.current_index += 1
        return seg

    def _try_split_sentence(self, text: str, is_final: bool = False) -> Optional[tuple[str, str]]:
        """
        Looks for a safe sentence boundary in text.
        Returns (sentence, remainder) if found, else None.
        """
        # Look for punctuation followed by space or end of string
        # Regex matches sentence terminator (. ? !)
        pattern = re.compile(r'([\.\?!])(\s+|$)')
        for m in pattern.finditer(text):
            punc_pos = m.start(1)
            punc_char = m.group(1)
            end_match = m.end()

            # Guard 1: Not inside math ($...$ or $$...$$)
            preceding = text[:punc_pos]
            dollar_count = preceding.count("$")
            if dollar_count % 2 != 0:
                continue

            # Guard 2: Not inside code (``)
            backtick_count = preceding.count("`")
            if backtick_count % 2 != 0:
                continue

            # Guard 3: Decimal numbers (e.g. 9.8)
            if punc_char == "." and punc_pos > 0 and punc_pos + 1 < len(text):
                if text[punc_pos - 1].isdigit() and text[punc_pos + 1].isdigit():
                    continue

            # Guard 4: Abbreviations (e.g., i.e., Fig., etc.)
            last_word_match = re.search(r'([A-Za-z]+)\.$', text[:punc_pos + 1], re.IGNORECASE)
            if last_word_match:
                word_with_dot = last_word_match.group(0).lower()
                if word_with_dot in ABBREVIATIONS:
                    continue
                # Also check multi-part abbreviations like "e.g." or "i.e."
                if re.search(r'\b[A-Za-z]\.[A-Za-z]\.$', text[:punc_pos + 1], re.IGNORECASE):
                    continue

            # Guard 5: List item prefix (e.g. "1.")
            if punc_char == "." and re.match(r'^\s*\d+\.$', text[:punc_pos + 1]):
                continue

            # Found a valid split candidate
            candidate = text[:punc_pos + 1].strip()
            # Check minimum word length unless is_final
            if self._word_count(candidate) >= self.min_words or is_final:
                remainder = text[end_match:].strip()
                return (candidate, remainder)

        return None

    def _force_flush_words(self, text: str) -> tuple[str, str]:
        """Forces a split near max_words at a safe space boundary."""
        words = text.split()
        if len(words) <= self.max_words:
            return text, ""
        flush_part = " ".join(words[:self.max_words])
        remainder = " ".join(words[self.max_words:])
        return flush_part, remainder
