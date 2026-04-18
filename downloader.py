#!/usr/bin/env python3
"""
YouTube Playlist MP3 Downloader
Downloads every track in a YouTube playlist as high-quality MP3 files,
with embedded metadata (title, artist, cover art) and resume support.

Usage:
    python downloader.py <playlist_url> [options]

Requirements:
    pip install -r requirements.txt
    ffmpeg must be installed and available in PATH
"""

import re
import sys
import argparse
import concurrent.futures
from pathlib import Path

import yt_dlp
from tqdm import tqdm


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = name.strip('. ')
    return name or 'unknown'


def download_track(
    entry: dict,
    output_dir: Path,
    index: int,
    quality: str,
    progress_bar: tqdm,
) -> str:
    video_id = entry.get('id', '')
    if not video_id:
        progress_bar.update(1)
        return 'error: missing video id'

    url = f"https://www.youtube.com/watch?v={video_id}"
    title = sanitize_filename(entry.get('title', video_id))
    prefix = f"{index:03d} - "
    base_name = prefix + title

    # Skip if already downloaded
    if (output_dir / f"{base_name}.mp3").exists():
        progress_bar.update(1)
        progress_bar.write(f"  [skip] {base_name}")
        return f"skipped: {base_name}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / f"{base_name}.%(ext)s"),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                # quality '0' = VBR best (~245 kbps avg, peaks 320 kbps)
                # quality '320' = CBR 320 kbps
                'preferredquality': quality,
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {
                'key': 'EmbedThumbnail',
            },
        ],
        'writethumbnail': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 3,
        'fragment_retries': 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        progress_bar.write(f"  [ok]   {base_name}")
        return f"ok: {base_name}"
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).splitlines()[0]
        progress_bar.write(f"  [err]  {base_name}: {msg}")
        return f"error: {base_name}"
    finally:
        progress_bar.update(1)


def fetch_playlist_info(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def download_playlist(
    url: str,
    workers: int = 4,
    quality: str = '0',
    output_base: Path = Path('.'),
) -> None:
    print(f"Fetching playlist info...")
    info = fetch_playlist_info(url)

    if not info:
        print("Error: could not retrieve playlist information.")
        sys.exit(1)

    if info.get('_type') != 'playlist':
        print("Error: URL does not point to a YouTube playlist.")
        sys.exit(1)

    playlist_title = sanitize_filename(info.get('title', 'playlist'))
    entries = [e for e in info.get('entries', []) if e]
    total = len(entries)

    if total == 0:
        print("Error: playlist is empty or private.")
        sys.exit(1)

    output_dir = output_base / playlist_title
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_label = f"VBR best (~245 kbps avg)" if quality == '0' else f"CBR {quality} kbps"
    print(f"Playlist : {playlist_title}")
    print(f"Tracks   : {total}")
    print(f"Quality  : {quality_label}")
    print(f"Output   : {output_dir.resolve()}")
    print(f"Workers  : {workers}")
    print()

    results = {'ok': 0, 'skipped': 0, 'error': 0}

    with tqdm(total=total, unit='track', ncols=72, desc='Downloading') as bar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(download_track, entry, output_dir, idx + 1, quality, bar): entry
                for idx, entry in enumerate(entries)
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result.startswith('ok'):
                    results['ok'] += 1
                elif result.startswith('skipped'):
                    results['skipped'] += 1
                else:
                    results['error'] += 1

    print()
    print(
        f"Done — {results['ok']} downloaded, "
        f"{results['skipped']} skipped, "
        f"{results['error']} errors"
    )
    print(f"Files saved to: {output_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Download a YouTube playlist as MP3 files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx"
  python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -w 2
  python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -o ~/Music --cbr
        """,
    )
    parser.add_argument('url', help='YouTube playlist URL')
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        metavar='N',
        help='Number of concurrent downloads (default: 4)',
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('.'),
        metavar='DIR',
        help='Base output directory (default: current directory)',
    )
    parser.add_argument(
        '--cbr',
        action='store_true',
        help='Use CBR 320 kbps instead of VBR best quality',
    )

    args = parser.parse_args()
    quality = '320' if args.cbr else '0'

    download_playlist(
        url=args.url,
        workers=args.workers,
        quality=quality,
        output_base=args.output,
    )


if __name__ == '__main__':
    main()
