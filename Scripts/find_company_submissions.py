import json
import os
import re
import time

import pandas as pd
from dotenv import load_dotenv
import praw
from prawcore.exceptions import PrawcoreException

from nifty_aliases import ALIASES
from reddit_subreddits import REDDIT_SUBREDDITS
from relevance import is_valid_source_text


# ============================================================
# PATHS
# ============================================================

NIFTY_FILE = (
    "StockMarket/Dataset/NIFTY50.csv"
)

OUTPUT_FILE = (
    "StockMarket/Dataset/Comments/Reddit/company_submissions.json"
)

SUBMISSIONS_PER_COMPANY_PER_SUBREDDIT = 5


# ============================================================
# LOAD API
# ============================================================

load_dotenv()

CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT", "hingfin-collector/0.1")

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not found in .env")
    exit()

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
)
reddit.read_only = True


# ============================================================
# LOAD NIFTY 50 COMPANIES
# ============================================================

companies_df = pd.read_csv(
    NIFTY_FILE
)

print(
    f"Loaded {len(companies_df)} NIFTY 50 companies"
)


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\u0900-\u097f]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# BUILD SEARCH TERMS (same approach as find_company_videos.py)
# ============================================================

company_terms = {}

for _, row in companies_df.iterrows():

    company_name = str(row["Company Name"]).strip()
    symbol = str(row["Symbol"]).strip()

    terms = [
        company_name,
        symbol,
    ]

    if symbol in ALIASES:
        terms.extend(ALIASES[symbol])

    # Reddit search works better with the cleanest, most distinctive
    # term rather than every alias at once -- use the shortest alias
    # (usually the colloquial name) as the primary search query, and
    # keep the rest only for later title/selftext matching.
    terms = [t for t in terms if len(t.strip()) >= 3]

    company_terms[symbol] = {
        "company_name": company_name,
        "primary_query": min(terms, key=len),
        "all_terms": list(set(normalize(t) for t in terms)),
    }


# ============================================================
# SEARCH REDDIT PER COMPANY
# ============================================================

company_submissions = {}

skipped_no_finance_context = 0
skipped_no_alias_match = 0

for symbol, info in company_terms.items():

    print()
    print("=" * 60)
    print(f"{symbol} ({info['company_name']})")
    print("=" * 60)

    company_submissions[symbol] = {
        "company_name": info["company_name"],
        "symbol": symbol,
        "submissions": [],
    }

    seen_ids = set()

    for subreddit_name in REDDIT_SUBREDDITS:

        try:
            subreddit = reddit.subreddit(subreddit_name)

            results = subreddit.search(
                info["primary_query"],
                sort="relevance",
                time_filter="year",
                limit=SUBMISSIONS_PER_COMPANY_PER_SUBREDDIT,
            )

            for submission in results:

                if submission.id in seen_ids:
                    continue

                title = submission.title or ""
                selftext = submission.selftext or ""

                title_norm = normalize(title)

                # Require an explicit alias/company match in the title
                # OR selftext -- otherwise we're relying on Reddit's own
                # search relevance alone, which is looser than we want.
                matched = False
                for term in info["all_terms"]:
                    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
                    if re.search(pattern, title_norm) or re.search(pattern, normalize(selftext)):
                        matched = True
                        break

                if not matched:
                    skipped_no_alias_match += 1
                    continue

                # Same finance-context gate as the YouTube pipeline --
                # keeps out non-market posts that happen to mention the
                # company name (memes, product complaints, etc).
                if not is_valid_source_text(title, selftext):
                    skipped_no_finance_context += 1
                    continue

                seen_ids.add(submission.id)

                company_submissions[symbol]["submissions"].append({
                    "submission_id": submission.id,
                    "title": title,
                    "selftext": selftext[:500],
                    "subreddit": subreddit_name,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                })

            time.sleep(0.5)

        except PrawcoreException as e:
            print(f"  search error in r/{subreddit_name}: {e}")

    count = len(company_submissions[symbol]["submissions"])
    print(f"  Matched submissions: {count}")


# ============================================================
# SAVE RESULTS
# ============================================================

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(company_submissions, f, ensure_ascii=False, indent=2)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("SUBMISSION MATCHING COMPLETE")
print("=" * 70)

total = sum(len(v["submissions"]) for v in company_submissions.values())

for symbol, data in company_submissions.items():
    print(f"{symbol:<15} {data['company_name']:<40} {len(data['submissions'])} submissions")

print("=" * 70)
print(f"Total company-submission matches: {total}")
print(f"Skipped (no alias match in title/selftext): {skipped_no_alias_match}")
print(f"Skipped (matched name but no finance context): {skipped_no_finance_context}")
print(f"Saved to: {OUTPUT_FILE}")
print("=" * 70)
