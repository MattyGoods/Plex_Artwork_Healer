# 🖼️ Plex Artwork Healer

A powerful self-healing script for Plex that ensures your Movies, TV Shows, and Collections never appear with broken or missing posters or backgrounds.

---

## ❓ Why I Created This Script

Many users experience missing posters or backgrounds in Plex — either due to agent failures, server restarts, or cache corruption. This script was designed to **automatically detect broken or missing artwork**, try restoring it from **local backups**, and if needed, **fetch replacements from TMDb**. It can even **re-upload** these images to Plex — completely unattended.

---

## ✅ Features

- 🧠 Detects broken or missing posters and backgrounds
- 💾 Restores from local backup if available (`Posters/...`)
- 🌍 Downloads from TMDb (requires free API key)
- 🔁 Optionally re-uploads posters/backgrounds to Plex
- 🗂️ Automatically creates folders for missing backup files
- 🎬 Supports Movies, TV Shows, and Collections
- 📝 Dry-run support with detailed logging

---

## 📁 Folder Structure

Expected structure for backups:

```bash
Posters/
├── Movies/
│   └── Gladiator/
│       ├── poster.jpg
│       └── background.jpg
└── TV Shows/
    └── The Office/
        ├── poster.jpg
        └── background.jpg
```

If artwork is missing in Plex and a local backup exists, it will be restored from this structure.

---

## ⚙️ Requirements

- Python 3.x
- [`plexapi`](https://pypi.org/project/plexapi/)
- [`requests`](https://pypi.org/project/requests/)

Install via pip:

```bash
pip install plexapi requests
```

---

## 🔑 TMDb API Key

To fetch posters and backdrops from TMDb:

1. Visit: https://www.themoviedb.org/settings/api
2. Create a (free) TMDb account if needed
3. Generate a **Developer API Key** (v3)
4. Use it in the config section of the script

---

## 🔧 Configuration

Edit `plex_artwork_healer.py`:

```python
PLEX_URL = 'http://your-plex-ip:32400'
PLEX_TOKEN = 'your_plex_token'
TMDB_API_KEY = 'your_tmdb_api_key'
```

Optional flags:

```python
ENABLE_UPLOAD = True   # Enables uploading images to Plex
DRY_RUN = True         # Preview changes without making edits
```

---

## ▶️ Usage

Run the script:

```bash
python plex_artwork_healer.py
```

🟢 Start with `DRY_RUN = True`  
🟢 Inspect `artwork_healer.log`  
🟢 When confident, set `DRY_RUN = False` to apply

---

## 🗒️ Tips & Notes

- Only affects items with broken or missing artwork
- Will not overwrite working posters or backdrops
- Local backups take priority over TMDb
- Can be run on a schedule (e.g., via cron or Task Scheduler)

---

## 📂 Logging

All actions are logged to:

```
artwork_healer.log
```

This includes:
- Items scanned
- Posters restored or skipped
- TMDb lookups
- Uploads to Plex

---

## ⚠️ Disclaimer

Use at your own risk. Always review logs before enabling upload mode.  
Not affiliated with Plex, TMDb, or any third-party services.

