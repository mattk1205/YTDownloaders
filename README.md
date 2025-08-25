# **YouTube / Spotify Playlist to MP3 Pipeline**

## **Overview**

This project automates the process of:

1. **Fetching track names from Spotify playlists**
2. **Searching YouTube for those track names**
3. **Extracting all videos from YouTube playlists**
4. **Combining all YouTube video URLs**
5. **Downloading them as high-quality MP3 files**

Each run creates a self-contained `run_XXX` directory with:

```
songs_XXX.txt   # All song names for that run
links_XXX.txt   # All YouTube URLs for that run
downloads/      # All downloaded MP3 files
```

---

## **Requirements**

* **Python 3.7+**
* **yt-dlp**
* **ffmpeg**
* **Spotify API credentials** (for Spotify playlist scraping)

Install dependencies:

```bash
pip install requests python-dotenv yt-dlp
# Install ffmpeg
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt install ffmpeg

```

---

## **Setup**

### **0. Clone Repo**

```bash
git clone [git@github.com:mattk1205/YTDownloaders.git](https://github.com/mattk1205/YTDownloaders.git)
cd YTDownloaders/
chmod +x main.sh
```
### **1. Spotify API Credentials**

Create a `.env` file (or export as environment variables):

```bash
export SPOTIFY_CLIENT_ID="your_spotify_client_id"
export SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
```

Your Spotify playlists **must be public**.

---

### **2. Input Files**

Place these files in the project root:

#### **`songs.txt`**

* Optional starting list of songs (one per line).
* May be empty if you only want to use playlists.

#### **`spotify_playlist_urls.txt`**

* List of Spotify playlist URLs or IDs (one per line).
* Example:

```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
https://open.spotify.com/playlist/5ABHKGoOzxkaa28ttQV9sE
```

#### **`youtube_playlist_urls.txt`**

* List of YouTube playlist URLs or IDs (one per line).
* Example:

```
https://www.youtube.com/playlist?list=PLynG1FzLd8nFhS9W
https://youtube.com/playlist?list=PLynG1FzLd8nFhS9X
```

---

#### **`my_links.txt`**

* Optional starting list of YouTube links (one per line).
* May be empty if you only want to use YouTube search or playlist extraction.
* To use this file directly, you must explicitly bypass link generation — see [**Running the Script**](#running-the-script) for the `--links-file` option.

---

## **How It Works**

The main orchestrator is **`main.sh`**.

It performs the following steps:

1. **Copies `songs.txt`** → `songs_XXX.txt` in the new run folder.
2. **Appends Spotify playlist track names** from `spotify_playlist_urls.txt`.
3. **Removes duplicate songs**.
4. **Searches YouTube** for each song (`ytsearch.sh`).
5. **Extracts YouTube playlist videos** from `youtube_playlist_urls.txt` (`grabplaylistitems.py`).
6. **Combines all links**, removes duplicates.
7. **Downloads MP3s** at 320 kbps (`yt2mp3.py`).

---

---

## Running the Script

```bash
./main.sh [--songs <file>] [--spotify <file>] [--ytpl <file>] [--links <file>] [--outdir <dir>]
````

Provide any combination:

* `--songs`   : song names (one per line) → searched on YouTube
* `--spotify` : Spotify playlist URLs (one per line) → expanded to song names
* `--ytpl`    : YouTube playlist URLs (one per line) → expanded to video links
* `--links`   : direct YouTube video URLs (one per line) → used as-is
* `--outdir`  : custom output directory (otherwise `run_XXX/` is created)

**Examples**

* Only existing YouTube links:

```bash
./main.sh --links my_links.txt
```

* Only YouTube playlists:

```bash
./main.sh --ytpl youtube_playlist_urls.txt
```

* Songs + Spotify + Playlists (full build):

```bash
./main.sh --songs songs.txt --spotify spotify_playlist_urls.txt --ytpl youtube_playlist_urls.txt
```

The script will only run the stages for which you supplied files. It de-duplicates songs and links and saves results in a numbered `run_XXX/` (unless you specify `--outdir`).

```bash
./main.sh
```

This will:

* Detect the next run number.
* Create a `run_XXX` directory.
* Process all inputs and download MP3s automatically.

---

## **Notes**

* **High quality**: All MP3s are downloaded at 320 kbps.
* **No overwrites**: Every run is stored in a new folder.
* **Deduplication**: Duplicate songs and YouTube links are removed before processing.
* **Cross-platform**: Works on Linux, macOS, and Windows (WSL recommended for Windows users).

---