import pandas as pd
import re

INPUT_FILE = "nifty100_constituents.tsv"
OUTPUT_FILE = "ticker_dictionary_candidates.tsv"

df = pd.read_csv(INPUT_FILE, sep="\t")

rows = []

# ---------------------------------------------------
# Generate aliases for each company
# ---------------------------------------------------

for _, row in df.iterrows():

    ticker = row["symbol"]
    company = row["company_name"]

    # 1. Official/legal name
    rows.append([
        ticker,
        company,
        "legal",
        False
    ])

    # 2. Ticker
    rows.append([
        ticker,
        ticker,
        "short",
        False
    ])

    # 3. Cashtag
    rows.append([
        ticker,
        f"${ticker}",
        "cashtag",
        False
    ])

    # 4. Hashtag
    rows.append([
        ticker,
        f"#{ticker}",
        "hashtag",
        False
    ])

    # ------------------------------------------------
    # 5. Remove common legal suffixes
    # ------------------------------------------------

    short_name = re.sub(
        r"\b(Limited|Ltd\.?|Private Limited|Pvt\. Ltd\.?)\b",
        "",
        company,
        flags=re.IGNORECASE
    ).strip()

    short_name = re.sub(r"\s+", " ", short_name)

    if short_name and short_name.lower() != company.lower():

        rows.append([
            ticker,
            short_name,
            "short",
            False
        ])

# ---------------------------------------------------
# Create dataframe
# ---------------------------------------------------

result = pd.DataFrame(
    rows,
    columns=[
        "symbol",
        "surface_form",
        "surface_form_type",
        "is_ambiguous"
    ]
)

# Remove duplicate rows
result = result.drop_duplicates()

# Save
result.to_csv(
    OUTPUT_FILE,
    sep="\t",
    index=False
)

print("Done!")
print(f"Companies: {df['symbol'].nunique()}")
print(f"Dictionary rows: {len(result)}")
print(f"Saved to: {OUTPUT_FILE}")