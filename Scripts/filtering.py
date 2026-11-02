
from pathlib import Path
import pandas as pd
import re

# =====================================================
# 1. FILE PATHS
# =====================================================

# Project structure:
# HINGFIN-Phase1/
#   Dataset/
#       youtube_comments.csv
#       ticker_dictionary.tsv
#   StockMarket/
#       Scripts/
#           filtering.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IGNORED_DIRS = {".venv", "venv", ".git", "__pycache__"}


def find_project_file(filename):
    """Find a file inside the project, including nested folders."""

    preferred = PROJECT_ROOT / "Dataset" / filename

    if preferred.is_file():
        return preferred

    matches = [
        path
        for path in PROJECT_ROOT.rglob(filename)
        if path.is_file()
        and not any(part in IGNORED_DIRS for part in path.parts)
    ]

    if not matches:
        raise FileNotFoundError(
            f"\nCannot find file: {filename}\n"
            f"Project searched: {PROJECT_ROOT}\n"
            "Place the file inside the project and try again."
        )

    if len(matches) > 1:
        print(f"\nMultiple copies of {filename} found:")
        for path in matches:
            print(f"  {path}")
        print(f"Using: {matches[0]}")

    return matches[0]


COMMENTS_FILE = find_project_file("youtube_comments.csv")
DICTIONARY_FILE = find_project_file("ticker_dictionary.tsv")

# Save outputs beside the comments input file.
OUTPUT_DIR = COMMENTS_FILE.parent

FILTERED_FILE = OUTPUT_DIR / "filtered_youtube_comments.csv"
DECISIONS_FILE = OUTPUT_DIR / "youtube_filter_decisions.csv"


# =====================================================
# 2. LOAD DATA
# =====================================================

print("Project root:", PROJECT_ROOT)
print("Comments file:", COMMENTS_FILE)
print("Dictionary file:", DICTIONARY_FILE)

comments_df = pd.read_csv(
    COMMENTS_FILE,
    dtype=str
).fillna("")

ticker_df = pd.read_csv(
    DICTIONARY_FILE,
    sep="\t",
    dtype=str
).fillna("")

required_columns = {
    "symbol",
    "surface_form",
    "surface_form_type",
    "is_ambiguous"
}

missing = required_columns - set(ticker_df.columns)

if missing:
    raise ValueError(
        f"Ticker dictionary is missing columns: {missing}"
    )

if "comment" not in comments_df.columns:
    raise ValueError(
        "Comments CSV must contain a 'comment' column."
    )


# =====================================================
# 3. TEXT NORMALIZATION AND MATCHING
# =====================================================

def normalize(text):
    text = str(text).lower()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_pattern(phrase):
    phrase = normalize(phrase)
    escaped = re.escape(phrase)
    escaped = escaped.replace(r"\ ", r"\s+")

    return re.compile(
        r"(?<!\w)" + escaped + r"(?!\w)",
        re.IGNORECASE
    )


# =====================================================
# 4. BUILD COMPANY ALIAS DICTIONARY
# =====================================================

company_aliases = {}

for _, row in ticker_df.iterrows():
    symbol = row["symbol"].strip().upper()
    alias = row["surface_form"].strip()
    alias_type = row["surface_form_type"].strip().lower()

    if not symbol or not alias:
        continue

    company_aliases.setdefault(symbol, [])

    company_aliases[symbol].append({
        "alias": alias,
        "type": alias_type,
        "ambiguous": (
            row["is_ambiguous"].strip().lower() == "true"
        )
    })


compiled_aliases = {}

for symbol, aliases in company_aliases.items():
    compiled_aliases[symbol] = []

    for item in aliases:
        compiled_aliases[symbol].append({
            **item,
            "pattern": make_pattern(item["alias"])
        })


# =====================================================
# 5. FINANCIAL VOCABULARY
# =====================================================

