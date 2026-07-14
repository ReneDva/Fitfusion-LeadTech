"""Exercise demo videos: curated YouTube links (data/exercise_videos.json), falling back to
a YouTube search when a specific video hasn't been assigned yet."""
import json

from fitfusion.config import DATA_DIR

with open(DATA_DIR / "exercise_videos.json", "r", encoding="utf-8") as f:
    _RAW = json.load(f)

EXERCISE_VIDEOS = {k: v for k, v in _RAW.items() if not k.startswith("_")}


def get_demo_video_url(exercise_id: str, exercise_name: str = "") -> str:
    url = EXERCISE_VIDEOS.get(exercise_id)
    if url:
        return url
    query = (exercise_name or exercise_id.replace("_", " ")) + " exercise proper form tutorial"
    return "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
