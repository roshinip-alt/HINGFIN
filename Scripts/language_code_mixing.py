"""
HINGFIN - Phase 1, Step 4
Language Identification and Code-Mixing Index

Input:
    Dataset/moneycontrol_clean_deduplicated.csv

Outputs:
    Dataset/moneycontrol_language_cmi.csv
    Dataset/moneycontrol_language_cmi.parquet
    Dataset/moneycontrol_language_cmi_report.json

Labels:
    EN
    HI_LATIN
    HI_DEVA
    NUM
    PUNCT
    EMOJI
    OTHER

CMI:
    100 * (1 - max(n_EN, n_HI) / N)

where:
    n_EN = English content tokens
    n_HI = HI_LATIN + HI_DEVA content tokens
    N = n_EN + n_HI

Posts with fewer than 3 content tokens:
    CMI = 0
    short_for_cmi = True
"""

from pathlib import Path
import json
import re
import unicodedata

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "Dataset"
    / "moneycontrol_clean_deduplicated.csv"
)

OUTPUT_CSV = (
    ROOT
    / "Dataset"
    / "moneycontrol_language_cmi.csv"
)

OUTPUT_PARQUET = (
    ROOT
    / "Dataset"
    / "moneycontrol_language_cmi.parquet"
)

REPORT_FILE = (
    ROOT
    / "Dataset"
    / "moneycontrol_language_cmi_report.json"
)


# ============================================================
# OPTIONAL LOCAL LEXICONS
# ============================================================

ENGLISH_LEXICON_FILE = (
    ROOT
    / "Dataset"
    / "english_lexicon.txt"
)

HINDI_LATIN_LEXICON_FILE = (
    ROOT
    / "Dataset"
    / "hindi_romanized_lexicon.txt"
)


# ============================================================
# REGEX
# ============================================================

TOKEN_PATTERN = re.compile(
    r"""
    https?://\S+
    |
    <[^>]+>
    |
    \$?[A-Za-z]+(?:['’][A-Za-z]+)?
    |
    [A-Za-z]+
    |
    [\u0900-\u097F]+
    |
    \d+(?:[.,]\d+)*
    |
    [^\w\s]
    """,
    re.VERBOSE,
)


# English-looking word
ENGLISH_WORD_PATTERN = re.compile(
    r"^[A-Za-z]+(?:['’][A-Za-z]+)?$"
)


# Devanagari
DEVANAGARI_PATTERN = re.compile(
    r"^[\u0900-\u097F]+$"
)


# Number
NUMBER_PATTERN = re.compile(
    r"^\d+(?:[.,]\d+)*$"
)


# ============================================================
# BASIC WORD LISTS
# ============================================================

# These are deliberately small fallback lists.
#
# For the final research version, use the project's intended
# English and Romanized-Hindi lexicons by putting them in:
#
# Dataset/english_lexicon.txt
# Dataset/hindi_romanized_lexicon.txt
#
# One word per line.

ENGLISH_FALLBACK = {
    "the", "a", "an", "is", "are", "was", "were",
    "be", "been", "being",
    "and", "or", "but", "if", "then", "than",
    "this", "that", "these", "those",
    "of", "to", "in", "on", "at", "for", "from",
    "with", "by", "as", "into", "about",
    "will", "would", "could", "should",
    "can", "may", "might",
    "good", "bad", "best", "worst",
    "buy", "sell", "hold",
    "target", "price", "stock", "share",
    "market", "profit", "loss",
    "growth", "fall", "rise", "rising", "falling",
    "strong", "weak",
    "today", "tomorrow", "yesterday",
    "company", "result", "results",
    "quarter", "revenue", "sales",
    "profit", "valuation",
    "support", "resistance",
    "breakout", "breakdown",
    "bullish", "bearish",
    "investment", "investor",
    "business", "sector",
    "good", "great", "nice",
}


