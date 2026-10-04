"""
HINGFIN - Step 3: Clean and Deduplicate Moneycontrol Data

Input:
    Dataset/moneycontrol_all_raw.csv

Outputs:
    Dataset/moneycontrol_clean_deduplicated.csv
    Dataset/moneycontrol_clean_deduplicated.parquet
    Dataset/moneycontrol_cleaning_report.json

Important:
    - NEVER modifies text_raw
    - Creates text_clean separately
    - Follows HINGFIN Phase 1 Step 3 specification
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

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "Dataset" / "moneycontrol_all_raw.csv"

OUTPUT_CSV = ROOT / "Dataset" / "moneycontrol_clean_deduplicated.csv"
OUTPUT_PARQUET = ROOT / "Dataset" / "moneycontrol_clean_deduplicated.parquet"
REPORT_FILE = ROOT / "Dataset" / "moneycontrol_cleaning_report.json"


# ============================================================
# HINGFIN PARAMETERS
# ============================================================

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 600

# HINGFIN specification:
# 5-character shingles
# Jaccard threshold = 0.85
SHINGLE_SIZE = 5
JACCARD_THRESHOLD = 0.85

# Number of MinHash permutations.
# 128 gives a reasonable approximation for this dataset size.
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

# Cashtag:
# $reliance -> $RELIANCE
CASHTAG_PATTERN = re.compile(
    r"\$([A-Za-z][A-Za-z0-9._-]*)"
)

# Email
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Indian phone numbers / common phone formats
PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+91[\s-]?)?"
    r"[6-9]\d{9}"
    r"(?!\d)"
)

# Aadhaar-shaped 12 digit number
AADHAAR_PATTERN = re.compile(
    r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"
)

# Obvious promotional phrases from the HINGFIN specification
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

# Uninterrupted ALL-CAPS stretches > 30 characters
ALL_CAPS_PATTERN = re.compile(
    r"\b[A-Z0-9][A-Z0-9\s!?.,:/()$%&+\-]{30,}\b"
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Create text_clean without modifying text_raw.

    HINGFIN requirements:
        - URLs -> <URL>
        - user mentions -> <USER>
        - cashtags normalized to uppercase
        - whitespace normalized
        - Unicode NFC normalization
        - emojis preserved
        - zero-width characters removed where safe
    """

    if pd.isna(text):
        return ""

    text = str(text)

    # Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Replace PII
    text = EMAIL_PATTERN.sub("<EMAIL>", text)
    text = PHONE_PATTERN.sub("<PHONE>", text)
    text = AADHAAR_PATTERN.sub("<ID>", text)

    # URLs
    text = URL_PATTERN.sub("<URL>", text)

    # User mentions
    text = USER_PATTERN.sub("<USER>", text)

    # Normalize cashtags
    def normalize_cashtag(match):
        return "$" + match.group(1).upper()

    text = CASHTAG_PATTERN.sub(normalize_cashtag, text)

    # Remove zero-width characters.
    # Keep Devanagari ligature behavior intact.
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")

    # Normalize all whitespace to single spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# SPAM / PROMO FILTER
# ============================================================

def is_obvious_promo(text):
    """
    Conservative promotional filter.

    Important:
    BUY / SELL / TARGET / CALL etc. are NOT treated as spam
    because financial advice-only posts are retained for later
    annotation.
    """

    if not text:
        return False

    if PROMO_REGEX.search(text):
        return True

    # Remaining phone placeholder is a strong promo signal
    if "<PHONE>" in text:
        return True

    # Very long uninterrupted ALL-CAPS stretch
    if ALL_CAPS_PATTERN.search(text):
        return True

    return False


# ============================================================
# 5-GRAM SHINGLES
# ============================================================

def get_shingles(text, k=SHINGLE_SIZE):
    """
    Return character-level k-shingles.
    """

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
    """
    Create a MinHash signature from character 5-grams.
    """

    minhash = MinHash(num_perm=NUM_PERM)

    shingles = get_shingles(text)

    for shingle in shingles:
        minhash.update(shingle.encode("utf-8"))

    return minhash


