# spotify_playlist_export.py
# Fetch all track names from a (public) Spotify playlist using Client Credentials flow
# Notes:
# - Works for PUBLIC playlists only. Private or collaborative playlists require OAuth with user login.
# - No redirect URI needed because we use the Client Credentials flow (no user context).
#
import os
import sys  
import time
import base64
import requests
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv  # optional, used if present
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed, we'll just read env vars directly
    pass

TOKEN_URL = "https://accounts.spotify.com/api/token"
PLAYLIST_ITEMS_URL = "https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

def get_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        print(f"ERROR: Environment variable {name} is not set.", file=sys.stderr)
        sys.exit(1)
    return val

def get_client_credentials_token(client_id: str, client_secret: str) -> str:
    # Construct Basic Authorization header
    auth_str = f"{client_id}:{client_secret}".encode("utf-8")
    b64 = base64.b64encode(auth_str).decode("utf-8")
    headers = {"Authorization": f"Basic {b64}"}
    data = {"grant_type": "client_credentials"}

    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"Failed to get token ({r.status_code}): {r.text}")
    return r.json()["access_token"]

def extract_playlist_id(playlist_url_or_id: str) -> str:
    # Accept raw ID or a Spotify URL. Return the playlist ID.
    text = playlist_url_or_id.strip()
    if "/" not in text and ":" not in text:
        return text  # looks like an ID
    # Handle open.spotify.com or spotify:playlist:ID
    if text.startswith("spotify:playlist:"):
        return text.split(":")[-1]
    parsed = urlparse(text)
    if parsed.netloc.endswith("open.spotify.com"):
        # path like /playlist/<ID>
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "playlist":
            return parts[1]
    raise ValueError("Could not determine playlist ID from input. Provide a valid playlist URL or ID.")

def fetch_playlist_track_names(access_token: str, playlist_id: str, market: str | None = None) -> list[str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "limit": 100,  # max per Spotify API
    }
    if market:
        params["market"] = market  # optional: influences availability
    url = PLAYLIST_ITEMS_URL.format(playlist_id=playlist_id)

    names: list[str] = []
    next_url = url
    while next_url:
        r = requests.get(next_url, headers=headers, params=params if next_url == url else None, timeout=30)
        if r.status_code == 429:
            # Rate limited; wait per Retry-After
            retry_after = int(r.headers.get("Retry-After", "1"))
            time.sleep(retry_after)
            continue
        if r.status_code != 200:
            raise SystemExit(f"Failed to fetch playlist items ({r.status_code}): {r.text}")
        payload = r.json()
        items = payload.get("items", [])
        for item in items:
            track = item.get("track")
            if not track:
                continue
            # Filter only music tracks (type could be 'track' or 'episode'); we want track names
            if track.get("type") == "track" and track.get("name"):
                names.append(track["name"])
        next_url = payload.get("next")
    return names

def main():
    if len(sys.argv) < 2:
        print("Usage: python spotify_playlist_export.py <playlist_url_or_id|file> [market]", file=sys.stderr)
        sys.exit(2)

    input_arg = sys.argv[1]
    market = sys.argv[2] if len(sys.argv) >= 3 else None

    client_id = get_env("SPOTIFY_CLIENT_ID")
    client_secret = get_env("SPOTIFY_CLIENT_SECRET")
    token = get_client_credentials_token(client_id, client_secret)

    # Check if input_arg is a file
    if os.path.isfile(input_arg):
        with open(input_arg, "r", encoding="utf-8") as f:
            playlist_inputs = [line.strip() for line in f if line.strip()]
    else:
        playlist_inputs = [input_arg]

    for playlist_input in playlist_inputs:
        try:
            playlist_id = extract_playlist_id(playlist_input)
            names = fetch_playlist_track_names(token, playlist_id, market=market)

            # Print and save results
            print(f"\nPlaylist {playlist_id}:")
            for name in names:
                print(name)

            out_name = f"songs.txt"
            with open(out_name, "a", encoding="utf-8") as f:
                for name in names:
                    f.write(name + "\n")
            print(f"Saved {len(names)} track names to {out_name}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {playlist_input}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
