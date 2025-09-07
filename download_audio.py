from __future__ import annotations

import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import yt_dlp
import innertube

COLLECTED_IDS_FILE = Path("collected_ids.txt")

# ──────────────────── YouTube‑Music helper ──────────────────────
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
        description="Download YouTube audio as WAV; optional YT-Music filter."
    )
    p.add_argument("--ids", type=Path,
                   help="Text file with one YouTube video ID per line.")
    p.add_argument("--out_dir", type=Path,
                   help="Directory for the .wav files (created if absent).")
    p.add_argument("--cookies", type=Path,
                   help="Path to cookies.txt (exported from browser).")
    p.add_argument("--threads", type=int, default=1,
                   help="Concurrent downloads (default 1).")
    p.add_argument("--filter-music", action="store_true",
                   help="Skip videos already on YouTube Music.")
    p.add_argument("--start", type=int, default=0,
                help="Start idx")
    p.add_argument("--stop", type=int, default=3000,
                help="Stop idx")
    return p.parse_args()


# ──────────────────── yt‑dlp config builder ─────────────────────
def _build_dl(out_dir: Path, cookies: Path | None) -> yt_dlp.YoutubeDL:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",
        }],
        "extractor_args": {"youtube": {"player_client": ["web"]}},
    }
    if cookies:
        opts["cookiefile"] = str(cookies)
    return yt_dlp.YoutubeDL(opts)


# ───────────────────────── downloader ───────────────────────────
def _download_one(ydl: yt_dlp.YoutubeDL, vid: str,
                  skip_music: bool) -> None:
    """Download a single video unless already downloaded or skipped."""

    if skip_music and _ytm_available(vid):
        print(f"[skip] {vid} found on YouTube Music")
        return vid

    try:
        ydl.download([f"https://www.youtube.com/watch?v={vid}"])
    
        return vid
    except Exception as exc:
        # Counting the number of sequential errors here we can detect if cookie has expired and alert the runner...
        print(f"[warn] Failed {vid}: {exc}", file=sys.stderr)
        return None


# ─────────────────────────── main ───────────────────────────────
def main() -> None:
    args = _parse()
    vid_ids = sorted({ln.strip() for ln in args.id_file.read_text().splitlines() if ln.strip()})[args.start:args.stop]
    if not vid_ids:
        sys.exit("No video IDs found.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ydl = _build_dl(args.out_dir, args.cookies)

    collected_ids = []
    with open(COLLECTED_IDS_FILE) as f:
        collected_ids = [l.strip() for l in f.readlines()]

    if args.threads == 1:
        for i, vid in enumerate(vid_ids):
            if vid in collected_ids:
                continue

            vid_id = _download_one(ydl, vid, args.filter_music)            
            collected_ids.append(vid_id)

            if i % 50 == 0:
                with open(COLLECTED_IDS_FILE) as f:
                    f.write("\n".join(collected_ids))

    else:
        with ThreadPoolExecutor(max_workers=args.threads) as pool:
            futs = {
                pool.submit(_download_one, ydl, vid, args.filter_music, args.out_dir): vid
                for vid in vid_ids
            }

            for f in as_completed(futs):
                f.result()   # re‑raise errors already logged

    print(f"[done] processed {len(vid_ids)} video(s)")


if __name__ == "__main__":
    main()