financial_terms = [
    "share", "shares", "stock", "stocks",
    "share price", "stock price", "share market",
    "stock market", "nse", "bse",
    "buy", "buying", "sell", "selling",
    "hold", "holding", "accumulate",
    "invest", "investment", "investing",
    "target", "price target", "cmp",
    "entry", "exit", "stop loss", "stoploss",
    "support", "resistance", "breakout",
    "bullish", "bearish", "multibagger",
    "upper circuit", "lower circuit",
    "profit", "loss", "returns", "return",
    "valuation", "fundamental", "technical",
    "quarterly results", "quarter results",
    "earnings", "revenue", "dividend",
    "ipo", "intraday", "swing trade",
    "long term", "short term", "portfolio",
    "pe ratio", "p/e", "market cap",
    "share price target", "price action",
    "trading", "trader", "investor",
    "market price", "results", "resistance level",
    "support level", "average price", "averaging",
    "delivery", "futures", "options"
]


# =====================================================
# 6. ENGLISH + HINGLISH OPINION PATTERNS
# =====================================================

opinion_patterns = [
    # English
    r"\bwill go up\b",
    r"\bwill go down\b",
    r"\bgoing up\b",
    r"\bgoing down\b",
    r"\bgoes up\b",
    r"\bgoes down\b",
    r"\bshould i buy\b",
    r"\bshould i sell\b",
    r"\bworth buying\b",
    r"\bgood time to buy\b",
    r"\btime to buy\b",
    r"\bnext target\b",
    r"\bprice will rise\b",
    r"\bprice will fall\b",

    # Hinglish: price movement
    r"\bupar jayega\b",
    r"\bupar jaayega\b",
    r"\bupar jayegi\b",
    r"\bupar jaayegi\b",
    r"\bupar ja raha hai\b",
    r"\bupar jaa raha hai\b",
    r"\bneeche jayega\b",
    r"\bneeche jaayega\b",
    r"\bneeche jayegi\b",
    r"\bneeche jaayegi\b",
    r"\bneeche ja raha hai\b",
    r"\bneeche jaa raha hai\b",
    r"\bbahut upar\b",
    r"\bbahut neeche\b",
    r"\bkal upar\b",
    r"\bkal neeche\b",
    r"\bbadhega\b",
    r"\bbadhegi\b",
    r"\bgirega\b",
    r"\bgiregi\b",
    r"\bteji aayegi\b",
    r"\bmandi aayegi\b",
    r"\baage badhega\b",
    r"\bprice badhega\b",
    r"\bprice girega\b",
    r"\bkitna badhega\b",
    r"\bkitna girega\b",

    # Hinglish: buying, selling and holding
    r"\blena chahiye\b",
    r"\bkharidna chahiye\b",
    r"\bbechna chahiye\b",
    r"\bsell karna chahiye\b",
    r"\bhold karna chahiye\b",
    r"\bbuy karu\b",
    r"\bsell karu\b",
    r"\bhold karu\b",
    r"\bhold karna\b",
    r"\bentry le\b",
    r"\babhi lena\b",
    r"\babhi kharidna\b",
    r"\babhi bechna\b",
    r"\ble sakte hain\b",
    r"\ble sakte hai\b",
    r"\bkharid sakte hain\b",
    r"\bkharid sakte hai\b",
    r"\btarget kya\b",
    r"\bkitna target\b"
]

financial_patterns = [
    make_pattern(term) for term in financial_terms
]

opinion_regexes = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in opinion_patterns
]


def has_financial_context(text):
    return any(
        pattern.search(text)
        for pattern in financial_patterns
    )


def has_stock_opinion(text):
    return any(
        pattern.search(text)
        for pattern in opinion_regexes
    )


# =====================================================
# 7. COMPANY MATCHING
# =====================================================

