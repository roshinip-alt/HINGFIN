
import googleapiclient.discovery
import googleapiclient.errors
import csv
import os

API_KEY = "AIzaSyCKwSjP8PhK6DfnjnH8M3U9uYe8WoQGraA"
VIDEO_ID = "MxzGxkVsVmk"

youtube = googleapiclient.discovery.build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

comments = []

try:
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=VIDEO_ID,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "video_id": VIDEO_ID,
                "comment": comment["textDisplay"],
                "published_at": comment["publishedAt"],
                "like_count": comment["likeCount"]
            })

        request = youtube.commentThreads().list_next(
            request, response
        )

    print(f"Total comments extracted: {len(comments)}")

    # Append to the existing CSV without deleting old comments
    file_exists = os.path.exists("youtube_comments.csv")
    file_has_data = (
        file_exists and os.path.getsize("youtube_comments.csv") > 0
    )

    with open(
        "youtube_comments.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "video_id",
                "comment",
                "published_at",
                "like_count"
            ]
        )

        # Write the header only if the file is new or empty
        if not file_has_data:
            writer.writeheader()

        writer.writerows(comments)

    print("New comments appended to youtube_comments.csv")
    print("Existing comments have been preserved.")

except googleapiclient.errors.HttpError as e:
    print(f"YouTube API error: {e}")
