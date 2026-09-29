import json
import time
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "Dataset" / "NIFTY50.csv"
OUTPUT_FILE = BASE_DIR / "Dataset" / "board_url_lookup.json"


SEARCH_URL = (
    "https://www.moneycontrol.com/"
    "mccode/common/autosuggestion_solr.php"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DELAY_SECONDS = 2



def search_moneycontrol(symbol):
    """
    Search Moneycontrol using the NSE symbol.

    Returns the JSON results from Moneycontrol.
    """

    params = {
        "classic": "true",
        "query": symbol,
        "type": "1",
        "format": "json"
    }

    try:

        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        print(f"  ERROR: Request failed: {e}")
        return []

    except ValueError:

        print("  ERROR: Moneycontrol returned invalid JSON.")
        return []


# ============================================================
# FIND CORRECT RESULT
# ============================================================

def find_matching_stock(results, company_name, symbol, isin):
    """
    Find the Moneycontrol result matching the company from
    NIFTY50.csv.

    We primarily match using:
        1. NSE symbol
        2. ISIN
        3. Company name
    """

    company_name_clean = (
        company_name
        .lower()
        .replace(" ltd.", "")
        .replace(" ltd", "")
        .replace(" limited", "")
        .strip()
    )

    symbol = symbol.upper()
    isin = isin.upper()

    # --------------------------------------------------------
    # First: try exact symbol + ISIN match
    # --------------------------------------------------------

    for result in results:

        description = result.get("pdt_dis_nm", "").upper()

        if symbol in description and isin in description:
            return result

    # --------------------------------------------------------
    # Second: symbol match
    # --------------------------------------------------------

    for result in results:

        description = result.get("pdt_dis_nm", "").upper()

        if symbol in description:
            return result

    # --------------------------------------------------------
    # Third: company name match
    # --------------------------------------------------------

    for result in results:

        stock_name = result.get(
            "stock_name",
            ""
        ).lower().strip()

        if (
            stock_name == company_name_clean
            or company_name_clean in stock_name
            or stock_name in company_name_clean
        ):
            return result

    return None


# ============================================================
# PROCESS ONE COMPANY
# ============================================================

def process_company(company_name, symbol, isin):

    print()
    print("-" * 60)
    print(f"Company : {company_name}")
    print(f"Symbol  : {symbol}")
    print(f"ISIN    : {isin}")

    results = search_moneycontrol(symbol)

    if not results:

        print("  ✗ No Moneycontrol result found.")

        return {
            "company_name": company_name,
            "symbol": symbol,
            "isin": isin,
            "board_url": None,
            "moneycontrol_stock_id": None,
            "status": "not_found"
        }

    print(f"  Moneycontrol results: {len(results)}")

    match = find_matching_stock(
        results,
        company_name,
        symbol,
        isin
    )

    if match is None:

        print("  ⚠ Results found, but no matching company.")

        return {
            "company_name": company_name,
            "symbol": symbol,
            "isin": isin,
            "board_url": None,
            "moneycontrol_stock_id": None,
            "status": "needs_review"
        }

    forum_url = match.get("forum_topics_url")

    if not forum_url:

        print("  ⚠ Company found, but no forum URL.")

        return {
            "company_name": company_name,
            "symbol": symbol,
            "isin": isin,
            "board_url": None,
            "moneycontrol_stock_id": match.get("sc_id"),
            "status": "needs_review"
        }

    print(f"  ✓ Moneycontrol stock: {match.get('stock_name')}")
    print(f"  ✓ Forum URL: {forum_url}")

    return {
        "company_name": company_name,
        "symbol": symbol,
        "isin": isin,
        "board_url": forum_url,
        "moneycontrol_stock_id": match.get("sc_id"),
        "moneycontrol_stock_name": match.get("stock_name"),
        "moneycontrol_sector": match.get("sc_sector"),
        "status": "verified"
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("HINGFIN - Moneycontrol Board URL Resolver")
    print("=" * 60)

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print()
        print("ERROR: NIFTY50.csv not found:")
        print(INPUT_FILE)
        return

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print()
    print(f"Loaded {len(df)} companies.")

    # --------------------------------------------------------
    # Check columns
    # --------------------------------------------------------

    required_columns = [
        "Company Name",
        "Symbol",
        "ISIN Code"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print()
        print("ERROR: Missing columns:")
        print(missing_columns)
        print()
        print("Available columns:")
        print(list(df.columns))

        return

    # --------------------------------------------------------
    # Resolve companies
    # --------------------------------------------------------

    results = {}

    for index, row in df.iterrows():

        company_name = str(
            row["Company Name"]
        ).strip()

        symbol = str(
            row["Symbol"]
        ).strip()

        isin = str(
            row["ISIN Code"]
        ).strip()

        result = process_company(
            company_name,
            symbol,
            isin
        )

        results[symbol] = result

        # Don't hammer Moneycontrol
        if index < len(df) - 1:

            print(
                f"  Waiting {DELAY_SECONDS} seconds..."
            )

            time.sleep(DELAY_SECONDS)

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    verified = sum(
        1
        for result in results.values()
        if result["status"] == "verified"
    )

    needs_review = sum(
        1
        for result in results.values()
        if result["status"] == "needs_review"
    )

    not_found = sum(
        1
        for result in results.values()
        if result["status"] == "not_found"
    )

    print()
    print("=" * 60)
    print("RESOLUTION COMPLETE")
    print("=" * 60)

    print(f"Total companies : {len(results)}")
    print(f"Verified        : {verified}")
    print(f"Needs review    : {needs_review}")
    print(f"Not found       : {not_found}")

    print()
    print("Output:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()