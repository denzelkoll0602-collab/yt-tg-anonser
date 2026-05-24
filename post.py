"""YouTube to Telegram link autoposter."""

import json
import os
import sys

import feedparser
import requests

YT_PLAYLIST_ID = os.environ["YT_PLAYLIST_ID"]
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]
STATE_FILE = "seen.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"seen": [], "initialized": False}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    state = load_state()
    seen = set(state.get("seen", []))
    initialized = state.get("initialized", False)
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?playlist_id={YT_PLAYLIST_ID}"
    )
    if not feed.entries:
        return
    entry_ids = [e.yt_videoid for e in feed.entries]
    if not initialized:
        state["seen"] = entry_ids
        state["initialized"] = True
        save_state(state)
        print(f"First run: marked {len(entry_ids)} videos as seen.")
        return
    new_entries = [e for e in feed.entries if e.yt_videoid not in seen]
    if not new_entries:
        print("No new videos.")
        return
    for entry in reversed(new_entries):
        vid_id = entry.yt_videoid
        video_url = f"https://www.youtube.com/watch?v={vid_id}"
        try:
            send_telegram(video_url)
            print(f"Posted: {vid_id}")
            seen.add(vid_id)
        except Exception as exc:
            print(f"Failed: {exc}", file=sys.stderr)
    state["seen"] = list(seen)[-200:]
    save_state(state)


if __name__ == "__main__":
    main()