HINDI_LATIN_FALLBACK = {
    "hai", "hain", "tha", "thi", "the",
    "hoga", "hogi", "honge",
    "ka", "ki", "ke",
    "ko", "se", "me", "mein",
    "par", "pe",
    "ye", "yah", "yeh",
    "woh", "vo",
    "aur", "ya",
    "toh", "to",
    "bhi", "hi",
    "nahi", "nahin",
    "mat", "abhi",
    "aaj", "kal",
    "kya", "kyu", "kyon",
    "kaise", "kab",
    "bahut", "zyada",
    "kam", "jyada",
    "achha", "acha",
    "accha", "bura",
    "lagega", "lagta", "lagti",
    "hoga", "hogi",
    "kar", "karo", "karna",
    "karta", "karte", "karti",
    "kiya", "kiye",
    "raha", "rahe", "rahi",
    "gaya", "gayi", "gaye",
    "wala", "wali", "wale",
    "mera", "meri", "mere",
    "tera", "teri", "tere",
    "apna", "apni", "apne",
    "unka", "unki", "unke",
    "iska", "iski", "iske",
    "iska", "uska", "uski",
    "upar", "neeche",
    "badhega", "badhta",
    "gir", "gira", "girna",
    "khareed", "bech",
    "sahi", "galat",
    "pakka", "shayad",
    "lag", "bhai",
    "sir", "ji",
    "milega", "mil",
    "dekh", "dekho",
    "ab", "phir",
}


# ============================================================
# LOAD LEXICONS
# ============================================================

def load_lexicon(path, fallback):
    """
    Load one-word-per-line lexicon if available.
    Otherwise use the fallback lexicon.
    """

    if not path.exists():
        return fallback

    words = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()

            if word and not word.startswith("#"):
                words.add(word)

    return words


# ============================================================
# EMOJI DETECTION
# ============================================================

def is_emoji(char):
    """
    Approximate emoji detector.

    Covers the main Unicode emoji ranges used in social text.
    """

    code = ord(char)

    return (
        0x1F300 <= code <= 0x1FAFF
        or 0x2600 <= code <= 0x27BF
        or 0x2300 <= code <= 0x23FF
    )


def contains_emoji(text):
    return any(is_emoji(char) for char in text)


# ============================================================
# SCRIPT DETECTION
# ============================================================

def get_script_flag(text):
    """
    HINGFIN:
        latin_only
        devanagari_only
        mixed_script
    """

    has_latin = bool(
        re.search(r"[A-Za-z]", text)
    )

    has_devanagari = bool(
        re.search(r"[\u0900-\u097F]", text)
    )

    if has_latin and has_devanagari:
        return "mixed_script"

    if has_devanagari:
        return "devanagari_only"

    return "latin_only"


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    """
    Tokenize while preserving punctuation and emoji.
    """

    tokens = []

    for match in TOKEN_PATTERN.finditer(text):
        token = match.group(0)

        # Break standalone emoji characters out
        if len(token) > 1:
            emoji_chars = [
                char for char in token
                if is_emoji(char)
            ]

            if emoji_chars:
                for char in token:
                    if is_emoji(char):
                        tokens.append(char)
                    else:
                        tokens.append(char)
                continue

        tokens.append(token)

    return tokens


# ============================================================
# TOKEN LANGUAGE IDENTIFICATION
# ============================================================

def classify_token(
    token,
    english_words,
    hindi_latin_words,
):
    """
    Return one of:

        EN
        HI_LATIN
        HI_DEVA
        NUM
        PUNCT
        EMOJI
        OTHER
    """

    # Emoji
    if len(token) == 1 and is_emoji(token):
        return "EMOJI"

    # Placeholder tokens
    if token.startswith("<") and token.endswith(">"):
        return "OTHER"

    # Number
    if NUMBER_PATTERN.match(token):
        return "NUM"

    # Devanagari
    if DEVANAGARI_PATTERN.match(token):
        return "HI_DEVA"

    # English / Romanized Hindi candidate
    if ENGLISH_WORD_PATTERN.match(token):

        word = token.lower()

        # Explicit Hindi lexicon takes priority
        if word in hindi_latin_words:
            return "HI_LATIN"

        if word in english_words:
            return "EN"

        # Conservative fallback:
        #
        # Unknown Latin words are not automatically treated
        # as Hindi. Finance vocabulary and English lexicon
        # should cover most English tokens.
        return "OTHER"

    # Punctuation
    if all(
        unicodedata.category(char).startswith("P")
        or unicodedata.category(char).startswith("S")
        for char in token
    ):
        return "PUNCT"

    return "OTHER"


# ============================================================
# LID FOR ONE POST
# ============================================================

def identify_language(
    text,
    english_words,
    hindi_latin_words,
):
    tokens = tokenize(text)

    tags = []

    for token in tokens:
        tag = classify_token(
            token,
            english_words,
            hindi_latin_words,
        )

        tags.append({
            "token": token,
            "label": tag,
        })

    return tags


# ============================================================
# CMI
# ============================================================

