import re
from typing import Dict, Any, Tuple, Set, List, Optional
from app.lexicon import lexicon_manager

COMMON_UNITS = r'(?:m/s\^2|m/s|kg|gm|mg|km/h|km|cm|mm|m|s|sec|min|hr|V|mV|kV|A|mA|W|kW|MW|Hz|kHz|MHz|GHz|J|kJ|N|kN|Pa|kPa|MPa|\u03A9|k\u03A9|M\u03A9|deg|rad|mol)'

class AnswerTermPinning:
    """
    Maintains per-answer state for dictionary term pinning across all segments.
    First mention: 'preferred_term (English Term)'
    Subsequent mentions: 'preferred_term'
    """
    def __init__(self, target_lang: str):
        self.target_lang = target_lang
        self.seen_terms: Set[str] = set()

    def get_replacement(self, eng_term: str, target_trans: str) -> str:
        clean_key = eng_term.lower().strip()
        # Clean target translation of any preexisting English brackets
        clean_trans = re.sub(r'\s*\([^)]*\)', '', target_trans).strip()
        if clean_key not in self.seen_terms:
            self.seen_terms.add(clean_key)
            return f"{clean_trans} ({eng_term.title()})"
        return clean_trans

class MaskingResult:
    def __init__(self, masked_text: str, placeholders: Dict[str, str], pin_terms: List[Tuple[str, str]]):
        self.masked_text = masked_text
        self.placeholders = placeholders
        self.pin_terms = pin_terms

def mask_content(text: str, target_lang: str, answer_state: Optional[AnswerTermPinning] = None) -> MaskingResult:
    """
    Masks formulas, LaTeX, code, numbers with units, decimals, bold/italic, and glossary terms.
    Returns MaskingResult with masked_text and placeholder map.
    """
    placeholders: Dict[str, str] = {}
    ph_counter = 0

    def add_ph(prefix: str, original: str) -> str:
        nonlocal ph_counter
        tag = f"__{prefix}_{ph_counter}__"
        ph_counter += 1
        placeholders[tag] = original
        return tag

    work_text = text

    # 1. Mask block math $$...$$
    def repl_block_math(m):
        return add_ph("BMATH", m.group(0))
    work_text = re.sub(r'\$\$[\s\S]+?\$\$', repl_block_math, work_text)

    # 2. Mask inline math $...$
    def repl_inline_math(m):
        return add_ph("IMATH", m.group(0))
    work_text = re.sub(r'\$[^\$\n]+?\$', repl_inline_math, work_text)

    # 3. Mask code blocks ```...```
    def repl_code_block(m):
        return add_ph("CBLOCK", m.group(0))
    work_text = re.sub(r'```[\s\S]*?```', repl_code_block, work_text)

    # 4. Mask inline code `...`
    def repl_inline_code(m):
        return add_ph("ICODE", m.group(0))
    work_text = re.sub(r'`[^`\n]+`', repl_inline_code, work_text)

    # 5. Mask numbers with units (e.g. 9.8 m/s^2, 100 kg, 5 V)
    def repl_units(m):
        return add_ph("UNIT", m.group(0))
    work_text = re.sub(rf'\b\d+(?:\.\d+)?\s*{COMMON_UNITS}\b', repl_units, work_text, flags=re.IGNORECASE)

    # 6. Mask standalone decimal numbers (e.g. 9.8, 3.14)
    def repl_decimals(m):
        return add_ph("DEC", m.group(0))
    work_text = re.sub(r'\b\d+\.\d+\b', repl_decimals, work_text)

    # 7. Mask markdown bold **...**
    def repl_bold(m):
        return add_ph("BOLD", m.group(0))
    # We leave bold markers so markdown renders, or mask if they enclose math/numbers
    # Masking bold markers around complex tokens:
    work_text = re.sub(r'\*\*([^*]+?)\*\*', repl_bold, work_text)

    # 8. Glossary Term Pinning
    pin_terms: List[Tuple[str, str]] = []
    if target_lang in ("mr", "hi"):
        rel_terms = lexicon_manager.get_relevant_terms(text, target_lang, max_terms=15)
        # Sort by length descending to match longest phrases first
        rel_terms.sort(key=lambda t: len(t[0]), reverse=True)
        for eng_t, trans_t in rel_terms:
            pattern = rf'\b{re.escape(eng_t)}\b'
            if re.search(pattern, work_text, re.IGNORECASE):
                tag = f"__GLOSS_{ph_counter}__"
                ph_counter += 1
                replacement = (
                    answer_state.get_replacement(eng_t, trans_t)
                    if answer_state
                    else f"{trans_t} ({eng_t.title()})"
                )
                placeholders[tag] = replacement
                work_text = re.sub(pattern, tag, work_text, flags=re.IGNORECASE)
                pin_terms.append((eng_t, trans_t))

    return MaskingResult(masked_text=work_text, placeholders=placeholders, pin_terms=pin_terms)

def restore_content(translated_text: str, placeholders: Dict[str, str]) -> Tuple[str, bool]:
    """
    Restores masked placeholders into translated text.
    Verifies that every placeholder appears exactly once.
    Returns (restored_text, is_valid).
    """
    restored = translated_text
    is_valid = True

    for tag, original in placeholders.items():
        # Check occurrence count
        count = restored.count(tag)
        if count == 1:
            restored = restored.replace(tag, original, 1)
        elif count > 1:
            # Duplicated placeholder: replace first, drop or replace duplicates
            restored = restored.replace(tag, original)
            is_valid = False
        else:
            # Placeholder missing! Check fuzzy/case-insensitive
            match = re.search(re.escape(tag), restored, re.IGNORECASE)
            if match:
                restored = restored[:match.start()] + original + restored[match.end():]
            else:
                # Completely missing from model output
                is_valid = False
                # Append missing original at end or as note
                restored += f" {original}"

    # Verify no residual placeholders remained
    residual = re.findall(r'__(?:BMATH|IMATH|CBLOCK|ICODE|UNIT|DEC|BOLD|GLOSS)_\d+__', restored)
    if residual:
        is_valid = False

    return restored, is_valid
