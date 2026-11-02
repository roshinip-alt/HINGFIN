import os
from dotenv import load_dotenv
import praw

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

# Test request
subreddit = reddit.subreddit("IndianStreetBets")

print("Reddit API is working!")
print("Subreddit:", subreddit.display_name)
print("Subscribers:", subreddit.subscribers)

print()
print("Test search: 'Reliance' in r/IndianStreetBets")

for submission in subreddit.search("Reliance", limit=3):
    print("-", submission.title)
