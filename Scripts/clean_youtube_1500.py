"""
HINGFIN - Step 3: Clean and Deduplicate YouTube Data (1500-comment collection)

Input:
    Dataset/youtube_filter_decisions_1500.csv

Outputs:
    Dataset/youtube_1500_clean_deduplicated.csv
    Dataset/youtube_1500_clean_deduplicated.parquet
    Dataset/youtube_1500_cleaning_report.json

Important:
    - Keeps only rows with decision == "retain".
    - Does not modify the original comment column.
    - Creates text_clean separately.
    - Uses the same HINGFIN cleaning and deduplication parameters
      as clean_moneycontrol.py.
    - The high-duplicate-author filter is omitted because this
      YouTube decision file does not contain author_hash.
"""

from pathlib import Path
import json
import re
import unicodedata

import pandas as pd
from datasketch import MinHash, MinHashLSH


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# Supports the usual project layout (script in scripts/, data in
# Dataset/) and also running the script from the project root.
ROOT_CANDIDATES = [SCRIPT_DIR.parent, SCRIPT_DIR]
ROOT = next(
    (
        candidate for candidate in ROOT_CANDIDATES
        if (candidate / "Dataset" / "youtube_filter_decisions_1500.csv").exists()
    ),
    SCRIPT_DIR
)

if (ROOT / "Dataset" / "youtube_filter_decisions_1500.csv").exists():
    DATA_DIR = ROOT / "Dataset"
elif (SCRIPT_DIR / "youtube_filter_decisions_1500.csv").exists():
    DATA_DIR = SCRIPT_DIR
else:
    DATA_DIR = ROOT / "Dataset"

INPUT_FILE = DATA_DIR / "youtube_filter_decisions_1500.csv"
OUTPUT_CSV = DATA_DIR / "youtube_1500_clean_deduplicated.csv"
OUTPUT_PARQUET = DATA_DIR / "youtube_1500_clean_deduplicated.parquet"
REPORT_FILE = DATA_DIR / "youtube_1500_cleaning_report.json"


# ============================================================
# HINGFIN PARAMETERS (same as Moneycontrol)
# ============================================================

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 600

SHINGLE_SIZE = 5
JACCARD_THRESHOLD = 0.85
NUM_PERM = 128


# ============================================================
# REGEX PATTERNS
# ============================================================

URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+",
    flags=re.IGNORECASE
)

USER_PATTERN = re.compile(
    r"(?<!\w)(?:@[A-Za-z0-9_]+|u/[A-Za-z0-9_-]+)"
)

CASHTAG_PATTERN = re.compile(
    r"\$([A-Za-z][A-Za-z0-9._-]*)"
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
)

AADHAAR_PATTERN = re.compile(
    r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"
)

PROMO_PATTERNS = [
    r"\bjoin\s+my\s+channel\b",
    r"\btelegram\s+link\b",
    r"\bdm\s+for\s+tips\b",
    r"\bcalls\s+deta\s+hu\b",
]

PROMO_REGEX = re.compile(
    "|".join(PROMO_PATTERNS),
    flags=re.IGNORECASE
)