# ============================================================
# NEAR-DUPLICATE REMOVAL
# ============================================================

def remove_near_duplicates(df):
    """
    Remove near duplicates using MinHash LSH.

    HINGFIN:
        - 5-character shingles
        - Jaccard threshold = 0.85
        - keep earliest record by created_utc
    """

    if df.empty:
        return df, 0

    # Sort so that the earliest record is encountered first.
    df = df.sort_values(
        by="created_utc",
        ascending=True,
        kind="stable"
    ).copy()

    lsh = MinHashLSH(
        threshold=JACCARD_THRESHOLD,
        num_perm=NUM_PERM
    )

    keep_indices = []
    removed_count = 0

    for idx, row in df.iterrows():

        text = row["text_clean"]

        # Skip empty text
        if not text:
            continue

        minhash = create_minhash(text)

        # Query existing records for near duplicates
        matches = lsh.query(minhash)

        if matches:
            # A near duplicate already exists.
            # Since records are processed chronologically,
            # the existing record is earlier.
            removed_count += 1
            continue

        # Keep this record
        key = f"post_{idx}"
        lsh.insert(key, minhash)

        keep_indices.append(idx)

    cleaned = df.loc[keep_indices].copy()

    return cleaned, removed_count


# ============================================================
# AUTHOR DUPLICATE-RATE FILTER
# ============================================================

