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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import yt_dlp
from tqdm import tqdm


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = name.strip('. ')
    return name or 'unknown'


# Prefijos de listas que YouTube genera dinámicamente y requieren el v= del video
# para poder ser consultadas. Convertirlas a playlist?list= las rompe.
_DYNAMIC_LIST_PREFIXES = ('RD', 'RDEM', 'RDMIX', 'RDCLAK', 'OLA', 'FL', 'LL')


def normalize_playlist_url(url: str) -> tuple[str, str]:
    """
    Analiza la URL y devuelve (url_para_fetch, tipo).

    Tipos:
      'playlist' → lista normal PL..., puede usarse como playlist?list=
      'mix'      → Radio/Mix RD..., requiere conservar el v= original
      'unknown'  → sin list=, se usará la URL tal cual

    Soporta todos estos formatos:
      https://www.youtube.com/watch?v=XXX&list=PLyyy
      https://www.youtube.com/watch?v=XXX&list=RDxxx&start_radio=1
      https://www.youtube.com/playlist?list=PLyyy
      https://youtu.be/XXX?list=PLyyy
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    list_id = params.get('list', [None])[0]
    video_id = params.get('v', [None])[0]

    if not list_id:
        return url, 'unknown'

    # Radio/Mix: conservar v= para que YouTube pueda generar la lista
    if list_id.startswith(_DYNAMIC_LIST_PREFIXES):
        if video_id:
            clean = f"https://www.youtube.com/watch?v={video_id}&list={list_id}"
        else:
            clean = url
        return clean, 'mix'

    # Lista normal: URL canónica sin parámetros extra
    return f"https://www.youtube.com/playlist?list={list_id}", 'playlist'


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
        'postprocessors': _postprocessors(quality),
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


def fetch_playlist_info(url: str) -> dict | None:
    """Intenta extraer metadatos de la playlist sin descargar."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
        'yes_playlist': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None


def _postprocessors(quality: str) -> list:
    return [
        {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality},
        {'key': 'FFmpegMetadata', 'add_metadata': True},
        {'key': 'EmbedThumbnail'},
    ]


def download_mix_direct(url: str, output_dir: Path, quality: str) -> dict:
    """
    Descarga un Radio/Mix directamente sin pre-fetch de entradas.
    Usado como fallback cuando extract_flat falla en listas RD.
    yt-dlp maneja internamente la paginación del mix.
    """
    results = {'ok': 0, 'skipped': 0, 'error': 0}

    def _hook(d: dict) -> None:
        if d['status'] == 'finished':
            fname = Path(d.get('filename', '')).stem
            print(f"  [ok]   {fname}")
            results['ok'] += 1
        elif d['status'] == 'error':
            results['error'] += 1

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / '%(playlist_index)03d - %(title)s.%(ext)s'),
        'postprocessors': _postprocessors(quality),
        'writethumbnail': True,
        'yes_playlist': True,
        'ignoreerrors': True,
        'retries': 3,
        'fragment_retries': 3,
        'progress_hooks': [_hook],
        'quiet': True,
        'no_warnings': True,
    }

    print("Descargando Radio/Mix directamente (sin pre-fetch)...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return results


def download_playlist(
    url: str,
    workers: int = 4,
    quality: str = '0',
    output_base: Path = Path('.'),
) -> None:
    clean_url, url_type = normalize_playlist_url(url)

    type_labels = {'playlist': 'Lista normal', 'mix': 'Radio/Mix', 'unknown': 'URL directa'}
    print(f"Tipo detectado : {type_labels.get(url_type, url_type)}")
    if clean_url != url:
        print(f"URL procesada  : {clean_url}")

    print("Fetching playlist info...")
    info = fetch_playlist_info(clean_url)
    entries = [e for e in (info or {}).get('entries', []) if e]

    # Para mixes que no responden al extract_flat, descarga directa con yt-dlp
    if not entries and url_type == 'mix':
        print("Pre-fetch no disponible para este Mix. Cambiando a modo descarga directa...")
        playlist_title = sanitize_filename((info or {}).get('title', 'YouTube Mix'))
        output_dir = output_base / playlist_title
        output_dir.mkdir(parents=True, exist_ok=True)
        quality_label = "VBR best" if quality == '0' else f"CBR {quality} kbps"
        print(f"Playlist : {playlist_title}")
        print(f"Quality  : {quality_label}")
        print(f"Output   : {output_dir.resolve()}")
        print()
        results = download_mix_direct(clean_url, output_dir, quality)
        print()
        print(f"Done — {results['ok']} downloaded, {results['error']} errors")
        print(f"Files saved to: {output_dir.resolve()}")
        return

    if not entries:
        print("Error: la lista está vacía, es privada o la URL no es válida.")
        if info:
            print(f"  _type detectado : {info.get('_type', 'desconocido')}")
        print(f"  URL usada       : {clean_url}")
        sys.exit(1)

    playlist_title = sanitize_filename(info.get('title', 'playlist'))
    total = len(entries)
    output_dir = output_base / playlist_title
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_label = "VBR best (~245 kbps avg)" if quality == '0' else f"CBR {quality} kbps"
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
