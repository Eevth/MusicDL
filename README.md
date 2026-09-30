# 🎧 MusicDL - Music Downloader

Aplikasi Windows native untuk download musik MP3 & MP4 dari YouTube.

![MusicDL](https://img.shields.io/badge/MusicDL-v1.0.0-e94560?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=for-the-badge&logo=windows)

## ✨ Fitur

- 🔍 **Search** - Cari lagu langsung dari app
- 🎵 **Download MP3** - Audio only, kualitas 320kbps
- 🎬 **Download MP4** - Video + Audio, pilih kualitas (360p - 1080p)
- 📥 **Direct URL** - Paste URL langsung dari YouTube
- 🔄 **Auto Update** - Sistem update otomatis dari GitHub Releases
- 🌙 **Dark Mode** - UI modern yang enak diliat

## 🚀 Quick Start

### Jalankan dari Source Code

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Jalankan app
python main.py
```

### Build jadi .exe

```bash
# Build executable
python build.py

# Output: dist/MusicDL_v1.0.0.exe
```

## 📦 Sistem Update

Aplikasi ini punya sistem auto-update dari GitHub Releases:

### Cara Release Versi Baru:

1. **Edit versi** di `music_downloader/config.py`:
   ```python
   APP_VERSION = "1.1.0"  # Naikkan versi
   ```

2. **Build** jadi `.exe`:
   ```bash
   python build.py
   ```

3. **Buat GitHub Release** baru:
   - Tag: `v1.1.0`
   - Title: `v1.1.0 - Nama Update`
   - Attach file `.exe` dari folder `dist/`

4. User yang pakai app lama akan otomatis dapat notifikasi update! 🎉

### Setup GitHub

Edit `music_downloader/config.py`:
```python
GITHUB_OWNER = "username-github-lo"
GITHUB_REPO = "nama-repo-lo"
```

## 🛠️ Tech Stack

| Komponen | Library |
|----------|---------|
| UI Framework | CustomTkinter |
| Download Engine | yt-dlp |
| Audio Convert | FFmpeg |
| Auto Update | GitHub API + Requests |
| Build Tool | PyInstaller |

## ⚠️ Prerequisite

- **FFmpeg** harus terinstall dan ada di PATH
  - Download: https://ffmpeg.org/download.html
  - Atau install via: `winget install FFmpeg`

## 📁 Struktur Project

```
music-downloader/
├── main.py                      # Entry point
├── build.py                     # Build script (.exe)
├── requirements.txt             # Dependencies
├── README.md
└── music_downloader/
    ├── __init__.py
    ├── config.py                # App config & versioning
    ├── app.py                   # Main UI application
    ├── downloader.py            # Download engine (yt-dlp)
    ├── updater.py               # Auto-update system
    └── assets/
        └── icon.ico             # App icon (optional)
```

## 📝 License

MIT License - Bebas dipakai dan dimodifikasi.
