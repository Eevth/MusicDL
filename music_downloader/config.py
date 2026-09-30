# App Configuration
APP_NAME = "MusicDL"
APP_VERSION = "1.0.0"

# Isi ini NANTI setelah lo bikin repo GitHub.
# Bisa juga diisi dari menu Pengaturan di aplikasi.
# Contoh: GITHUB_OWNER = "namauser"
#         GITHUB_REPO  = "music-downloader"
GITHUB_OWNER = "Eevth"
GITHUB_REPO = "MusicDL"


def get_update_url(owner=None, repo=None):
    owner = owner or GITHUB_OWNER
    repo = repo or GITHUB_REPO
    if not owner or not repo:
        return ""
    return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"


UPDATE_URL = get_update_url()
