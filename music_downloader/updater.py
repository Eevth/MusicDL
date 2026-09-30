"""
Updater Module - Sistem auto-update dari GitHub Releases
Cek versi terbaru, download, dan install otomatis.
GitHub belum diisi? App tetap jalan, tombol update cuma kasih info.
"""

import os
import sys
import subprocess
import threading
import requests
from packaging import version
from music_downloader.config import APP_VERSION, APP_NAME, get_update_url
from music_downloader.settings_store import load_settings


class Updater:
    def __init__(self, callback=None):
        """
        callback: function(status: str, progress: float|None)
            - status: pesan status update
            - progress: 0.0 - 1.0 atau None
        """
        self.callback = callback
        self.latest_version = None
        self.download_url = None
        self.release_notes = ""

    def _notify(self, status, progress=None):
        if self.callback:
            self.callback(status, progress)

    def _resolve_update_url(self):
        settings = load_settings()
        owner = (settings.get("github_owner") or "").strip()
        repo = (settings.get("github_repo") or "").strip()
        return get_update_url(owner, repo)

    def check_for_updates(self):
        """Cek apakah ada versi baru di GitHub Releases."""
        update_url = self._resolve_update_url()
        if not update_url:
            self._notify("ℹ️ GitHub belum di-set. Isi di Pengaturan.", None)
            return False

        try:
            self._notify("🔍 Mengecek update...", None)
            response = requests.get(update_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.latest_version = data.get("tag_name", "").lstrip("v")
                self.release_notes = data.get("body", "Tidak ada catatan rilis.") or "Tidak ada catatan rilis."

                assets = data.get("assets", [])
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        self.download_url = asset["browser_download_url"]
                        break

                if self.latest_version and version.parse(self.latest_version) > version.parse(APP_VERSION):
                    self._notify(
                        f"✅ Update tersedia! v{APP_VERSION} → v{self.latest_version}",
                        None
                    )
                    return True
                else:
                    self._notify(f"👍 Sudah versi terbaru (v{APP_VERSION})", None)
                    return False
            elif response.status_code == 404:
                self._notify("⚠️ Repo/release belum ada di GitHub", None)
                return False
            else:
                self._notify(f"⚠️ Gagal cek update (HTTP {response.status_code})", None)
                return False

        except requests.exceptions.ConnectionError:
            self._notify("❌ Tidak ada koneksi internet", None)
            return False
        except Exception as e:
            self._notify(f"❌ Error: {str(e)}", None)
            return False

    def download_update(self):
        """Download file update dari GitHub Releases."""
        if not self.download_url:
            self._notify("❌ Tidak ada URL download", None)
            return None

        try:
            self._notify("📥 Mendownload update...", 0.0)
            response = requests.get(self.download_url, stream=True, timeout=60)
            total_size = int(response.headers.get('content-length', 0))

            update_dir = os.path.join(os.path.expanduser("~"), ".musicdl_updates")
            os.makedirs(update_dir, exist_ok=True)

            filename = os.path.basename(self.download_url.split("?")[0]) or f"{APP_NAME}_update.exe"
            filepath = os.path.join(update_dir, filename)

            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = downloaded / total_size
                            mb_done = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            self._notify(
                                f"📥 Downloading... {mb_done:.1f}/{mb_total:.1f} MB",
                                progress
                            )

            self._notify("✅ Download selesai!", 1.0)
            return filepath

        except Exception as e:
            self._notify(f"❌ Gagal download: {str(e)}", None)
            return None

    def install_update(self, filepath):
        """Jalankan installer update dan tutup app lama."""
        if filepath and os.path.exists(filepath):
            self._notify("🔄 Menginstall update... App akan restart.", None)
            subprocess.Popen([filepath], shell=True)
            sys.exit(0)

    def check_and_update(self):
        """Full flow: cek → download → install (jalankan di thread)."""
        def _worker():
            has_update = self.check_for_updates()
            if has_update:
                filepath = self.download_update()
                if filepath:
                    self.install_update(filepath)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
