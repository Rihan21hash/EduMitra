import os
import json
import logging
import unicodedata
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger("edumitra.lexicon")

class LexiconManager:
    def __init__(self):
        self.glossary: Dict[str, Dict[str, str]] = {}
        self.hindi_dict: Dict[str, str] = {}
        self.marathi_dict: Dict[str, str] = {}
        self.is_loaded = False

    def load(self, base_dir: Optional[str] = None):
        """Loads both dictionaries and the curated STEM glossary."""
        if self.is_loaded:
            return

        app_dir = Path(__file__).resolve().parent
        project_root = app_dir.parent.parent

        # 1. Load Curated Glossary (highest fidelity)
        glossary_path = app_dir / "data" / "glossary.json"
        if glossary_path.exists():
            try:
                with open(glossary_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.glossary[k.lower().strip()] = {
                            "mr": unicodedata.normalize("NFC", v.get("mr", "")),
                            "hi": unicodedata.normalize("NFC", v.get("hi", "")),
                            "en": v.get("en", k)
                        }
                logger.info(f"Loaded {len(self.glossary)} terms from curated glossary.")
            except Exception as e:
                logger.warning(f"Error loading glossary.json: {e}")

        # 2. Add expanded computer science & STEM terms to curated glossary
        cs_stem_terms = {
            "object": {"mr": "ऑब्जेक्ट / घटक", "hi": "ऑब्जेक्ट / वस्तु", "en": "object"},
            "class": {"mr": "क्लास / वर्ग", "hi": "क्लास / वर्ग", "en": "class"},
            "inheritance": {"mr": "वारसाहक्क (Inheritance)", "hi": "उत्तराधिकार / इनहेरिटेंस", "en": "inheritance"},
            "polymorphism": {"mr": "बहुरूपता (Polymorphism)", "hi": "बहुरूपता (Polymorphism)", "en": "polymorphism"},
            "encapsulation": {"mr": "कॅप्सूलीकरण (Encapsulation)", "hi": "कैप्सूलीकरण (Encapsulation)", "en": "encapsulation"},
            "abstraction": {"mr": "अमूर्तीकरण (Abstraction)", "hi": "अमूर्तीकरण (Abstraction)", "en": "abstraction"},
            "function": {"mr": "फंक्शन / कार्य", "hi": "फ़ंक्शन / कार्य", "en": "function"},
            "variable": {"mr": "चल / व्हेरिएबल", "hi": "चर / वेरिएबल", "en": "variable"},
            "recursion": {"mr": "रिकर्शन / पुनरावृत्ती", "hi": "रिकर्शन / पुनरावर्तन", "en": "recursion"},
            "algorithm": {"mr": "अल्गोरिदम / कार्यपद्धती", "hi": "एल्गोरिदम / कलन विधि", "en": "algorithm"},
            "database": {"mr": "डेटाबेस / माहितीसंच", "hi": "डेटाबेस / आँकड़ा संचय", "en": "database"},
            "compiler": {"mr": "कंपाइलर / अनुवादक", "hi": "कंपाइलर / अनुवादक", "en": "compiler"},
            "pointer": {"mr": "पॉइंटर / निर्देशक", "hi": "पॉइंटर / सूचक", "en": "pointer"},
            "array": {"mr": "अ‍ॅरे / सारणी", "hi": "ऐरे / व्यूह", "en": "array"},
            "queue": {"mr": "रांग (Queue)", "hi": "पंक्ति (Queue)", "en": "queue"},
            "stack": {"mr": "स्टॅक (Stack)", "hi": "ढेर / स्टैक", "en": "stack"},
            "newton": {"mr": "न्यूटन", "hi": "न्यूटन", "en": "Newton"},
            "law": {"mr": "नियम", "hi": "नियम", "en": "law"},
            "cell": {"mr": "पेशी", "hi": "कोशिका", "en": "cell"},
            "tissue": {"mr": "ऊती", "hi": "ऊतक", "en": "tissue"},
            "organ": {"mr": "अवयव / इंद्रिय", "hi": "अंग", "en": "organ"}
        }
        for k, v in cs_stem_terms.items():
            if k not in self.glossary:
                self.glossary[k] = v

        # 3. Locate Dictionary Directory
        dict_dir = None
        candidates = [
            project_root / "Dictionary",
            project_root / "dictionary",
            app_dir.parent / "Dictionary"
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                dict_dir = c
                break

        if not dict_dir:
            logger.warning("Dictionary directory not found.")
            self.is_loaded = True
            return

        # 4. Parse Hindi Dictionary
        hi_file = dict_dir / "English-to-Hindi-Dictionary.txt"
        if hi_file.exists():
            try:
                with open(hi_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                pages = content.split("\x0c")
                for p in pages:
                    lines = [l.strip() for l in p.splitlines() if l.strip()]
                    w_idx, m_idx = -1, -1
                    for i, l in enumerate(lines):
                        if "English Word" in l:
                            w_idx = i
                        elif "Hindi Meaning" in l:
                            m_idx = i
                    if w_idx != -1 and m_idx != -1 and m_idx > w_idx:
                        words = [w for w in lines[w_idx + 1:m_idx] if not any(x in w for x in ["Compiled By", "MANISH", "Accounts", "Hindalco"])]
                        meanings = [m for m in lines[m_idx + 1:] if not any(x in m for x in ["MANISH", "Accounts", "Hindalco"])]
                        for w, m in zip(words, meanings):
                            clean_w = w.lower().strip()
                            if clean_w and re.match(r"^[a-z\s\-\'\,]+$", clean_w):
                                norm_m = unicodedata.normalize("NFC", m)
                                for sw in clean_w.split(","):
                                    single = sw.strip()
                                    if single and single not in self.hindi_dict:
                                        self.hindi_dict[single] = norm_m
                logger.info(f"Loaded {len(self.hindi_dict)} entries from Hindi dictionary.")
            except Exception as e:
                logger.warning(f"Error parsing Hindi dictionary: {e}")

        # 5. Parse Marathi Dictionary
        mr_file = dict_dir / "English-to-Marathi-Dictionary.txt"
        if mr_file.exists():
            try:
                with open(mr_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
                curr_eng = None
                for line in lines:
                    has_dev = any("\u0900" <= ch <= "\u097f" for ch in line)
                    if not has_dev:
                        if re.match(r"^[A-Za-z][A-Za-z\s\-\']{1,35}$", line) and not line.endswith(";"):
                            curr_eng = line.lower()
                    else:
                        if curr_eng and curr_eng not in self.marathi_dict:
                            norm_mr = unicodedata.normalize("NFC", line)
                            self.marathi_dict[curr_eng] = norm_mr
                logger.info(f"Loaded {len(self.marathi_dict)} entries from Marathi dictionary.")
            except Exception as e:
                logger.warning(f"Error parsing Marathi dictionary: {e}")

        self.is_loaded = True

    def get_relevant_terms(self, text: str, target_lang: str, max_terms: int = 20) -> List[Tuple[str, str]]:
        """
        Extracts relevant vocabulary matches from the question and context text.
        Returns a list of (English Term, Target Language Translation) tuples.
        """
        if not self.is_loaded:
            self.load()

        if target_lang not in ("mr", "hi"):
            return []

        # Tokenize text into words and 2-grams
        raw_words = re.findall(r"[A-Za-z]+", text.lower())
        candidates = set(raw_words)
        for i in range(len(raw_words) - 1):
            candidates.add(f"{raw_words[i]} {raw_words[i+1]}")

        # Common stop words to ignore
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when",
            "where", "who", "which", "and", "or", "in", "on", "at", "to", "for", "with",
            "by", "of", "it", "this", "that", "these", "those", "can", "could", "will",
            "would", "should", "shall", "may", "might", "must", "give", "tell", "explain",
            "please", "me", "you", "che", "chya", "cha", "chi", "sang", "sanga", "aahe",
            "hoti", "hota", "kya", "hai", "batao", "samjhao"
        }

        matched: List[Tuple[str, str]] = []
        seen_eng = set()

        # Priority 1: Curated glossary
        for cand in candidates:
            if cand in stopwords:
                continue
            if cand in self.glossary:
                trans = self.glossary[cand].get(target_lang)
                if trans and cand not in seen_eng:
                    matched.append((cand.title(), trans))
                    seen_eng.add(cand)

        # Priority 2: Full dictionary
        active_dict = self.marathi_dict if target_lang == "mr" else self.hindi_dict
        for cand in candidates:
            if len(matched) >= max_terms:
                break
            if cand in stopwords or cand in seen_eng:
                continue
            if cand in active_dict:
                trans = active_dict[cand]
                matched.append((cand.title(), trans))
                seen_eng.add(cand)

        return matched[:max_terms]

    def format_for_prompt(self, terms: List[Tuple[str, str]], target_lang: str) -> str:
        """Formats extracted terms into prompt guidance."""
        if not terms:
            return ""

        lang_label = "मराठी" if target_lang == "mr" else "हिंदी"
        lines = [f"\n### प्रामाणिक शब्दकोश संदर्भ (Official {lang_label} Terminology - Use these terms):"]
        for eng, trans in terms:
            lines.append(f"- {eng} ➔ {trans} ({eng})")
        lines.append("पहिल्या उल्लेखावेळी प्रामाणिक शब्द वापरा आणि कंसात इंग्रजी संज्ञा ठेवा.\n")
        return "\n".join(lines)

lexicon_manager = LexiconManager()
