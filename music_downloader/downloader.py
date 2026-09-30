"""
Downloader Module - Engine download musik MP3 & MP4 pakai yt-dlp
"""

import os
import sys
import threading
import yt_dlp


def get_ffmpeg_dir():
    """Cari folder ffmpeg: di folder project, di samping exe, subfolder bin, atau default PATH."""
    possible_dirs = []

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        possible_dirs.append(exe_dir)
        possible_dirs.append(os.path.join(exe_dir, "bin"))
        if hasattr(sys, '_MEIPASS'):
            possible_dirs.append(sys._MEIPASS)
            possible_dirs.append(os.path.join(sys._MEIPASS, "bin"))

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_dirs.append(root_dir)
    possible_dirs.append(os.path.join(root_dir, "bin"))
    possible_dirs.append(os.getcwd())
    possible_dirs.append(os.path.join(os.getcwd(), "bin"))

    for d in possible_dirs:
        if os.path.exists(os.path.join(d, "ffmpeg.exe")) or os.path.exists(os.path.join(d, "ffmpeg")):
            return d

    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return os.path.dirname(exe)
    except Exception:
        pass

    return None


class DownloadResult:
    def __init__(self, success, title="", filepath="", error=""):
        self.success = success
        self.title = title
        self.filepath = filepath
        self.error = error


class CancelToken:
    """Per-download cancel token agar cancel 1 download gak affect yang lain."""
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class MusicDownloader:
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(os.path.expanduser("~"), "Music", "MusicDL")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_dir = get_ffmpeg_dir()
        self._active_tokens = []

    def cancel_all(self):
        for token in self._active_tokens:
            token.cancel()

    def _progress_hook(self, d, callback=None, cancel_token=None):
        if cancel_token and cancel_token.cancelled:
            raise Exception("Download dibatalkan")

        if callback is None:
            return

        status = d.get('status', '')

        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            progress = (downloaded / total) if total > 0 else 0
            speed_str = f"{speed / (1024*1024):.1f} MB/s" if speed else "-- MB/s"
            eta_str = f"{eta}s" if eta else "--"

            callback(
                "downloading",
                progress,
                f"⬇️ {progress*100:.1f}% | {speed_str} | ETA: {eta_str}"
            )

        elif status == 'finished':
            callback("converting", 0.95, "🔄 Mengkonversi file...")

        elif status == 'error':
            callback("error", 0, "❌ Error saat download")

    def search(self, query, max_results=10):
        """Search video/musik dari YouTube."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{max_results}',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(query, download=False)

                if 'entries' in result:
                    entries = []
                    for entry in result['entries']:
                        if entry:
                            entries.append({
                                'id': entry.get('id', ''),
                                'title': entry.get('title', 'Unknown'),
                                'url': entry.get('url', '') or f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                                'duration': entry.get('duration', 0),
                                'channel': entry.get('channel', '') or entry.get('uploader', 'Unknown'),
                                'thumbnail': entry.get('thumbnail', ''),
                            })
                    return entries
                return []

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def download_mp3(self, url, callback=None):
        """Download sebagai MP3 (audio only)."""
        cancel_token = CancelToken()
        self._active_tokens.append(cancel_token)

        def _worker():
            try:
                if callback:
                    callback("starting", 0, "🎵 Memulai download MP3...")

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }],
                    'progress_hooks': [lambda d: self._progress_hook(d, callback, cancel_token)],
                    'quiet': True,
                    'no_warnings': True,
                }
                if self.ffmpeg_dir:
                    ydl_opts['ffmpeg_location'] = self.ffmpeg_dir

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown')
                    filepath = os.path.join(self.output_dir, f"{title}.mp3")

                    if callback:
                        callback("done", 1.0, f"✅ Selesai: {title}.mp3")

                    return DownloadResult(True, title, filepath)

            except Exception as e:
                error_msg = str(e)
                if callback:
                    callback("error", 0, f"❌ Error: {error_msg}")
                return DownloadResult(False, error=error_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def download_mp4(self, url, quality="best", callback=None):
        """Download sebagai MP4 (video + audio)."""
        cancel_token = CancelToken()
        self._active_tokens.append(cancel_token)

        quality_map = {
            "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "best":  "bestvideo+bestaudio/best",
        }

        fmt = quality_map.get(quality, quality_map["best"])

        def _worker():
            try:
                if callback:
                    callback("starting", 0, "🎬 Memulai download MP4...")

                ydl_opts = {
                    'format': fmt,
                    'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                    'merge_output_format': 'mp4',
                    'progress_hooks': [lambda d: self._progress_hook(d, callback, cancel_token)],
                    'quiet': True,
                    'no_warnings': True,
                }
                if self.ffmpeg_dir:
                    ydl_opts['ffmpeg_location'] = self.ffmpeg_dir

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown')
                    filepath = os.path.join(self.output_dir, f"{title}.mp4")

                    if callback:
                        callback("done", 1.0, f"✅ Selesai: {title}.mp4")

                    return DownloadResult(True, title, filepath)

            except Exception as e:
                error_msg = str(e)
                if callback:
                    callback("error", 0, f"❌ Error: {error_msg}")
                return DownloadResult(False, error=error_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def get_info(self, url):
        """Ambil info video tanpa download."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'channel': info.get('channel', '') or info.get('uploader', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url,
                    'formats': [
                        f"{f.get('format_note', '')} - {f.get('ext', '')}"
                        for f in info.get('formats', [])
                        if f.get('format_note')
                    ]
                }
        except Exception as e:
            return None
