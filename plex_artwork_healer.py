# === IMPORTS ===
import os
import re
import time
import csv
import datetime
import requests
from plexapi.server import PlexServer
from tmdbv3api import TMDb, Movie

# === CONFIGURATION ===
PLEX_URL = 'http://<PLEX_IP>:32400'        # Plex server base URL
PLEX_TOKEN = 'PLEX_TOKEN'                  # Plex API token
TMDB_API_KEY = 'TMDB API'                  # TMDb API key

LIBRARIES = ['Movies', 'TV Shows']         # Plex libraries to process
BASE_DIR = 'Posters'                       # Directory to store artwork backups
LOG_FILE = 'artwork_healer.log'            # Output log file
CACHE_FILE = 'tmdb_cache.csv'              # TMDb ID cache CSV file

ENABLE_UPLOAD = True                       # Whether to upload artwork to Plex
FORCE_UPLOAD_ALL = False                   # If True, re-upload even working images
DRY_RUN = False                            # If True, don't make changes
ENABLE_LOG = True                          # If True, write to log file
DELAY = 1                                  # Delay (in seconds) between items

# === TMDb SETUP ===
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
tmdb.language = 'en'
movie_search = Movie()                     # TMDb movie search instance

# === LOGGING UTILITY ===
def log(msg):
    """Prints and logs messages with timestamp"""
    print(msg)
    if ENABLE_LOG:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now()} - {msg}\n")

# === FILE SYSTEM HELPERS ===
def safe_filename(name):
    """Cleans a string to make it a safe filename"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def ensure_folder(path):
    """Creates directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)

def artwork_url_invalid(url):
    """Checks if a given artwork URL is invalid or unreachable"""
    try:
        r = requests.get(url, timeout=5)
        return r.status_code != 200
    except:
        return True

def get_artwork_path(library, title, art_type):
    """Returns full path to the local poster or background image file"""
    return os.path.join(BASE_DIR, library, safe_filename(title), f"{art_type}.jpg")

def extract_tmdb_id_from_guid(guid):
    """Extracts TMDb ID from a Plex GUID string (if available)"""
    match = re.search(r'themoviedb://(\d+)', guid or '')
    return int(match.group(1)) if match else None

# === ARTWORK BACKUP / DOWNLOAD / UPLOAD ===
def backup_from_plex(item, art_type, path):
    """Downloads and saves poster or background from Plex"""
    rel_url = item.thumb if art_type == 'poster' else item.art
    if not rel_url:
        return False
    try:
        url = f"{PLEX_URL}{rel_url}?X-Plex-Token={PLEX_TOKEN}"
        r = requests.get(url)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            log(f"[BACKUP] Saved {art_type} for {item.title} from Plex")
            return True
    except Exception as e:
        log(f"[ERROR] Failed backup for {item.title} ({art_type}): {e}")
    return False

def download_tmdb_art(tmdb_data, art_type, path):
    """Downloads poster or backdrop from TMDb"""
    key = 'poster_path' if art_type == 'poster' else 'backdrop_path'
    art_path = getattr(tmdb_data, key, None)
    if not art_path:
        return False
    url = f"https://image.tmdb.org/t/p/original{art_path}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            log(f"[TMDb] Downloaded {art_type} for {tmdb_data.title}")
            return True
    except Exception as e:
        log(f"[ERROR] Failed TMDb download for {tmdb_data.title} ({art_type}): {e}")
    return False

def upload_to_plex(item, art_type, path):
    """Uploads poster or background to Plex"""
    try:
        if art_type == 'poster':
            item.uploadPoster(filepath=path)
        else:
            item.uploadArt(filepath=path)
        log(f"[UPLOAD] Uploaded {art_type} for {item.title}")
    except Exception as e:
        log(f"[ERROR] Upload failed for {item.title} ({art_type}): {e}")

