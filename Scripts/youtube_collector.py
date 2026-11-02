import os
import csv
from dotenv import load_dotenv
from googleapiclient.discovery import build

# -----------------------------
# SETTINGS
# -----------------------------
COMPANY = "Adani Enterprises Ltd."
TICKER = "ADANIENT"
TARGET_COMMENTS = 1000

SEARCH_QUERIES = [
    "Adani Enterprises share",
    "Adani Enterprises stock",
    "Adani Enterprises analysis",
    "Adani Enterprises target",
    "Adani Enterprises results",
    "ADANIENT share",
    "ADANIENT stock",
]

# -----------------------------
# LOAD API KEY
# -----------------------------
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env")

youtube = build("youtube", "v3", developerKey=API_KEY)


# -----------------------------
# SEARCH VIDEOS
# -----------------------------
def search_videos(query, max_pages=3):
    videos = []
    next_page_token = None

    for _ in range(max_pages):
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=50,
            pageToken=next_page_token
        )

        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"].get("videoId")

            if not video_id:
                continue

            title = item["snippet"]["title"]

            # Keep videos specifically about Adani Enterprises
            title_lower = title.lower()

            if (
                "adani enterprises" in title_lower
                or "adani enterprise" in title_lower
                or "adanient" in title_lower
            ):
                # Exclude obvious other Adani companies
                excluded = [
                    "adani ports",
                    "adani power",
                    "adani green",
                    "adani wilmar",
                    "adani energy solutions",
                    "adani total gas",
                    "atgl",
                    "ambuja",
                    "acc limited"
                ]

                if not any(word in title_lower for word in excluded):
                    videos.append({
                        "video_id": video_id,
                        "title": title,
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"]
                    })

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    return videos


# -----------------------------
# COLLECT COMMENTS
# -----------------------------
def collect_comments(video):
    comments = []
    next_page_token = None

    while len(comments) < TARGET_COMMENTS:

        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video["video_id"],
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText",
                order="relevance"
            )

            response = request.execute()

        except Exception as e:
            print(f"  Could not collect comments: {e}")
            break

        for item in response.get("items", []):

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comment_text = snippet.get("textDisplay", "").strip()

            if not comment_text:
                continue

            comments.append({
                "company": COMPANY,
                "ticker": TICKER,
                "comment": comment_text,
                "video_title": video["title"],
                "channel": video["channel"],
                "video_id": video["video_id"],
                "video_published_at": video["published_at"],
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "comment_date": snippet.get("publishedAt", ""),
                "likes": snippet.get("likeCount", 0),
                "youtube_url": f"https://www.youtube.com/watch?v={video['video_id']}"
            })

            if len(comments) >= TARGET_COMMENTS:
                break

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    return comments


# -----------------------------
# MAIN
# -----------------------------
def main():

    print(f"\nCollecting raw YouTube comments for {TICKER}")
    print(f"Target: {TARGET_COMMENTS} comments\n")

    all_videos = {}

    # Find videos
    for query in SEARCH_QUERIES:

        print(f"Searching: {query}")

        videos = search_videos(query)

        for video in videos:
            all_videos[video["video_id"]] = video

    videos = list(all_videos.values())

    print(f"\nFound {len(videos)} relevant videos.")

    if not videos:
        print("No relevant videos found.")
        return

    # Collect comments
    all_comments = []
    seen_comment_ids = set()

    for i, video in enumerate(videos, start=1):

        if len(all_comments) >= TARGET_COMMENTS:
            break

        print(
            f"\n[{i}/{len(videos)}] "
            f"{video['title']}"
        )

        comments = collect_comments(video)

        added = 0

        for comment in comments:

            if comment["comment_id"] in seen_comment_ids:
                continue

            seen_comment_ids.add(comment["comment_id"])
            all_comments.append(comment)
            added += 1

            if len(all_comments) >= TARGET_COMMENTS:
                break

        print(f"Added: {added}")
        print(f"Total unique comments: {len(all_comments)}")

    # -----------------------------
    # SAVE
    # -----------------------------
    output_dir = os.path.join(
        "StockMarket",
        "Dataset",
        "Comments",
        "YouTube"
    )

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(
        output_dir,
        f"{TICKER}_raw_1000.csv"
    )

    fieldnames = [
        "company",
        "ticker",
        "comment",
        "video_title",
        "channel",
        "video_id",
        "video_published_at",
        "comment_id",
        "comment_date",
        "likes",
        "youtube_url"
    ]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(all_comments)

    print("\n================================")
    print("COLLECTION COMPLETE")
    print("================================")
    print(f"Videos found: {len(videos)}")
    print(f"Comments collected: {len(all_comments)}")
    print(f"Saved to: {output_file}")
    print("================================")


if __name__ == "__main__":
    main()