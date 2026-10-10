"""Text normalisation used ONLY for security comparisons.

Claim-Check and the canary check compare model output against fixed things (banned
phrases, allowed numbers, a secret token). An attacker, or a model that was fooled,
can dodge a literal comparison by changing how the same words are written. This
module turns text into one canonical form before comparing.

The result is for MATCHING ONLY. Callers must keep and display the original text;
nothing here rewrites what a customer sees.

Steps, in order:
  1. NFKC normalisation: folds fullwidth letters and digits, compatibility forms
     (ligatures, superscripts) and unusual spaces and hyphens.
  2. Confusable folding: a small explicit table of Cyrillic and Greek letters that
     are visually identical to Latin letters is mapped to those Latin letters.
     Applied BEFORE case folding so capital lookalikes are covered too.
  3. Case folding.
  4. Decompose and drop combining marks, so "approved" still matches when an
     accent mark has been attached to one of its letters.
  5. Drop invisible format characters (zero-width space, joiners, bidi marks, soft
     hyphen, BOM).

What this is NOT: it is not a general transliteration. Only the letters listed in
CONFUSABLES are changed; every other letter, in any script, is left as it is.

Known limits:
- The table is small on purpose. Lookalikes from other scripts (for example
  Armenian or Cherokee) and lookalike digits (Latin O for 0) are not covered.
- Real Cyrillic or Greek words are also folded for comparison. That cannot hurt
  display, and it is very unlikely to spell a banned English phrase by accident.
- This does not detect meaning-preserving rewording ("will definitely save").
"""
import unicodedata
from typing import Dict

# code point -> Latin letter. Each entry is a letter whose standard glyph is, in
# common fonts, indistinguishable from the Latin letter it maps to.
CONFUSABLES: Dict[int, str] = {
    # --- Cyrillic, capital ---
    0x0410: "A",  # CYRILLIC CAPITAL LETTER A
    0x0412: "B",  # CYRILLIC CAPITAL LETTER VE
    0x0415: "E",  # CYRILLIC CAPITAL LETTER IE
    0x041A: "K",  # CYRILLIC CAPITAL LETTER KA
    0x041C: "M",  # CYRILLIC CAPITAL LETTER EM
    0x041D: "H",  # CYRILLIC CAPITAL LETTER EN
    0x041E: "O",  # CYRILLIC CAPITAL LETTER O
    0x0420: "P",  # CYRILLIC CAPITAL LETTER ER
    0x0421: "C",  # CYRILLIC CAPITAL LETTER ES
    0x0422: "T",  # CYRILLIC CAPITAL LETTER TE
    0x0423: "Y",  # CYRILLIC CAPITAL LETTER U
    0x0425: "X",  # CYRILLIC CAPITAL LETTER HA
    0x0406: "I",  # CYRILLIC CAPITAL LETTER BYELORUSSIAN-UKRAINIAN I
    0x0408: "J",  # CYRILLIC CAPITAL LETTER JE
    0x0405: "S",  # CYRILLIC CAPITAL LETTER DZE
    # --- Cyrillic, small ---
    0x0430: "a",  # CYRILLIC SMALL LETTER A
    0x0435: "e",  # CYRILLIC SMALL LETTER IE
    0x043A: "k",  # CYRILLIC SMALL LETTER KA
    0x043E: "o",  # CYRILLIC SMALL LETTER O
    0x0440: "p",  # CYRILLIC SMALL LETTER ER
    0x0441: "c",  # CYRILLIC SMALL LETTER ES
    0x0443: "y",  # CYRILLIC SMALL LETTER U
    0x0445: "x",  # CYRILLIC SMALL LETTER HA
    0x0456: "i",  # CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
    0x0458: "j",  # CYRILLIC SMALL LETTER JE
    0x0455: "s",  # CYRILLIC SMALL LETTER DZE
    0x04BB: "h",  # CYRILLIC SMALL LETTER SHHA
    0x0501: "d",  # CYRILLIC SMALL LETTER KOMI DE
    0x051B: "q",  # CYRILLIC SMALL LETTER QA
    0x051D: "w",  # CYRILLIC SMALL LETTER WE
    # --- Greek, capital ---
    0x0391: "A",  # GREEK CAPITAL LETTER ALPHA
    0x0392: "B",  # GREEK CAPITAL LETTER BETA
    0x0395: "E",  # GREEK CAPITAL LETTER EPSILON
    0x0396: "Z",  # GREEK CAPITAL LETTER ZETA
    0x0397: "H",  # GREEK CAPITAL LETTER ETA
    0x0399: "I",  # GREEK CAPITAL LETTER IOTA
    0x039A: "K",  # GREEK CAPITAL LETTER KAPPA
    0x039C: "M",  # GREEK CAPITAL LETTER MU
    0x039D: "N",  # GREEK CAPITAL LETTER NU
    0x039F: "O",  # GREEK CAPITAL LETTER OMICRON
    0x03A1: "P",  # GREEK CAPITAL LETTER RHO
    0x03A4: "T",  # GREEK CAPITAL LETTER TAU
    0x03A5: "Y",  # GREEK CAPITAL LETTER UPSILON
    0x03A7: "X",  # GREEK CAPITAL LETTER CHI
    # --- Greek, small ---
    0x03B1: "a",  # GREEK SMALL LETTER ALPHA
    0x03B9: "i",  # GREEK SMALL LETTER IOTA
    0x03BA: "k",  # GREEK SMALL LETTER KAPPA
    0x03BD: "v",  # GREEK SMALL LETTER NU
    0x03BF: "o",  # GREEK SMALL LETTER OMICRON
    0x03C1: "p",  # GREEK SMALL LETTER RHO
    0x03C5: "u",  # GREEK SMALL LETTER UPSILON
    # --- Other Latin-script lookalikes ---
    0x0131: "i",  # LATIN SMALL LETTER DOTLESS I
    0x0261: "g",  # LATIN SMALL LETTER SCRIPT G
}


def normalise(text: str) -> str:
    """Canonical form of `text` for security comparisons (never for display)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).translate(CONFUSABLES)
    text = text.casefold()
    decomposed = unicodedata.normalize("NFD", text)
    kept = [c for c in decomposed
            if unicodedata.category(c) not in ("Mn", "Cf")]
    return unicodedata.normalize("NFC", "".join(kept))