def find_high_duplicate_authors(df):
    """
    HINGFIN specifies:

    If one author contributes >200 posts and >80% are
    near-duplicates, drop all posts from that author.

    We calculate this conservatively using MinHash
    against the author's own posts.
    """

    bad_authors = set()

    if df.empty:
        return bad_authors

    author_counts = df["author_hash"].value_counts()

    candidates = author_counts[author_counts > 200].index

    for author in candidates:

        author_df = df[df["author_hash"] == author].copy()

        if len(author_df) <= 200:
            continue

        # Sort chronologically
        author_df = author_df.sort_values(
            "created_utc",
            ascending=True,
            kind="stable"
        )

        lsh = MinHashLSH(
            threshold=JACCARD_THRESHOLD,
            num_perm=NUM_PERM
        )

        duplicate_count = 0
        total_count = 0

        for idx, row in author_df.iterrows():

            text = row["text_clean"]

            if not text:
                continue

            total_count += 1

            mh = create_minhash(text)

            if lsh.query(mh):
                duplicate_count += 1
            else:
                lsh.insert(f"author_{author}_{idx}", mh)

        if total_count > 0:
            duplicate_rate = duplicate_count / total_count

            if duplicate_rate > 0.80:
                bad_authors.add(author)

    return bad_authors


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("HINGFIN - Moneycontrol Step 3: Clean and Deduplicate")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    initial_count = len(df)

    print(f"\nLoaded: {initial_count:,} records")
    print(f"Input:  {INPUT_FILE}")

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required_columns = [
        "post_id",
        "source",
        "platform_id",
        "text_raw",
        "created_utc",
        "created_ist",
        "author_hash",
        "parent_id",
        "url",
        "symbol",
        "collection_date",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Preserve original text
    # --------------------------------------------------------

    original_raw = df["text_raw"].copy()

    # --------------------------------------------------------
    # Create text_clean
    # --------------------------------------------------------

    print("\n[1/7] Creating text_clean...")

    df["text_clean"] = df["text_raw"].apply(clean_text)

    # Verify text_raw was not modified
    if not df["text_raw"].equals(original_raw):
        raise RuntimeError(
            "ERROR: text_raw was modified. "
            "Pipeline stopped."
        )

    # --------------------------------------------------------
    # Length filter
    # --------------------------------------------------------

    print("[2/7] Applying length filter...")

    before = len(df)

    length_mask = (
        df["text_clean"].str.len().between(
            MIN_TEXT_LENGTH,
            MAX_TEXT_LENGTH
        )
    )

    length_removed = (~length_mask).sum()

    df = df[length_mask].copy()

    print(
        f"      Removed {length_removed:,} "
        f"records outside 10-600 characters"
    )

    # --------------------------------------------------------
    # Promotional / spam filter
    # --------------------------------------------------------

    print("[3/7] Applying conservative promo/spam filter...")

    before = len(df)

    promo_mask = df["text_clean"].apply(is_obvious_promo)

    promo_removed = promo_mask.sum()

    df = df[~promo_mask].copy()

    print(
        f"      Removed {promo_removed:,} "
        f"obvious promotional/spam records"
    )

    # --------------------------------------------------------
    # Author duplicate-rate filter
    # --------------------------------------------------------

    print("[4/7] Checking high-volume duplicate authors...")

    bad_authors = find_high_duplicate_authors(df)

    author_removed = 0

    if bad_authors:
        author_mask = df["author_hash"].isin(bad_authors)
        author_removed = author_mask.sum()

        df = df[~author_mask].copy()

        print(
            f"      Removed {author_removed:,} records "
            f"from {len(bad_authors)} high-duplicate authors"
        )
    else:
        print("      No high-duplicate authors detected.")

    # --------------------------------------------------------
    # Exact deduplication
    # --------------------------------------------------------

    print("[5/7] Exact deduplication...")

    # Ensure chronological order first.
    df = df.sort_values(
        by="created_utc",
        ascending=True,
        kind="stable"
    )

    exact_duplicates = df.duplicated(
        subset=["text_clean"],
        keep="first"
    ).sum()

    df = df.drop_duplicates(
        subset=["text_clean"],
        keep="first"
    ).copy()

    print(
        f"      Removed {exact_duplicates:,} "
        f"exact duplicates"
    )

    # --------------------------------------------------------
    # Near deduplication
    # --------------------------------------------------------

    print("[6/7] Near-duplicate deduplication...")
    print(
        f"      Shingle size: {SHINGLE_SIZE}"
    )
    print(
        f"      Jaccard threshold: {JACCARD_THRESHOLD}"
    )

    df, near_duplicates = remove_near_duplicates(df)

    print(
        f"      Removed {near_duplicates:,} "
        f"near duplicates"
    )

    # --------------------------------------------------------
    # Final sorting
    # --------------------------------------------------------

    df = df.sort_values(
        by="created_utc",
        ascending=True,
        kind="stable"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print("[7/7] Saving outputs...")

    # IMPORTANT:
    # These are NEW files. The original raw CSV is untouched.

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
        "source": "Moneycontrol Message Board",
        "input_file": str(INPUT_FILE.relative_to(ROOT)),
        "output_csv": str(OUTPUT_CSV.relative_to(ROOT)),
        "output_parquet": str(OUTPUT_PARQUET.relative_to(ROOT)),

        "input_records": int(initial_count),

        "removed_length_filter": int(length_removed),
        "removed_promo_spam": int(promo_removed),
        "removed_high_duplicate_authors": int(author_removed),
        "high_duplicate_author_count": int(len(bad_authors)),
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
            "raw": "text_raw",
            "clean": "text_clean"
        },

        "raw_text_preserved": True
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
    print("STEP 3 COMPLETE")
    print("=" * 70)

    print(f"Input records:          {initial_count:,}")
    print(f"Length removed:         {length_removed:,}")
    print(f"Promo/spam removed:     {promo_removed:,}")
    print(f"Author-filter removed:  {author_removed:,}")
    print(f"Exact duplicates:       {exact_duplicates:,}")
    print(f"Near duplicates:        {near_duplicates:,}")
    print("-" * 70)
    print(f"Final records:          {final_count:,}")

    print("\nFiles created:")
    print(f"  CSV:     {OUTPUT_CSV}")
    print(f"  Parquet: {OUTPUT_PARQUET}")
    print(f"  Report:  {REPORT_FILE}")

    print("\nOriginal raw file was NOT modified.")


if __name__ == "__main__":
    main()