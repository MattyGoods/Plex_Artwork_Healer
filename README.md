# Plex Artwork Healer

A powerful script that scans your Plex libraries and collections for missing or broken posters and backgrounds, and automatically restores or re-downloads them.

---

## 🔧 Features

* ✅ Detects broken or missing posters and backgrounds
* 📂 Restores from local backup if available
* 🌐 Downloads from TMDb as a fallback (requires API key)
* 📄 Optionally uploads fixed artwork back to Plex
* 📁 Automatically creates folder structure for backups
* 🚜 Supports Movies, TV Shows, and Collections

---

## 📁 Folder Structure

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

---

## ✨ Getting Started

### 1. Install Requirements

```bash
pip install plexapi requests
```

### 2. Set Configuration

Edit the script with your Plex and TMDb info:

```python
PLEX_URL = 'http://your-plex-ip:32400'
PLEX_TOKEN = 'your_plex_token'
TMDB_API_KEY = 'your_tmdb_api_key'
```

Optional config:

* `ENABLE_UPLOAD = True` to enable fixing artwork
* `DRY_RUN = True` to preview actions without uploading

---

## 🛠 Usage

```bash
python plex_artwork_healer.py
```

* First run it with `DRY_RUN = True` to safely test
* Review `artwork_healer.log`
* Then run with `DRY_RUN = False` to apply changes

---

## 📌 Notes

* Only uses official Plex and TMDb APIs
* Does not overwrite existing good artwork
* Can be scheduled via cron or Task Scheduler for auto-healing

---

