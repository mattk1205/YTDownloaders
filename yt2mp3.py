#!/usr/bin/env python3
"""
Clean YouTube to MP3 Converter
No data collection, no tracking, just downloads.
"""
#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import re

def check_dependencies():
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except Exception:
        sys.stderr.write("ERROR: yt-dlp not installed.\n")
        sys.exit(1)
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except Exception:
        sys.stderr.write("ERROR: ffmpeg not installed.\n")
        sys.exit(1)

def is_valid_youtube_url(url):
    return re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', url.strip()) is not None

def read_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def download_mp3(url, output_dir, quality="320"):
    cmd = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', quality,
        '--output', str(output_dir / '%(title)s.%(ext)s'),
        '--no-playlist',
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python yt2mp3.py <links_file> <output_dir>\n")
        sys.exit(1)

    links_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    check_dependencies()

    urls = read_urls_from_file(links_file)
    urls = [u for u in urls if is_valid_youtube_url(u)]

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Downloading: {url}")
        if not download_mp3(url, output_dir):
            print(f"✗ Failed: {url}")
        else:
            print(f"✓ Done")

if __name__ == "__main__":
    main()