def find_companies(text):
    text_normalized = normalize(text)

    financial_context = has_financial_context(text_normalized)
    stock_opinion = has_stock_opinion(text_normalized)
    has_context = financial_context or stock_opinion

    matches = []

    for symbol, aliases in compiled_aliases.items():
        matched_aliases = []
        ambiguous_match = False

        for item in aliases:
            alias = item["alias"]

            if not item["pattern"].search(text_normalized):
                continue

            # Short ticker symbols can match ordinary words.
            # Require financial context for these matches.
            if (
                len(symbol) <= 3
                and alias.upper() == symbol
                and not has_context
            ):
                continue

            matched_aliases.append(alias)

            if item["ambiguous"]:
                ambiguous_match = True

        # Explicit $SYMBOL and #SYMBOL references
        for prefix in ("$", "#"):
            explicit_pattern = re.compile(
                re.escape(prefix)
                + re.escape(symbol)
                + r"(?!\w)",
                re.IGNORECASE
            )

            if explicit_pattern.search(text_normalized):
                matched_aliases.append(prefix + symbol)

        matched_aliases = list(dict.fromkeys(matched_aliases))

        if matched_aliases:
            matches.append({
                "symbol": symbol,
                "aliases": matched_aliases,
                "ambiguous": ambiguous_match
            })

    return matches


# =====================================================
# 8. CLASSIFY EACH COMMENT
# =====================================================

def classify_comment(comment):
    text = normalize(comment)

    if not text:
        return {
            "decision": "reject",
            "matched_symbols": "",
            "matched_aliases": "",
            "reason": "Empty comment"
        }

    companies = find_companies(text)

    if not companies:
        return {
            "decision": "reject",
            "matched_symbols": "",
            "matched_aliases": "",
            "reason": "No company alias matched"
        }

    financial_context = has_financial_context(text)
    stock_opinion = has_stock_opinion(text)
    has_context = financial_context or stock_opinion

    symbols = [
        company["symbol"] for company in companies
    ]

    aliases = list(dict.fromkeys(
        f'{company["symbol"]}:{alias}'
        for company in companies
        for alias in company["aliases"]
    ))

    # Retain only if a company is identified and
    # financial context or a stock opinion is detected.
    if has_context:
        if financial_context and stock_opinion:
            reason = (
                "Company mention + financial and opinion context"
            )
        elif financial_context:
            reason = "Company mention + financial context"
        else:
            reason = "Company mention + stock opinion phrase"

        decision = "retain"

    else:
        decision = "review"
        reason = "Company mention without clear stock context"

    return {
        "decision": decision,
        "matched_symbols": ";".join(symbols),
        "matched_aliases": ";".join(aliases),
        "reason": reason
    }


# =====================================================
# 9. PROCESS ALL COMMENTS
# =====================================================

results = comments_df["comment"].apply(classify_comment)

decisions_df = pd.DataFrame(results.tolist())

output_df = pd.concat(
    [
        comments_df.reset_index(drop=True),
        decisions_df.reset_index(drop=True)
    ],
    axis=1
)

filtered_df = output_df[
    output_df["decision"] == "retain"
].copy()

# Save retained comments separately.
filtered_df.to_csv(
    FILTERED_FILE,
    index=False,
    encoding="utf-8-sig"
)

# Save all decisions for auditing and manual review.
output_df.to_csv(
    DECISIONS_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =====================================================
# 10. SUMMARY
# =====================================================

print("\n========== HINGFIN FILTER SUMMARY ==========")

print("Total comments:", len(output_df))
print("Retained:", (output_df["decision"] == "retain").sum())
print("Needs review:", (output_df["decision"] == "review").sum())
print("Rejected:", (output_df["decision"] == "reject").sum())

print("\nRetained comments by ticker:")

if not filtered_df.empty:
    print(
        filtered_df["matched_symbols"]
        .str.split(";")
        .explode()
        .value_counts()
    )
else:
    print("No comments retained.")

print("\nSaved files:")
print(FILTERED_FILE)
print(DECISIONS_FILE)

print("\nFirst 10 retained comments:")

if not filtered_df.empty:
    print(
        filtered_df[
            [
                "comment",
                "matched_symbols",
                "matched_aliases",
                "reason"
            ]
        ].head(10).to_string(index=False)
    )

print("\n============================================")
