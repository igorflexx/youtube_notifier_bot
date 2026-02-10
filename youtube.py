import requests
import feedparser

def resolve_channel(url: str):
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
        html = requests.get(f"https://www.youtube.com/@{handle}").text
        marker = '"channelId":"'
        if marker in html:
            return html.split(marker)[1].split('"')[0]

    return None

def get_channel_info(channel_id: str):
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )
    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
