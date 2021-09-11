import os

from dotenv import load_dotenv
from dateutil.parser import parse
from sqlmodel import Session, select
import requests

from youtube.models import YouTube, engine

load_dotenv()

YT_CHANNEL = os.environ["YT_CHANNEL"]
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
YOUTUBE_VIDEO = "youtube#video"
BASE_URL = (
    f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}"
    f"&channelId={YT_CHANNEL}&part=snippet,id&order=date&maxResults=20"
)


def get_videos_from_channel(channel: str = YT_CHANNEL) -> list[dict]:
    videos = []
    next_page, url = None, BASE_URL
    while True:
        if next_page is not None:
            url = BASE_URL + f"&pageToken={next_page}"

        response = requests.get(url).json()

        for vid in response["items"]:
            if vid["id"]["kind"] != "youtube#video":
                continue
            videos.append(vid)

        if "nextPageToken" not in response:
            break

        next_page = response["nextPageToken"]

    return videos


def insert_youtube_videos(videos: list[dict]) -> None:
    num_inserted = 0
    with Session(engine) as session:
        for video in videos:
            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]
            description = video["snippet"]["description"]
            thumb = video["snippet"]["thumbnails"]["medium"]["url"]
            published = video["snippet"]["publishTime"]

            statement = select(YouTube).where(YouTube.video_id == video_id)
            results = session.exec(statement)
            if results.first() is not None:
                continue

            youtube = YouTube(
                video_id=video_id,
                title=title,
                description=description,
                thumb=thumb,
                published=parse(published),
            )

            session.add(youtube)
            num_inserted += 1

        session.commit()

        statement = select(YouTube)
        results = session.exec(statement)
        total_records = len(results.all())
        print(f"Total records: {total_records} (newly inserted: {num_inserted})")


if __name__ == "__main__":
    videos = get_videos_from_channel()
    insert_youtube_videos(videos)
