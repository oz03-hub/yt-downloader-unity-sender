from __future__ import annotations

import argparse
import sys
import time
import random
import subprocess
import os
from pathlib import Path

import yt_dlp
from yt_dlp.utils import match_filter_func
import innertube

COLLECTED_IDS_FILE = Path("collected_ids.txt")

# =================== Config for rsync =====================
RSYNC_DEST = "unity://scratch3/workspace/oyilmazel_umass_edu-yt-lang-detect/wavs/"
RSYNC_CMD = [
    "rsync",
    "-avP", "--partial", "--info=progress2", "--bwlimit=20000",
    "-e", "ssh -i ~/.ssh/ytb_rsync_key -T -o Compression=no -o StrictHostKeyChecking=no",
]
# ===========================================================


# ──────────────────── YouTube-Music helper ──────────────────────
def _ytm_available(video_id: str, tries: int = 5) -> bool:
    """Return True if `video_id` is found on YouTube Music."""
    client = innertube.InnerTube("WEB_REMIX")
    query = f"inurl:{video_id}"
    for _ in range(tries):
        try:
            resp = client.search(query=query)
            s = str(resp).replace(query, "")
            if f"https://i.ytimg.com/vi/{video_id}" in s or \
               f"https://i.ytimg.com/vi_webp/{video_id}" in s:
                return True
            return False
        except Exception:
            # transient error → retry
            continue
    return False


# ──────────────────────── CLI parsing ───────────────────────────
def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download YouTube audio as WAV and send via rsync."
    )
    p.add_argument("--ids", type=Path,
                   help="Text file with one YouTube video ID per line.")
    p.add_argument("--out_dir", type=Path, required=True,
                   help="Directory for the .wav files (created if absent).")
    p.add_argument("--cookies", type=Path,
                   help="Path to cookies.txt (exported from browser).")
    p.add_argument("--filter-music", action="store_true",
                   help="Skip videos already on YouTube Music.")
    p.add_argument("--start", type=int, default=0,
                   help="Start idx")
    p.add_argument("--stop", type=int, default=3000,
                   help="Stop idx")
    return p.parse_args()


# ──────────────────── yt-dlp config builder ─────────────────────
def _build_dl(out_dir: Path, cookies: Path | None) -> yt_dlp.YoutubeDL:
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",
        }],
        "match_filter": match_filter_func("!is_live"),
	"live_from_start": False,
        "ignore_no_formats_error": True,
        "extractor_args": {"youtube": {"player_client": ["web"]}},
    }
    if cookies:
        opts["cookiefile"] = str(cookies)
    return yt_dlp.YoutubeDL(opts)


# ───────────────────────── downloader + sender ───────────────────────────
def _rsync_file(filepath: Path):
    try:
        cmd = RSYNC_CMD + [str(filepath), RSYNC_DEST]
        print(f"[rsync] {filepath} → {RSYNC_DEST}")
        subprocess.run(cmd, check=True)
        print(f"[rsync] done: {filepath}")
        filepath.unlink(missing_ok=True)
        print(f"[cleanup] deleted local file {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"[error] rsync failed for {filepath}: {e}")


def _download_one(ydl: yt_dlp.YoutubeDL, vid: str,
                  skip_music: bool, out_dir: Path) -> str | None:
    """Download one video, send via rsync, return video ID if successful."""
    if skip_music and _ytm_available(vid):
        print(f"[skip] {vid} found on YouTube Music")
        return vid

    try:
        ydl.download([f"https://www.youtube.com/watch?v={vid}"])
        # Find resulting .wav file
        candidate = next(out_dir.glob(f"{vid}*.wav"), None)
        if candidate and candidate.exists():
            _rsync_file(candidate)
        else:
            print(f"[warn] No .wav file found for {vid}")
            return None
        time.sleep(random.uniform(2, 6))  # polite delay
        return vid
    except Exception as exc:
        print(f"[warn] Failed {vid}: {exc}", file=sys.stderr)
        return None


# ─────────────────────────── main ───────────────────────────────
def main() -> None:
    args = _parse()
    vid_ids = sorted({ln.strip() for ln in args.ids.read_text().splitlines() if ln.strip()})[args.start:args.stop]
    if not vid_ids:
        sys.exit("No video IDs found.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ydl = _build_dl(args.out_dir, args.cookies)

    # load checkpoint of collected IDs
    collected_ids = set()
    if COLLECTED_IDS_FILE.exists():
        collected_ids.update(l.strip() for l in COLLECTED_IDS_FILE.read_text().splitlines() if l.strip())

    error_streak = 0

    for i, vid in enumerate(vid_ids, start=1):
        if vid in collected_ids:
            continue

        vid_id = _download_one(ydl, vid, args.filter_music, args.out_dir)
        if vid_id:
            collected_ids.add(vid_id)
            error_streak = 0
        else:
            error_streak += 1
            if error_streak >= 50:
                sys.exit("[fatal] 50 consecutive errors — aborting (likely bad cookies).")

        # checkpoint every 20 vids
        if i % 20 == 0:
            COLLECTED_IDS_FILE.write_text("\n".join(sorted(collected_ids)))

    # final checkpoint
    COLLECTED_IDS_FILE.write_text("\n".join(sorted(collected_ids)))
    print(f"[done] processed {len(vid_ids)} video(s)")


if __name__ == "__main__":
    main()