def calculate_cmi(lid_tags):
    """
    HINGFIN CMI:

    CMI = 100 * (
        1 - max(n_EN, n_HI) / N
    )

    n_HI = HI_LATIN + HI_DEVA

    NUM/PUNCT/EMOJI/OTHER are excluded.
    """

    n_en = sum(
        1
        for item in lid_tags
        if item["label"] == "EN"
    )

    n_hi = sum(
        1
        for item in lid_tags
        if item["label"] in {
            "HI_LATIN",
            "HI_DEVA",
        }
    )

    n = n_en + n_hi

    if n < 3:
        return 0.0, True, n_en, n_hi, n

    cmi = 100 * (
        1 - max(n_en, n_hi) / n
    )

    return round(cmi, 4), False, n_en, n_hi, n


# ============================================================
# CMI BUCKET
# ============================================================

def get_cmi_bucket(cmi, short_for_cmi):
    """
    HINGFIN provisional buckets:

        mono       CMI = 0
        low        0 < CMI <= 15
        medium     15 < CMI <= 35
        high       CMI > 35
    """

    if short_for_cmi:
        return "mono"

    if cmi == 0:
        return "mono"

    if cmi <= 15:
        return "low"

    if cmi <= 35:
        return "medium"

    return "high"


# ============================================================
# EMOJI POLARITY
# ============================================================

# IMPORTANT:
# The research document says this should come from the
# Emoji Sentiment Ranking (Kralj Novak et al., 2015).
#
# We do NOT invent sentiment values for every emoji here.
#
# This small seed is only a temporary implementation for
# common emojis. For the final research dataset, replace this
# with the actual Emoji Sentiment Ranking lookup table.

EMOJI_POLARITY_SEED = {
    "😀": "positive",
    "😃": "positive",
    "😄": "positive",
    "😁": "positive",
    "😂": "positive",
    "🤣": "positive",
    "😊": "positive",
    "😍": "positive",
    "🥰": "positive",
    "😘": "positive",
    "👍": "positive",
    "👏": "positive",
    "🔥": "positive",
    "🚀": "positive",
    "📈": "positive",

    "😞": "negative",
    "😔": "negative",
    "😟": "negative",
    "😢": "negative",
    "😭": "negative",
    "😡": "negative",
    "😠": "negative",
    "👎": "negative",
    "💔": "negative",
    "📉": "negative",

    "😐": "neutral",
    "😑": "neutral",
    "🤔": "neutral",
}


