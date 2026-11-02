import os
import json
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv
import praw
from prawcore.exceptions import PrawcoreException

from relevance import classify_submission, is_relevant_comment


# ============================================================
# PATHS
# ============================================================

BASE_DIR = "StockMarket/Dataset/Comments/Reddit"

SUBMISSIONS_FILE = os.path.join(
    BASE_DIR,
    "company_submissions.json"
)

DB_FILE = os.path.join(
    BASE_DIR,
    "reddit_comments.db"
)


# ============================================================
# SETTINGS
# ============================================================

TARGET_COMMENTS_PER_COMPANY = 20


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
# LOAD COMPANY SUBMISSIONS
# ============================================================

if not os.path.exists(SUBMISSIONS_FILE):
    print("ERROR: company_submissions.json not found. Run find_company_submissions.py first.")
    exit()

with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
    company_submissions = json.load(f)


# ============================================================
# CONNECT DATABASE
# ============================================================

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    ticker TEXT,
    comment_id TEXT UNIQUE,
    comment_text TEXT,
    submission_id TEXT,
    submission_title TEXT,
    subreddit TEXT,
    parent_comment_id TEXT,
    is_reply INTEGER,
    published_at TEXT,
    like_count INTEGER,
    collected_at TEXT,
    sentiment TEXT,
    sentiment_confidence REAL,
    post_mode TEXT,
    match_reason TEXT
)
""")

conn.commit()


# ============================================================
# JUNK / BOT / REMOVED-COMMENT CHECK
# ============================================================
# Reddit-specific junk that YouTube doesn't have: [deleted]/[removed]
# bodies, and AutoModerator's own posts (pinned rules/disclaimer
# comments that show up on almost every thread and are never about any
# stock).

def is_removed_or_bot(comment):

    if comment.body in ("[deleted]", "[removed]", ""):
        return True

    author_name = str(comment.author) if comment.author else ""

    if author_name in ("AutoModerator", "[deleted]"):
        return True

    return False


# ============================================================
# GET EXISTING COMMENTS / COUNTS
# ============================================================

cursor.execute("SELECT comment_id FROM comments")
existing_comment_ids = {row[0] for row in cursor.fetchall()}


def get_comment_count(ticker):
    cursor.execute(
        "SELECT COUNT(*) FROM comments WHERE ticker = ?",
        (ticker,)
    )
    return cursor.fetchone()[0]


# ============================================================
# COLLECT COMMENTS FROM ONE SUBMISSION
# ============================================================

def collect_submission_comments(ticker, company_name, submission_info):

    submission_id = submission_info.get("submission_id")

    if not submission_id:
        return 0

    title = submission_info.get("title", "")
    selftext = submission_info.get("selftext", "")
    subreddit_name = submission_info.get("subreddit", "")

    # CHANGED (same idea as the YouTube fix): classify this submission
    # once -- 'single' if it's dedicated to this company (a discussion
    # post about just this stock), 'multi' if it's a roundup/daily
    # discussion thread that could be about any stock, in which case a
    # comment must name this company explicitly to be kept.
    post_mode = classify_submission(f"{title} {selftext}", ticker)

    try:
        submission = reddit.submission(id=submission_id)
        submission.comments.replace_more(limit=0)
        comment_list = submission.comments.list()
    except PrawcoreException as e:
        print(f"    comment fetch error on {submission_id}: {e}")
        return 0

    collected = 0
    skipped_irrelevant = 0
    skipped_junk = 0

    for comment in comment_list:

        if get_comment_count(ticker) >= TARGET_COMMENTS_PER_COMPANY:
            break

        if comment.id in existing_comment_ids:
            continue

        if is_removed_or_bot(comment):
            skipped_junk += 1
            continue

        comment_text = comment.body

        is_relevant, reason = is_relevant_comment(
            comment_text,
            ticker,
            post_mode,
        )

        if not is_relevant:
            skipped_irrelevant += 1
            continue

        author_name = str(comment.author) if comment.author else "deleted"

        collected_at = datetime.now(timezone.utc).isoformat()

        cursor.execute(
            """
            INSERT INTO comments (
                company,
                ticker,
                comment_id,
                comment_text,
                submission_id,
                submission_title,
                subreddit,
                parent_comment_id,
                is_reply,
                published_at,
                like_count,
                collected_at,
                sentiment,
                sentiment_confidence,
                post_mode,
                match_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                ticker,
                comment.id,
                comment_text,
                submission_id,
                title,
                subreddit_name,
                None,
                0,
                datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
                comment.score,
                collected_at,
                None,
                None,
                post_mode,
                reason,
            )
        )

        conn.commit()

        existing_comment_ids.add(comment.id)
        collected += 1

    print(f"    (skipped {skipped_irrelevant} irrelevant, {skipped_junk} removed/bot comments)")

    return collected


# ============================================================
# MAIN COLLECTION LOOP
# ============================================================

print()
print("=" * 60)
print("REDDIT COMMENT COLLECTION")
print("=" * 60)
print()

for ticker, entry in company_submissions.items():

    company_name = entry.get("company_name", ticker)
    submissions = entry.get("submissions", [])

    current_count = get_comment_count(ticker)

    if current_count >= TARGET_COMMENTS_PER_COMPANY:
        print(f"{ticker}: {current_count}/{TARGET_COMMENTS_PER_COMPANY} already complete - SKIPPING")
        continue

    needed = TARGET_COMMENTS_PER_COMPANY - current_count

    print()
    print(f"{ticker}: {current_count}/{TARGET_COMMENTS_PER_COMPANY}")
    print(f"Need {needed} more comments")
    print(f"Candidate submissions: {len(submissions)}")

    for sub_number, submission_info in enumerate(submissions, start=1):

        if get_comment_count(ticker) >= TARGET_COMMENTS_PER_COMPANY:
            break

        print()
        print(f"  Submission {sub_number}/{len(submissions)}")
        print(f"  Title: {submission_info.get('title', '')}")
        print(f"  Subreddit: r/{submission_info.get('subreddit', '')}")

        before = get_comment_count(ticker)

        collect_submission_comments(
            ticker=ticker,
            company_name=company_name,
            submission_info=submission_info,
        )

        after = get_comment_count(ticker)

        print(f"  Added: {after - before}")
        print(f"  Total: {after}/{TARGET_COMMENTS_PER_COMPANY}")

    final_count = get_comment_count(ticker)
    print()
    if final_count >= TARGET_COMMENTS_PER_COMPANY:
        print(f"{ticker}: {final_count}/{TARGET_COMMENTS_PER_COMPANY} COMPLETE")
    else:
        print(f"{ticker}: {final_count}/{TARGET_COMMENTS_PER_COMPANY} STILL NEEDS {TARGET_COMMENTS_PER_COMPANY - final_count}")


# ============================================================
# FINAL SUMMARY
# ============================================================

cursor.execute("SELECT COUNT(*) FROM comments")
total_comments = cursor.fetchone()[0]

print()
print("=" * 60)
print("COLLECTION FINISHED")
print("=" * 60)
print(f"Total Reddit comments: {total_comments}")
print(f"Target: {TARGET_COMMENTS_PER_COMPANY * len(company_submissions)}")
print("=" * 60)

conn.close()
