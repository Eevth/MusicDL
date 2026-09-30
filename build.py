"""
Build Script - Bikin .exe pakai PyInstaller
Jalankan: python build.py
"""

import os
import subprocess
import sys
from music_downloader.config import APP_NAME, APP_VERSION


def build():
    print(f"Building {APP_NAME} v{APP_VERSION}...")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", f"{APP_NAME}_v{APP_VERSION}",
        "--add-data", "music_downloader;music_downloader",
        "--add-data", "bin;bin",
        "main.py",
    ]

    icon_path = os.path.join("music_downloader", "assets", "icon.ico")
    if os.path.exists(icon_path):
        cmd.insert(-1, "--icon")
        cmd.insert(-1, icon_path)

    print("Running:", " ".join(cmd))
    print()

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{APP_NAME}_v{APP_VERSION}.exe")
        print()
        print("=" * 50)
        print("Build berhasil!")
        print("File:", exe_path)
        print("Upload file ini ke GitHub Releases sebagai v" + APP_VERSION)
    else:
        print()
        print("Build gagal!")
        sys.exit(1)


if __name__ == "__main__":
    build()
