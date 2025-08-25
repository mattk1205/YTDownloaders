#!/usr/bin/env bash
SONG_FILE="$1"

if [ -z "$SONG_FILE" ] || [ ! -f "$SONG_FILE" ]; then
    echo "Usage: ytsearch.sh <songs_file>"
    exit 1
fi

while IFS= read -r song; do
    if [ -n "$song" ]; then
        yt-dlp "ytsearch1:${song}" --get-id | while read -r id; do
            echo "https://youtube.com/watch?v=${id}"
        done
    fi
done < "$SONG_FILE"
