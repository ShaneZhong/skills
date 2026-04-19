"""
Find a single YouTube AI interview/podcast video matching Shane's criteria.

Criteria:
- Human-to-human conversation (interview / podcast), not promotional
- Duration > 10 minutes
- Upload date: this month
- Avoid generic "what is AI" explainers
- Prefer actionable advice or "how someone uses AI for X"
- No duplicates (track in used_videos.json)

Output:
- candidates_{date}.json — all filtered candidates
- pick_{date}.json — chosen video with reasoning
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

ROOT = Path("/Users/shane/Documents/playground/ai_writing/auto_youtube_finder")
USED_VIDEOS_PATH = ROOT / "used_videos.json"

SEARCH_QUERIES = [
    "AI interview",
    "AI podcast",
    "interview AI founder",
]

ACTOR_ID = "streamers/youtube-scraper"
MAX_RESULTS_PER_QUERY = 25


def load_used_videos() -> set[str]:
    if not USED_VIDEOS_PATH.exists():
        return set()
    with USED_VIDEOS_PATH.open() as f:
        data = json.load(f)
    return set(data.get("video_ids", []))


def parse_duration_seconds(duration: str | int | None) -> int:
    if duration is None:
        return 0
    if isinstance(duration, int):
        return duration
    if isinstance(duration, str) and duration.isdigit():
        return int(duration)
    if isinstance(duration, str):
        parts = duration.split(":")
        try:
            parts = [int(p) for p in parts]
        except ValueError:
            return 0
        if len(parts) == 3:
            h, m, s = parts
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = parts
            return m * 60 + s
        if len(parts) == 1:
            return parts[0]
    return 0


def main() -> None:
    load_dotenv("/Users/shane/Documents/playground/.env")
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        log.error("APIFY_TOKEN not found in .env")
        sys.exit(1)

    used = load_used_videos()
    log.info("Loaded %d previously used video IDs", len(used))

    client = ApifyClient(token)

    actor = client.actor(ACTOR_ID)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    all_candidates: list[dict] = []

    for query in SEARCH_QUERIES:
        log.info("Searching: %r", query)
        run_input = {
            "searchKeywords": query,
            "maxResults": MAX_RESULTS_PER_QUERY,
            "maxResultsShorts": 0,
            "uploadDate": "month",
            "duration": "medium",
            "features": "",
            "sort": "r",
        }
        run = actor.call(run_input=run_input, timeout_secs=300)
        if run is None:
            log.warning("Actor call returned None for query %r", query)
            continue
        log.info("Run %s status=%s", run["id"], run["status"])
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        log.info("Got %d raw items for %r", len(items), query)
        for it in items:
            it["_search_query"] = query
            all_candidates.append(it)

    log.info("Total raw items across all queries: %d", len(all_candidates))

    candidates_raw_path = ROOT / f"candidates_raw_{today}.json"
    with candidates_raw_path.open("w") as f:
        json.dump(all_candidates, f, indent=2, default=str)
    log.info("Wrote raw candidates to %s", candidates_raw_path)

    seen_ids: set[str] = set()
    filtered: list[dict] = []
    for it in all_candidates:
        vid = it.get("id") or it.get("videoId") or ""
        if not vid:
            continue
        if vid in seen_ids:
            continue
        seen_ids.add(vid)
        if vid in used:
            continue

        duration_sec = parse_duration_seconds(it.get("duration"))
        if duration_sec < 10 * 60:
            continue
        if duration_sec > 3 * 3600:
            continue

        filtered.append(
            {
                "id": vid,
                "title": it.get("title"),
                "url": it.get("url") or f"https://www.youtube.com/watch?v={vid}",
                "channel": (it.get("channelName") or it.get("channel") or {}),
                "duration": it.get("duration"),
                "duration_seconds": duration_sec,
                "viewCount": it.get("viewCount"),
                "date": it.get("date") or it.get("uploadDate") or it.get("publishedAt"),
                "description": (it.get("text") or it.get("description") or "")[:500],
                "search_query": it.get("_search_query"),
            }
        )

    log.info("After filter (dedup + duration + not-used): %d candidates", len(filtered))

    candidates_path = ROOT / f"candidates_{today}.json"
    with candidates_path.open("w") as f:
        json.dump(filtered, f, indent=2, default=str)
    log.info("Wrote %d filtered candidates to %s", len(filtered), candidates_path)

    print(json.dumps(filtered[:30], indent=2, default=str))


if __name__ == "__main__":
    main()
