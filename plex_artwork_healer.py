import os
import requests
import datetime
import time
import re
from plexapi.server import PlexServer

# === Configuration ===
PLEX_URL = 'http://localhost:32400'                 # Your Plex server URL or IP
PLEX_TOKEN = 'YOUR_PLEX_TOKEN_HERE'                 # Your Plex authentication token
TMDB_API_KEY = 'YOUR_TMDB_API_KEY_HERE'             # TMDb API key
LIBRARIES = ['Movies', 'TV Shows']                  # Plex library names to process
BASE_DIR = 'Posters'                                # Local folder to store or load backup images
ENABLE_UPLOAD = False                               # If True, script will upload fixed artwork to Plex
DRY_RUN = False                                     # If True, simulate actions without performing them
ENABLE_LOG = True                                   # Enable logging to file
LOG_FILE = 'artwork_healer.log'                     # Log file name
DELAY = 1                                           # Delay between operations (in seconds)
TMDB_LANG = 'en-US'                                 # Language used when querying TMDb

HEADERS = {"Accept": "application/json"}            # Common headers for TMDb API calls

# --- Utility Functions ---

def log(message):
    """Log a message to the console and optionally to a file."""
    print(message)
    if ENABLE_LOG:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now()} - {message}\n")

def safe_filename(name):
    """Sanitize a filename to remove characters invalid for file/folder names."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def check_poster_url(poster_url):
    """Check if the provided Plex artwork URL is broken (e.g. 404 or timeout)."""
    try:
        r = requests.get(poster_url, timeout=5)
        return r.status_code != 200
    except:
        return True

def restore_from_backup(library_name, title, art_type):
    """Check if a local backup of the poster or background exists and return its path if found."""
    file_name = f"{art_type}.jpg"
    item_dir = os.path.join(BASE_DIR, library_name, safe_filename(title))
    backup_path = os.path.join(item_dir, file_name)
    return backup_path if os.path.exists(backup_path) else None

def search_tmdb(title, content_type):
    """Search TMDb for the given title (either 'movie' or 'tv') and return the first result."""
    try:
        search_type = 'movie' if content_type == 'movie' else 'tv'
        url = f"https://api.themoviedb.org/3/search/{search_type}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': TMDB_LANG,
            'query': title
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        return data['results'][0] if data.get('results') else None
    except Exception as e:
        log(f"[TMDb] Search failed for {title}: {e}")
        return None

def download_tmdb_image(tmdb_data, art_type):
    """Download a poster or backdrop image from TMDb and return it as binary data."""
    try:
        key = 'poster_path' if art_type == 'poster' else 'backdrop_path'
        if not tmdb_data.get(key):
            return None
        image_url = f"https://image.tmdb.org/t/p/original{tmdb_data[key]}"
        r = requests.get(image_url, timeout=10)
        return r.content if r.status_code == 200 else None
    except Exception as e:
        log(f"[TMDb] Failed to download {art_type}: {e}")
        return None

# --- Core Logic ---

def fix_art(item, title, library_name, art_type, tmdb_type=None):
    """
    Attempt to fix missing/broken artwork for an item by:
    1. Checking Plex for broken poster/art.
    2. Trying to restore from local backup.
    3. Falling back to TMDb to redownload.
    4. Optionally uploading the image to Plex.
    """
    try:
        item_dir = os.path.join(BASE_DIR, library_name, safe_filename(title))
        os.makedirs(item_dir, exist_ok=True)

        # Determine the correct artwork field
        rel_url = getattr(item, 'thumb' if art_type == 'poster' else 'art', None)
        is_broken = not rel_url or check_poster_url(f"{PLEX_URL}{rel_url}?X-Plex-Token={PLEX_TOKEN}")

        if not is_broken:
            log(f"[OK] {title} {art_type} is fine.")
            return

        log(f"[FIX] {title} missing/broken {art_type}")

        # Step 1: Try restoring from local backup
        backup_path = restore_from_backup(library_name, title, art_type)
        if backup_path:
            log(f"[RESTORE] Using backup {backup_path}")
            if ENABLE_UPLOAD and not DRY_RUN:
                with open(backup_path, 'rb') as f:
                    item.uploadPoster(f) if art_type == 'poster' else item.uploadArt(f)
            return

        # Step 2: Try downloading from TMDb
        if tmdb_type:
            tmdb_data = search_tmdb(title, tmdb_type)
            if tmdb_data:
                img = download_tmdb_image(tmdb_data, art_type)
                if img:
                    log(f"[TMDb] Downloaded {art_type} for {title} from TMDb")
                    if ENABLE_UPLOAD and not DRY_RUN:
                        from io import BytesIO
                        stream = BytesIO(img)
                        item.uploadPoster(stream) if art_type == 'poster' else item.uploadArt(stream)
                    return

        # If all fails
        log(f"[MISSING] No {art_type} available for {title}")
    except Exception as e:
        log(f"[ERROR] {title} {art_type}: {e}")

def process_items(library_name, items, tmdb_type=None):
    """Iterate over Plex items and run fix_art for both poster and background."""
    for item in items:
        title = item.title
        fix_art(item, title, library_name, 'poster', tmdb_type)
        fix_art(item, title, library_name, 'background', tmdb_type)
        time.sleep(DELAY)

def main():
    """Main script execution."""
    if ENABLE_LOG:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("=== Plex Artwork Healer Log ===\n")

    # Connect to Plex server
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    # Process all specified libraries
    for library_name in LIBRARIES:
        try:
            section = plex.library.section(library_name)
            content_type = 'movie' if section.type == 'movie' else 'tv'
            log(f"\n=== Processing {library_name} ===")
            process_items(library_name, section.all(), content_type)
        except Exception as e:
            log(f"[ERROR] Failed library {library_name}: {e}")

    # Process collections in each library
    try:
        log(f"\n=== Processing Collections ===")
        for library_name in LIBRARIES:
            section = plex.library.section(library_name)
            collections = section.collections()
            process_items(library_name, collections)
    except Exception as e:
        log(f"[ERROR] Failed to process collections: {e}")

# --- Entry point ---
if __name__ == '__main__':
    main()
