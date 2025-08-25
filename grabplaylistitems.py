#!/usr/bin/env python3
"""
Extract all video URLs from multiple YouTube playlists (list in file)
"""

import subprocess
import sys
import os

def check_yt_dlp():
    """Check if yt-dlp is installed."""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("yt-dlp not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], check=True)

def extract_playlist_urls(playlist_url):
    """Extract all video URLs from a YouTube playlist."""
    try:
        cmd = [
            'yt-dlp', 
            '--flat-playlist',
            '--print', 'url',
            playlist_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        urls = [url.strip() for url in result.stdout.strip().split('\n') if url.strip()]
        return urls
    except subprocess.CalledProcessError as e:
        print(f"Error extracting playlist: {e.stderr}")
        return []

def main():
    print("YouTube Playlist URL Extractor")
    print("=" * 40)

    if len(sys.argv) < 2:
        print("Usage: python grabplaylistitems.py <playlist_urls_file>")
        sys.exit(1)

    playlist_file = sys.argv[1]
    if not os.path.isfile(playlist_file):
        print(f"File not found: {playlist_file}")
        sys.exit(1)

    check_yt_dlp()

    all_urls = []
    with open(playlist_file, 'r', encoding='utf-8') as f:
        playlists = [line.strip() for line in f if line.strip()]

    for playlist_url in playlists:
        print(f"\nExtracting URLs from: {playlist_url}")
        urls = extract_playlist_urls(playlist_url)
        if not urls:
            print("  No URLs found or error occurred.")
            continue

        print(f"  Found {len(urls)} videos:")
        for i, url in enumerate(urls, 1):
            print(f"    {i:2d}. {url}")
        all_urls.extend(urls)

    if all_urls:
        filename = "playlist_urls.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            for url in all_urls:
                f.write(url + '\n')
        print(f"\nAll URLs saved to: {filename}")
    else:
        print("\nNo videos extracted from any playlist.")

if __name__ == "__main__":
    main()