# === TMDb ID CACHING ===
def build_tmdb_cache(plex):
    """Builds TMDb ID cache from all libraries + movie collections"""
    cache = {}
    log("[CACHE] Generating new TMDb cache...")

    for lib in LIBRARIES:
        try:
            section = plex.library.section(lib)
            for item in section.all():
                guid = getattr(item, 'guid', '')
                tmdb_id = extract_tmdb_id_from_guid(guid)
                if tmdb_id:
                    cache[item.title] = tmdb_id
        except Exception as e:
            log(f"[ERROR] Failed to cache {lib}: {e}")

    # Also try caching Collections under "Movies"
    try:
        movies_section = plex.library.section('Movies')
        for coll in movies_section.collections():
            guid = getattr(coll, 'guid', '')
            tmdb_id = extract_tmdb_id_from_guid(guid)
            if tmdb_id:
                cache[coll.title] = tmdb_id
    except Exception as e:
        log(f"[ERROR] Failed to cache collections: {e}")

    # Write cache to CSV
    with open(CACHE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['title', 'tmdb_id'])
        for title, tmdb_id in cache.items():
            writer.writerow([title, tmdb_id])
    log(f"[CACHE] Saved TMDb ID cache to {CACHE_FILE}")
    return cache

def load_tmdb_cache():
    """Loads TMDb cache from CSV file"""
    cache = {}
    if not os.path.exists(CACHE_FILE):
        return cache
    with open(CACHE_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['title'] and row['tmdb_id'].isdigit():
                cache[row['title']] = int(row['tmdb_id'])
    return cache

# === MAIN FUNCTION TO FIX POSTER OR BACKGROUND ===
def fix_art(item, library, art_type, cache):
    title = item.title
    rel_url = item.thumb if art_type == 'poster' else item.art
    broken = FORCE_UPLOAD_ALL or not rel_url or artwork_url_invalid(f"{PLEX_URL}{rel_url}?X-Plex-Token={PLEX_TOKEN}")
    backup_path = get_artwork_path(library, title, art_type)
    ensure_folder(os.path.dirname(backup_path))

    # Step 1: Backup if not already done
    if not os.path.exists(backup_path):
        backup_from_plex(item, art_type, backup_path)

    # Step 2: Skip if not broken and not forcing
    if not broken:
        log(f"[OK] {title} {art_type} is fine.")
        return

    log(f"[{'FORCE' if FORCE_UPLOAD_ALL else 'FIX'}] Redownloading {art_type} for {title}")

    # Step 3: Restore from local backup
    if os.path.exists(backup_path) and not FORCE_UPLOAD_ALL:
        log(f"[RESTORE] Found local {art_type} for {title}")
        if ENABLE_UPLOAD and not DRY_RUN:
            upload_to_plex(item, art_type, backup_path)
        return

    # Step 4: TMDb Lookup from cache or search
    tmdb_id = cache.get(title)
    tmdb_data = None
    if tmdb_id:
        try:
            tmdb_data = movie_search.details(tmdb_id)
        except Exception as e:
            log(f"[ERROR] TMDb lookup failed for {title} (ID {tmdb_id}): {e}")
    else:
        try:
            results = movie_search.search(title)
            tmdb_data = results[0] if results else None
        except Exception as e:
            log(f"[ERROR] TMDb search failed for {title}: {e}")

    # Step 5: Download and Upload artwork
    if tmdb_data and download_tmdb_art(tmdb_data, art_type, backup_path):
        if ENABLE_UPLOAD and not DRY_RUN:
            upload_to_plex(item, art_type, backup_path)
    else:
        log(f"[MISSING] No {art_type} found for {title}")

def process_section(section, library, cache):
    """Processes all items in a Plex library section"""
    for item in section.all():
        fix_art(item, library, 'poster', cache)
        fix_art(item, library, 'background', cache)
        time.sleep(DELAY)

# === MAIN ENTRY POINT ===
def main():
    if ENABLE_LOG:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("=== Plex Artwork Healer Log ===\n")

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    # Step 1: Generate ID Cache
    cache = build_tmdb_cache(plex)

    # Step 2: Process all libraries
    for lib in LIBRARIES:
        try:
            log(f"\n=== Processing Library: {lib} ===")
            section = plex.library.section(lib)
            process_section(section, lib, cache)
        except Exception as e:
            log(f"[ERROR] Failed processing {lib}: {e}")

if __name__ == '__main__':
    main()