def get_emoji_polarity_seed(text):
    labels = []

    for char in text:
        if is_emoji(char):
            if char in EMOJI_POLARITY_SEED:
                labels.append(
                    EMOJI_POLARITY_SEED[char]
                )

    if not labels:
        return "none"

    # If both positive and negative emojis appear,
    # mark mixed rather than forcing a polarity.
    if "positive" in labels and "negative" in labels:
        return "mixed"

    if "positive" in labels:
        return "positive"

    if "negative" in labels:
        return "negative"

    return "neutral"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("HINGFIN - Step 4: Language Identification + CMI")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nLoaded {len(df):,} records"
    )

    if "text_clean" not in df.columns:
        raise ValueError(
            "Input dataset does not contain text_clean."
        )

    # --------------------------------------------------------
    # Load lexicons
    # --------------------------------------------------------

    english_words = load_lexicon(
        ENGLISH_LEXICON_FILE,
        ENGLISH_FALLBACK,
    )

    hindi_latin_words = load_lexicon(
        HINDI_LATIN_LEXICON_FILE,
        HINDI_LATIN_FALLBACK,
    )

    print(
        f"English lexicon: "
        f"{len(english_words):,} words"
    )

    print(
        f"Romanized Hindi lexicon: "
        f"{len(hindi_latin_words):,} words"
    )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    print("\nProcessing language information...")

    lid_tags_column = []
    cmi_column = []
    cmi_bucket_column = []
    short_cmi_column = []
    script_column = []
    emoji_column = []
    emoji_polarity_column = []

    total_en = 0
    total_hi_latin = 0
    total_hi_deva = 0

    for text in df["text_clean"].fillna(""):

        text = str(text)

        # Token-level LID
        lid_tags = identify_language(
            text,
            english_words,
            hindi_latin_words,
        )

        # Store compact representation
        lid_tags_column.append(
            json.dumps(
                lid_tags,
                ensure_ascii=False
            )
        )

        # CMI
        (
            cmi,
            short_for_cmi,
            n_en,
            n_hi,
            n_content,
        ) = calculate_cmi(lid_tags)

        cmi_column.append(cmi)
        short_cmi_column.append(short_for_cmi)

        # Bucket
        cmi_bucket_column.append(
            get_cmi_bucket(
                cmi,
                short_for_cmi
            )
        )

        # Script
        script_column.append(
            get_script_flag(text)
        )

        # Emoji
        has_emoji = contains_emoji(text)

        emoji_column.append(has_emoji)

        emoji_polarity_column.append(
            get_emoji_polarity_seed(text)
        )

        # Counters
        total_en += n_en

        total_hi_latin += sum(
            1
            for item in lid_tags
            if item["label"] == "HI_LATIN"
        )

        total_hi_deva += sum(
            1
            for item in lid_tags
            if item["label"] == "HI_DEVA"
        )

    # --------------------------------------------------------
    # Add Step 4 columns
    # --------------------------------------------------------

    df["lid_tags"] = lid_tags_column
    df["cmi"] = cmi_column
    df["cmi_bucket"] = cmi_bucket_column
    df["short_for_cmi"] = short_cmi_column
    df["script"] = script_column
    df["has_emoji"] = emoji_column
    df["emoji_polarity_seed"] = emoji_polarity_column

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    df.to_parquet(
        OUTPUT_PARQUET,
        index=False
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    bucket_counts = (
        df["cmi_bucket"]
        .value_counts()
        .to_dict()
    )

    script_counts = (
        df["script"]
        .value_counts()
        .to_dict()
    )

    emoji_counts = (
        df["has_emoji"]
        .value_counts()
        .to_dict()
    )

    report = {
        "pipeline": "HINGFIN Phase 1 - Step 4",
        "source": "Moneycontrol Message Board",

        "input_file": str(
            INPUT_FILE.relative_to(ROOT)
        ),

        "output_csv": str(
            OUTPUT_CSV.relative_to(ROOT)
        ),

        "output_parquet": str(
            OUTPUT_PARQUET.relative_to(ROOT)
        ),

        "records_processed": int(len(df)),

        "token_labels": [
            "EN",
            "HI_LATIN",
            "HI_DEVA",
            "NUM",
            "PUNCT",
            "EMOJI",
            "OTHER",
        ],

        "parameters": {
            "cmi_formula":
                "100 * (1 - max(n_EN, n_HI) / N)",
            "n_hi":
                "HI_LATIN + HI_DEVA",
            "content_tokens":
                "EN + HI_LATIN + HI_DEVA",
            "short_cmi_threshold": 3,
            "cmi_buckets": {
                "mono": "CMI = 0",
                "low": "0 < CMI <= 15",
                "medium": "15 < CMI <= 35",
                "high": "CMI > 35",
            },
        },

        "bucket_counts": {
            key: int(value)
            for key, value in bucket_counts.items()
        },

        "script_counts": {
            key: int(value)
            for key, value in script_counts.items()
        },

        "emoji_counts": {
            str(key): int(value)
            for key, value in emoji_counts.items()
        },

        "token_totals": {
            "EN": int(total_en),
            "HI_LATIN": int(total_hi_latin),
            "HI_DEVA": int(total_hi_deva),
        },

        "lexicons": {
            "english_file":
                str(ENGLISH_LEXICON_FILE.relative_to(ROOT)),
            "hindi_latin_file":
                str(HINDI_LATIN_LEXICON_FILE.relative_to(ROOT)),
        },

        "note":
            "CMI thresholds are provisional and must be "
            "calibrated on a 1,000-post sample before "
            "annotation, as specified by HINGFIN."
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 4 COMPLETE")
    print("=" * 70)

    print(
        f"Records processed: {len(df):,}"
    )

    print("\nCMI buckets:")

    for bucket in [
        "mono",
        "low",
        "medium",
        "high",
    ]:
        print(
            f"  {bucket:8s}: "
            f"{bucket_counts.get(bucket, 0):,}"
        )

    print("\nScript distribution:")

    for script, count in script_counts.items():
        print(
            f"  {script:18s}: {count:,}"
        )

    print("\nOutput files:")

    print(
        f"  CSV:     {OUTPUT_CSV}"
    )

    print(
        f"  Parquet: {OUTPUT_PARQUET}"
    )

    print(
        f"  Report:  {REPORT_FILE}"
    )


if __name__ == "__main__":
    main()