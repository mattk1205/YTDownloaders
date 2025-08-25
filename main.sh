#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------
# Parse arguments (only run what is provided)
# ---------------------------------------
SONGS_IN=""
SPOTIFY_IN=""
YTPL_IN=""
LINKS_IN=""
OUTDIR_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --songs)   SONGS_IN="$2"; shift 2 ;;
    --spotify) SPOTIFY_IN="$2"; shift 2 ;;
    --ytpl)    YTPL_IN="$2"; shift 2 ;;
    --links)   LINKS_IN="$2"; shift 2 ;;
    --outdir)  OUTDIR_ARG="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--songs <file>] [--spotify <file>] [--ytplaylist <file>] [--yt_links <file>] [--outdir <dir>]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      echo "Usage: $0 [--songs <file>] [--spotify <file>] [--ytplaylist <file>] [--yt_links <file>] [--outdir <dir>]"
      exit 1
      ;;
  esac
done

if [[ -z "$SONGS_IN" && -z "$SPOTIFY_IN" && -z "$YTPL_IN" && -z "$LINKS_IN" ]]; then
  echo "Nothing to do: provide at least one of --songs / --spotify / --ytpl / --links"
  exit 1
fi

# ---------------------------------------
# Determine run directory
# ---------------------------------------
if [[ -n "$OUTDIR_ARG" ]]; then
  RUN_DIR="$OUTDIR_ARG"
else
  LAST_RUN=$(find . -maxdepth 1 -type d -name "run_*" | sed 's|./run_||' | sort -n | tail -n 1)
  if [[ -z "$LAST_RUN" ]]; then
      RUN_ID=1
  else
      RUN_ID=$((LAST_RUN + 1))
  fi
  RUN_ID_PADDED=$(printf "%03d" "$RUN_ID")
  RUN_DIR="run_${RUN_ID_PADDED}"
fi

mkdir -p "$RUN_DIR/downloads"

# If we generated RUN_ID_PADDED above, keep it for filenames; otherwise derive from folder name.
if [[ -z "${RUN_ID_PADDED:-}" ]]; then
  # Extract numeric suffix or default to 000
  RUN_ID_PADDED=$(printf "%03d" "$(echo "$RUN_DIR" | sed -n 's/.*run_\([0-9]\+\).*/\1/p')")
  [[ -z "$RUN_ID_PADDED" ]] && RUN_ID_PADDED="000"
fi

SONGS_FILE="${RUN_DIR}/songs_${RUN_ID_PADDED}.txt"
LINKS_FILE="${RUN_DIR}/links_${RUN_ID_PADDED}.txt"

echo ">>> Run directory: $RUN_DIR"
: > "$SONGS_FILE"  # create/empty
: > "$LINKS_FILE"  # create/empty

# ---------------------------------------
# Stage 1: seed songs from --songs (if provided)
# ---------------------------------------
if [[ -n "$SONGS_IN" ]]; then
  if [[ -s "$SONGS_IN" ]]; then
    echo ">>> Seeding songs from: $SONGS_IN"
    cat "$SONGS_IN" >> "$SONGS_FILE"
  else
    echo ">>> --songs provided but file is empty: $SONGS_IN"
  fi
fi

# ---------------------------------------
# Stage 2: fetch Spotify playlists -> songs (if provided)
# Note: your scraper prints a 'Playlist <id>:' header and ALSO writes a local songs.txt:contentReference[oaicite:4]{index=4}.
# We capture stdout (filter out headers) and then remove the side-effect file if created.
# ---------------------------------------
if [[ -n "$SPOTIFY_IN" ]]; then
  if [[ -s "$SPOTIFY_IN" ]]; then
    echo ">>> Fetching songs from Spotify playlists: $SPOTIFY_IN"
    # capture stdout, strip lines that start with "Playlist "
    TMP_SPOT=$(mktemp)
    python3 spotify_song_name_playslist_scrape.py "$SPOTIFY_IN" \
      | grep -vE '^Playlist ' >> "$TMP_SPOT" || true
    # append into run songs file
    cat "$TMP_SPOT" >> "$SONGS_FILE"
    rm -f "$TMP_SPOT"
    # clean up side-effect file if the script created one in CWD
    [[ -f "songs.txt" ]] && rm -f "songs.txt"
  else
    echo ">>> --spotify provided but file is empty: $SPOTIFY_IN"
  fi
fi

# De-dup songs (if any)
if [[ -s "$SONGS_FILE" ]]; then
  sort -u "$SONGS_FILE" -o "$SONGS_FILE"
  echo ">>> Songs prepared: $(wc -l < "$SONGS_FILE") unique entries"
fi

# ---------------------------------------
# Stage 3: song names -> YouTube links via ytsearch.sh (if we have songs)
# ---------------------------------------
if [[ -s "$SONGS_FILE" ]]; then
  echo ">>> Searching YouTube for songs (ytsearch.sh)..."
  # ytsearch.sh prints URLs to stdout:contentReference[oaicite:5]{index=5}
  bash ytsearch.sh "$SONGS_FILE" >> "$LINKS_FILE"
fi

# ---------------------------------------
# Stage 4: YouTube playlist URLs -> video links (if provided)
# ---------------------------------------
if [[ -n "$YTPL_IN" ]]; then
  if [[ -s "$YTPL_IN" ]]; then
    echo ">>> Extracting YouTube playlist items from: $YTPL_IN"
    # grabplaylistitems.py prints URLs to stdout:contentReference[oaicite:6]{index=6}
    python3 grabplaylistitems.py "$YTPL_IN" >> "$LINKS_FILE"
  else
    echo ">>> --ytpl provided but file is empty: $YTPL_IN"
  fi
fi

# ---------------------------------------
# Stage 5: direct YouTube links (if provided)
# ---------------------------------------
if [[ -n "$LINKS_IN" ]]; then
  if [[ -s "$LINKS_IN" ]]; then
    echo ">>> Adding direct YouTube links from: $LINKS_IN"
    cat "$LINKS_IN" >> "$LINKS_FILE"
  else
    echo ">>> --links provided but file is empty: $LINKS_IN"
  fi
fi

# De-dup links (if any)
if [[ -s "$LINKS_FILE" ]]; then
  sort -u "$LINKS_FILE" -o "$LINKS_FILE"
  echo ">>> Links prepared: $(wc -l < "$LINKS_FILE") unique URLs"
else
  echo ">>> No links to download. Exiting."
  exit 0
fi

# ---------------------------------------
# Stage 6: download MP3s (320kbps) to run/downloads
# ---------------------------------------
echo ">>> Downloading MP3s to: $RUN_DIR/downloads"
python3 yt2mp3.py "$LINKS_FILE" "$RUN_DIR/downloads"

echo ">>> Done."