ALL_CAPS_PATTERN = re.compile(
    r"\b[A-Z0-9][A-Z0-9\s!?.,:/()$%&+\-]{30,}\b"
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """Create text_clean without modifying the original comment."""

    if pd.isna(text):
        return ""

    text = str(text)
    text = unicodedata.normalize("NFC", text)

    # Replace personally identifying information.
    text = EMAIL_PATTERN.sub("<EMAIL>", text)
    text = PHONE_PATTERN.sub("<PHONE>", text)
    text = AADHAAR_PATTERN.sub("<ID>", text)

    # Replace URLs and user mentions.
    text = URL_PATTERN.sub("<URL>", text)
    text = USER_PATTERN.sub("<USER>", text)

    # Normalize cashtags to uppercase.
    def normalize_cashtag(match):
        return "$" + match.group(1).upper()

    text = CASHTAG_PATTERN.sub(normalize_cashtag, text)

    # Remove zero-width characters while preserving Devanagari text.
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# SPAM / PROMO FILTER
# ============================================================

def is_obvious_promo(text):
    """Apply the same conservative promotional filter as Moneycontrol."""

    if not text:
        return False

    if PROMO_REGEX.search(text):
        return True

    if "<PHONE>" in text:
        return True

    if ALL_CAPS_PATTERN.search(text):
        return True

    return False


# ============================================================
# 5-GRAM SHINGLES
# ============================================================

def get_shingles(text, k=SHINGLE_SIZE):
    """Return character-level k-shingles."""

    if len(text) < k:
        return {text}

    return {
        text[i:i + k]
        for i in range(len(text) - k + 1)
    }


# ============================================================
# MINHASH
# ============================================================

def create_minhash(text):
    """Create a MinHash signature from character 5-grams."""

    minhash = MinHash(num_perm=NUM_PERM)

    for shingle in get_shingles(text):
        minhash.update(shingle.encode("utf-8"))

    return minhash


# ============================================================
# NEAR-DUPLICATE REMOVAL
# ============================================================

def remove_near_duplicates(df):
    """
    Remove near duplicates using MinHash LSH.
    Keep the first encountered comment; missing published_at values retain input order.
    """

    if df.empty:
        return df, 0

    df = df.sort_values(
        by="_published_sort",
        ascending=True,
        kind="stable",
        na_position="last"
    ).copy()

    lsh = MinHashLSH(
        threshold=JACCARD_THRESHOLD,
        num_perm=NUM_PERM
    )

    keep_indices = []
    removed_count = 0

    for idx, row in df.iterrows():
        text = row["text_clean"]

        if not text:
            continue

        minhash = create_minhash(text)
        matches = lsh.query(minhash)

        if matches:
            removed_count += 1
            continue

        lsh.insert(f"youtube_{idx}", minhash)
        keep_indices.append(idx)

    cleaned = df.loc[keep_indices].copy()

    return cleaned, removed_count


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("HINGFIN - YouTube Step 3: Clean and Deduplicate (1500-comment collection)")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}\n\n"
            "Place youtube_filter_decisions_1500.csv in the Dataset folder "
            "or in the same folder as this script."
        )

    df = pd.read_csv(INPUT_FILE)
    initial_count = len(df)

    print(f"\nLoaded: {initial_count:,} records")
    print(f"Input:  {INPUT_FILE}")

    required_columns = [
        "video_id",
        "comment",
        "published_at",
        "like_count",
        "decision",
        "matched_symbols",
        "matched_aliases",
        "reason",
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Preserve the original comment column.
    original_comments = df["comment"].copy()

    # --------------------------------------------------------
    # Keep only comments already approved by the decision stage
    # --------------------------------------------------------

    print("\n[1/7] Keeping only decision == 'retain'...")

    decision_values = df["decision"].astype(str).str.strip().str.lower()
    rejected_by_decision = int((decision_values != "retain").sum())
    df = df[decision_values == "retain"].copy()

    print(
        f"      Kept {len(df):,} retained comments; "
        f"excluded {rejected_by_decision:,} review/reject/other records"
    )

    # --------------------------------------------------------
    # Create text_clean
    # --------------------------------------------------------

    print("[2/7] Creating text_clean...")

    df["text_clean"] = df["comment"].apply(clean_text)

    # Verify the original comment text has not been modified.
    if not df["comment"].equals(original_comments.loc[df.index]):
        raise RuntimeError(
            "ERROR: Original comment column was modified. Pipeline stopped."
        )

    # Parse publication timestamps for chronological sorting.
    df["_published_sort"] = pd.to_datetime(
        df["published_at"],
        errors="coerce",
        utc=True
    )

    # --------------------------------------------------------
    # Length filter
    # --------------------------------------------------------

    print("[3/7] Applying length filter...")

    length_mask = df["text_clean"].str.len().between(
        MIN_TEXT_LENGTH,
        MAX_TEXT_LENGTH
    )

    length_removed = int((~length_mask).sum())
    df = df[length_mask].copy()

    print(
        f"      Removed {length_removed:,} records "
        f"outside 10-600 characters"
    )

    # --------------------------------------------------------
    # Promotional / spam filter
    # --------------------------------------------------------

    print("[4/7] Applying conservative promo/spam filter...")

    promo_mask = df["text_clean"].apply(is_obvious_promo)
    promo_removed = int(promo_mask.sum())
    df = df[~promo_mask].copy()

    print(f"      Removed {promo_removed:,} promotional/spam records")

    # --------------------------------------------------------
    # Author duplicate-rate filter
    # --------------------------------------------------------

    print("[5/7] Author duplicate-rate filter...")

    # Not applied: this YouTube CSV has no author_hash/author identifier.
    author_removed = 0
    print("      Skipped: author_hash is not available in this input file.")

    # --------------------------------------------------------
    # Exact deduplication
    # --------------------------------------------------------

    print("[6/7] Exact and near-duplicate deduplication...")

    df = df.sort_values(
        by="_published_sort",
        ascending=True,
        kind="stable",
        na_position="last"
    )

    exact_duplicates = int(
        df.duplicated(subset=["text_clean"], keep="first").sum()
    )

    df = df.drop_duplicates(
        subset=["text_clean"],
        keep="first"
    ).copy()

    print(f"      Removed {exact_duplicates:,} exact duplicates")
    print(f"      Shingle size: {SHINGLE_SIZE}")
    print(f"      Jaccard threshold: {JACCARD_THRESHOLD}")

    df, near_duplicates = remove_near_duplicates(df)

    print(f"      Removed {near_duplicates:,} near duplicates")

    # --------------------------------------------------------
    # Final sorting and save
    # --------------------------------------------------------

    df = df.sort_values(
        by="_published_sort",
        ascending=True,
        kind="stable",
        na_position="last"
    )

    # Internal sorting helper is not needed in the output.
    df = df.drop(columns=["_published_sort"]).reset_index(drop=True)

    print("[7/7] Saving outputs...")

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
    # Cleaning report
    # --------------------------------------------------------

    final_count = len(df)

    report = {
        "pipeline": "HINGFIN Phase 1 - Step 3",
        "source": "YouTube comments",
        "input_file": str(INPUT_FILE),
        "output_csv": str(OUTPUT_CSV),
        "output_parquet": str(OUTPUT_PARQUET),
        "input_records": int(initial_count),
        "removed_by_decision_filter": int(rejected_by_decision),
        "retained_for_cleaning": int(initial_count - rejected_by_decision),
        "removed_length_filter": int(length_removed),
        "removed_promo_spam": int(promo_removed),
        "removed_high_duplicate_authors": int(author_removed),
        "author_filter_applied": False,
        "author_filter_reason": "author_hash is not present in the input CSV",
        "removed_exact_duplicates": int(exact_duplicates),
        "removed_near_duplicates": int(near_duplicates),
        "final_records": int(final_count),
        "parameters": {
            "min_text_length": MIN_TEXT_LENGTH,
            "max_text_length": MAX_TEXT_LENGTH,
            "shingle_size": SHINGLE_SIZE,
            "jaccard_threshold": JACCARD_THRESHOLD,
            "minhash_num_perm": NUM_PERM,
        },
        "text_columns": {
            "raw": "comment",
            "clean": "text_clean"
        },
        "raw_text_preserved": True,
        "keep_policy": "first encountered; published_at is missing for records in this input"
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("YOUTUBE STEP 3 COMPLETE")
    print("=" * 70)

    print(f"Input records:             {initial_count:,}")
    print(f"Excluded by decision:      {rejected_by_decision:,}")
    print(f"Length removed:            {length_removed:,}")
    print(f"Promo/spam removed:        {promo_removed:,}")
    print(f"Author-filter removed:     {author_removed:,} (skipped)")
    print(f"Exact duplicates:          {exact_duplicates:,}")
    print(f"Near duplicates:           {near_duplicates:,}")
    print("-" * 70)
    print(f"Final records:             {final_count:,}")

    print("\nFiles created:")
    print(f"  CSV:     {OUTPUT_CSV}")
    print(f"  Parquet: {OUTPUT_PARQUET}")
    print(f"  Report:  {REPORT_FILE}")

    print("\nOriginal YouTube decision CSV was NOT modified.")


if __name__ == "__main__":
    main()
