"""
MusicDL - Main Application UI
Native Windows app pakai CustomTkinter (dark mode, modern UI)
"""

import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import requests
from io import BytesIO

from music_downloader.config import APP_NAME, APP_VERSION
from music_downloader.downloader import MusicDownloader
from music_downloader.updater import Updater
from music_downloader.settings_store import load_settings, save_settings


# ── Theme Setup ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Colors ───────────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":      "#0f0f0f",
    "bg_card":      "#1a1a2e",
    "bg_card2":     "#16213e",
    "accent":       "#e94560",
    "accent_hover": "#c81e45",
    "accent2":      "#0f3460",
    "text":         "#ffffff",
    "text_dim":     "#8b8b8b",
    "success":      "#00c853",
    "warning":      "#ff9800",
    "error":        "#f44336",
    "mp3":          "#1db954",
    "mp4":          "#ff4757",
    "border":       "#2a2a3e",
}


class SearchResultCard(ctk.CTkFrame):
    """Card untuk setiap hasil pencarian."""

    def __init__(self, parent, data, on_download_mp3, on_download_mp4, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)
        self.data = data

        # ── Layout ───────────────────────────────
        self.grid_columnconfigure(1, weight=1)

        # Thumbnail placeholder
        thumb_frame = ctk.CTkFrame(self, width=120, height=68, fg_color=COLORS["bg_card2"], corner_radius=8)
        thumb_frame.grid(row=0, column=0, rowspan=3, padx=(12, 8), pady=12, sticky="ns")
        thumb_frame.grid_propagate(False)

        thumb_label = ctk.CTkLabel(thumb_frame, text="🎵", font=("Segoe UI Emoji", 28))
        thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        # Load thumbnail async
        if data.get('thumbnail'):
            self._load_thumbnail(thumb_frame, data['thumbnail'])

        # Title
        title = data.get('title', 'Unknown')
        if len(title) > 65:
            title = title[:62] + "..."
        title_label = ctk.CTkLabel(
            self, text=title,
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"],
            anchor="w"
        )
        title_label.grid(row=0, column=1, padx=8, pady=(12, 0), sticky="sw")

        # Channel & Duration
        duration = data.get('duration', 0)
        dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else "--:--"
        channel = data.get('channel', 'Unknown')

        info_label = ctk.CTkLabel(
            self, text=f"👤 {channel}  •  ⏱️ {dur_str}",
            font=("Segoe UI", 11), text_color=COLORS["text_dim"],
            anchor="w"
        )
        info_label.grid(row=1, column=1, padx=8, pady=0, sticky="nw")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=1, padx=8, pady=(4, 12), sticky="sw")

        mp3_btn = ctk.CTkButton(
            btn_frame, text="⬇ MP3", width=90, height=30,
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["mp3"], hover_color="#17a34a",
            corner_radius=8,
            command=lambda: on_download_mp3(data)
        )
        mp3_btn.pack(side="left", padx=(0, 8))

        mp4_btn = ctk.CTkButton(
            btn_frame, text="⬇ MP4", width=90, height=30,
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["mp4"], hover_color="#e03e4e",
            corner_radius=8,
            command=lambda: on_download_mp4(data)
        )
        mp4_btn.pack(side="left")

    def _load_thumbnail(self, frame, url):
        """Load thumbnail dari URL secara async."""
        def _worker():
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    img_data = BytesIO(resp.content)
                    pil_img = Image.open(img_data)
                    pil_img = pil_img.resize((120, 68), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 68))

                    # Update di main thread
                    self.after(0, lambda: self._set_thumbnail(frame, ctk_img))
            except:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _set_thumbnail(self, frame, ctk_img):
        try:
            for widget in frame.winfo_children():
                widget.destroy()
            label = ctk.CTkLabel(frame, image=ctk_img, text="")
            label.image = ctk_img  # Keep reference
            label.place(relx=0.5, rely=0.5, anchor="center")
        except:
            pass


class DownloadItemCard(ctk.CTkFrame):
    """Card untuk setiap item yang sedang/sudah di-download."""

    def __init__(self, parent, title, format_type="MP3", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=10, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        badge_color = COLORS["mp3"] if format_type == "MP3" else COLORS["mp4"]
        badge = ctk.CTkLabel(
            header, text=f" {format_type} ",
            font=("Segoe UI", 10, "bold"),
            fg_color=badge_color, corner_radius=4,
            text_color="white", width=40
        )
        badge.grid(row=0, column=0, sticky="w")

        if len(title) > 50:
            title = title[:47] + "..."
        self.title_label = ctk.CTkLabel(
            header, text=title,
            font=("Segoe UI", 12, "bold"), text_color=COLORS["text"],
            anchor="w"
        )
        self.title_label.grid(row=0, column=1, padx=(8, 0), sticky="w")

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            fg_color=COLORS["border"], progress_color=badge_color
        )
        self.progress_bar.grid(row=1, column=0, padx=12, pady=(8, 4), sticky="ew")
        self.progress_bar.set(0)

        # Status Text
        self.status_label = ctk.CTkLabel(
            self, text="Menunggu...",
            font=("Segoe UI", 10), text_color=COLORS["text_dim"],
            anchor="w"
        )
        self.status_label.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="w")

    def update_progress(self, value, status_text=""):
        try:
            self.progress_bar.set(value)
            if status_text:
                self.status_label.configure(text=status_text)
        except:
            pass

    def set_done(self, status_text=""):
        try:
            self.progress_bar.set(1.0)
            self.status_label.configure(text=status_text, text_color=COLORS["success"])
        except:
            pass

    def set_error(self, status_text=""):
        try:
            self.status_label.configure(text=status_text, text_color=COLORS["error"])
        except:
            pass


class App(ctk.CTk):
    """Main Application Window."""

    def __init__(self):
        super().__init__()

        # ── Window Config ─────────────────────────
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("900x650")
        self.minsize(750, 550)
        self.configure(fg_color=COLORS["bg_dark"])

        # Set icon if exists
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # ── Downloader Engine ─────────────────────
        saved = load_settings()
        output_dir = saved.get("output_dir") or None
        self.downloader = MusicDownloader(output_dir=output_dir)
        self.download_threads = []

        # ── Build UI ──────────────────────────────
        self._build_sidebar()
        self._build_main_area()

        # ── Check for updates on start ────────────
        self.after(2000, self._check_update_silent)

    # ═══════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════════════════════════════════════

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["bg_card"], corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo / Brand
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))

        logo_label = ctk.CTkLabel(
            logo_frame, text="🎧 MusicDL",
            font=("Segoe UI", 22, "bold"), text_color=COLORS["accent"]
        )
        logo_label.pack(anchor="w")

        version_label = ctk.CTkLabel(
            logo_frame, text=f"v{APP_VERSION}",
            font=("Segoe UI", 11), text_color=COLORS["text_dim"]
        )
        version_label.pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=16, pady=12)

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("🔍  Cari & Download", "search"),
            ("📥  Download Queue", "downloads"),
            ("📁  Buka Folder", "folder"),
            ("⚙️  Pengaturan", "settings"),
        ]

        for text, key in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=text, anchor="w",
                font=("Segoe UI", 13), height=42,
                fg_color="transparent",
                hover_color=COLORS["accent2"],
                text_color=COLORS["text"],
                corner_radius=8,
                command=lambda k=key: self._nav_click(k)
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn

        # Set active
        self.nav_buttons["search"].configure(fg_color=COLORS["accent2"])
        self.active_nav = "search"

        # Bottom area
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(expand=True, fill="both")

        # Update button
        self.update_btn = ctk.CTkButton(
            sidebar, text="🔄 Cek Update",
            font=("Segoe UI", 12), height=36,
            fg_color=COLORS["accent2"],
            hover_color=COLORS["accent"],
            corner_radius=8,
            command=self._check_update_manual
        )
        self.update_btn.pack(fill="x", padx=12, pady=(0, 8))

        # Update status
        self.update_status_label = ctk.CTkLabel(
            sidebar, text="",
            font=("Segoe UI", 10), text_color=COLORS["text_dim"],
            wraplength=190
        )
        self.update_status_label.pack(fill="x", padx=16, pady=(0, 16))

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN AREA
    # ═══════════════════════════════════════════════════════════════════════

    def _build_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.main_container.pack(side="right", expand=True, fill="both")

        # ── Pages ─────────────────────────────────
        self.pages = {}
        self._build_search_page()
        self._build_downloads_page()
        self._build_settings_page()

        # Show search by default
        self._show_page("search")

    def _build_search_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["search"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        title = ctk.CTkLabel(
            header, text="🔍 Cari Musik",
            font=("Segoe UI", 20, "bold"), text_color=COLORS["text"]
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header, text="Cari lagu dari YouTube, download sebagai MP3 atau MP4",
            font=("Segoe UI", 12), text_color=COLORS["text_dim"]
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Search Bar
        search_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12, height=50)
        search_frame.pack(fill="x", padx=24, pady=(0, 12))
        search_frame.pack_propagate(False)

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(expand=True, fill="both", padx=4, pady=4)
        search_inner.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="🔍 Ketik judul lagu atau paste URL YouTube...",
            font=("Segoe UI", 13), height=42,
            fg_color=COLORS["bg_card2"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.search_btn = ctk.CTkButton(
            search_inner, text="Cari", width=80, height=42,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8,
            command=self._do_search
        )
        self.search_btn.grid(row=0, column=1, padx=4, pady=4)

        # ── Direct URL Download ───────────────────
        direct_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12)
        direct_frame.pack(fill="x", padx=24, pady=(0, 12))

        direct_inner = ctk.CTkFrame(direct_frame, fg_color="transparent")
        direct_inner.pack(fill="x", padx=12, pady=10)
        direct_inner.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            direct_inner,
            placeholder_text="🔗 Paste URL langsung di sini (YouTube, SoundCloud, dll)...",
            font=("Segoe UI", 12), height=38,
            fg_color=COLORS["bg_card2"],
            border_color=COLORS["border"],
            corner_radius=8
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        # Quality selector
        self.quality_var = ctk.StringVar(value="720p")
        quality_menu = ctk.CTkOptionMenu(
            direct_inner, variable=self.quality_var,
            values=["360p", "480p", "720p", "1080p", "best"],
            width=90, height=38,
            font=("Segoe UI", 11),
            fg_color=COLORS["bg_card2"],
            button_color=COLORS["accent2"],
            corner_radius=8
        )
        quality_menu.grid(row=0, column=1, padx=(0, 4))

        direct_mp3_btn = ctk.CTkButton(
            direct_inner, text="MP3", width=60, height=38,
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["mp3"], hover_color="#17a34a",
            corner_radius=8,
            command=lambda: self._download_url("mp3")
        )
        direct_mp3_btn.grid(row=0, column=2, padx=2)

        direct_mp4_btn = ctk.CTkButton(
            direct_inner, text="MP4", width=60, height=38,
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["mp4"], hover_color="#e03e4e",
            corner_radius=8,
            command=lambda: self._download_url("mp4")
        )
        direct_mp4_btn.grid(row=0, column=3, padx=2)

        # ── Search Results ────────────────────────
        results_header = ctk.CTkFrame(page, fg_color="transparent")
        results_header.pack(fill="x", padx=24, pady=(4, 4))

        self.results_count_label = ctk.CTkLabel(
            results_header, text="",
            font=("Segoe UI", 12), text_color=COLORS["text_dim"]
        )
        self.results_count_label.pack(anchor="w")

        # Scrollable results
        self.results_scroll = ctk.CTkScrollableFrame(
            page, fg_color="transparent",
            scrollbar_button_color=COLORS["accent2"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.results_scroll.pack(expand=True, fill="both", padx=24, pady=(0, 12))
        self.results_scroll.grid_columnconfigure(0, weight=1)

        # Loading label (hidden by default)
        self.loading_label = ctk.CTkLabel(
            self.results_scroll, text="",
            font=("Segoe UI", 14), text_color=COLORS["text_dim"]
        )

    def _build_downloads_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["downloads"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        title = ctk.CTkLabel(
            header, text="📥 Download Queue",
            font=("Segoe UI", 20, "bold"), text_color=COLORS["text"]
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header, text="Status semua download yang sedang berjalan",
            font=("Segoe UI", 12), text_color=COLORS["text_dim"]
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Downloads list
        self.downloads_scroll = ctk.CTkScrollableFrame(
            page, fg_color="transparent",
            scrollbar_button_color=COLORS["accent2"]
        )
        self.downloads_scroll.pack(expand=True, fill="both", padx=24, pady=(0, 12))
        self.downloads_scroll.grid_columnconfigure(0, weight=1)

        # Empty state
        self.downloads_empty = ctk.CTkLabel(
            self.downloads_scroll, text="📭 Belum ada download\nCari lagu dulu yuk!",
            font=("Segoe UI", 14), text_color=COLORS["text_dim"],
            justify="center"
        )
        self.downloads_empty.grid(row=0, column=0, pady=60)

    def _build_settings_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["settings"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))

        title = ctk.CTkLabel(
            header, text="⚙️ Pengaturan",
            font=("Segoe UI", 20, "bold"), text_color=COLORS["text"]
        )
        title.pack(anchor="w")

        # ── Output Directory ──────────────────────
        card1 = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12)
        card1.pack(fill="x", padx=24, pady=(0, 12))

        card1_inner = ctk.CTkFrame(card1, fg_color="transparent")
        card1_inner.pack(fill="x", padx=16, pady=16)
        card1_inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card1_inner, text="📁 Folder Download",
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.folder_entry = ctk.CTkEntry(
            card1_inner, font=("Segoe UI", 12), height=38,
            fg_color=COLORS["bg_card2"], border_color=COLORS["border"],
            corner_radius=8
        )
        self.folder_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self.folder_entry.insert(0, self.downloader.output_dir)

        browse_btn = ctk.CTkButton(
            card1_inner, text="Browse", width=80, height=38,
            font=("Segoe UI", 12),
            fg_color=COLORS["accent2"], hover_color=COLORS["accent"],
            corner_radius=8,
            command=self._browse_folder
        )
        browse_btn.grid(row=1, column=2)

        # ── GitHub Update ─────────────────────────
        card_gh = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12)
        card_gh.pack(fill="x", padx=24, pady=(0, 12))

        gh_inner = ctk.CTkFrame(card_gh, fg_color="transparent")
        gh_inner.pack(fill="x", padx=16, pady=16)
        gh_inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            gh_inner, text="🐙 Akun GitHub (untuk auto-update)",
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ctk.CTkLabel(
            gh_inner, text="Boleh dikosongin dulu. Isi setelah repo GitHub sudah dibuat.",
            font=("Segoe UI", 11), text_color=COLORS["text_dim"]
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        saved = load_settings()

        ctk.CTkLabel(gh_inner, text="Username", font=("Segoe UI", 12), text_color=COLORS["text_dim"]).grid(row=2, column=0, sticky="w", pady=4)
        self.github_owner_entry = ctk.CTkEntry(
            gh_inner, font=("Segoe UI", 12), height=36,
            fg_color=COLORS["bg_card2"], border_color=COLORS["border"],
            corner_radius=8, placeholder_text="contoh: namauser"
        )
        self.github_owner_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.github_owner_entry.insert(0, saved.get("github_owner", ""))

        ctk.CTkLabel(gh_inner, text="Nama Repo", font=("Segoe UI", 12), text_color=COLORS["text_dim"]).grid(row=3, column=0, sticky="w", pady=4)
        self.github_repo_entry = ctk.CTkEntry(
            gh_inner, font=("Segoe UI", 12), height=36,
            fg_color=COLORS["bg_card2"], border_color=COLORS["border"],
            corner_radius=8, placeholder_text="contoh: music-downloader"
        )
        self.github_repo_entry.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.github_repo_entry.insert(0, saved.get("github_repo", ""))

        save_gh_btn = ctk.CTkButton(
            gh_inner, text="Simpan GitHub", width=140, height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8,
            command=self._save_github_settings
        )
        save_gh_btn.grid(row=4, column=1, sticky="e", pady=(8, 0))

        # ── About ─────────────────────────────────
        card2 = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12)
        card2.pack(fill="x", padx=24, pady=(0, 12))

        card2_inner = ctk.CTkFrame(card2, fg_color="transparent")
        card2_inner.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            card2_inner, text="ℹ️ Tentang Aplikasi",
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 8))

        about_text = (
            f"🎧 {APP_NAME} v{APP_VERSION}\n\n"
            "Music Downloader untuk Windows.\n"
            "Download lagu dari YouTube sebagai MP3 (audio) atau MP4 (video).\n\n"
            "Engine: yt-dlp\n"
            "UI: CustomTkinter\n"
            "Update: GitHub Releases"
        )
        ctk.CTkLabel(
            card2_inner, text=about_text,
            font=("Segoe UI", 12), text_color=COLORS["text_dim"],
            justify="left", anchor="w"
        ).pack(anchor="w")

    # ═══════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════════════

    def _nav_click(self, key):
        if key == "folder":
            self._open_download_folder()
            return

        # Update nav button styles
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["accent2"])
            else:
                btn.configure(fg_color="transparent")

        self.active_nav = key
        self._show_page(key)

    def _show_page(self, key):
        for k, page in self.pages.items():
            page.pack_forget()
        if key in self.pages:
            self.pages[key].pack(expand=True, fill="both")

    # ═══════════════════════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════════════════════

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        # Clear results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        # Show loading
        self.loading_label = ctk.CTkLabel(
            self.results_scroll, text="🔍 Mencari...",
            font=("Segoe UI", 14), text_color=COLORS["text_dim"]
        )
        self.loading_label.grid(row=0, column=0, pady=40)
        self.results_count_label.configure(text="")
        self.search_btn.configure(state="disabled", text="...")

        def _worker():
            results = self.downloader.search(query, max_results=8)
            self.after(0, lambda: self._show_results(results))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_results(self, results):
        # Clear loading
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        self.search_btn.configure(state="normal", text="Cari")

        if not results:
            no_result = ctk.CTkLabel(
                self.results_scroll, text="😔 Tidak ada hasil ditemukan",
                font=("Segoe UI", 14), text_color=COLORS["text_dim"]
            )
            no_result.grid(row=0, column=0, pady=40)
            self.results_count_label.configure(text="0 hasil")
            return

        self.results_count_label.configure(text=f"🎵 {len(results)} hasil ditemukan")

        for i, item in enumerate(results):
            card = SearchResultCard(
                self.results_scroll, item,
                on_download_mp3=self._start_download_mp3,
                on_download_mp4=self._start_download_mp4
            )
            card.grid(row=i, column=0, padx=4, pady=4, sticky="ew")

    # ═══════════════════════════════════════════════════════════════════════
    # DOWNLOAD
    # ═══════════════════════════════════════════════════════════════════════

    def _download_url(self, format_type):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Kosong", "Paste URL dulu bro!")
            return

        if format_type == "mp3":
            self._start_download_mp3({"title": "Direct URL", "url": url})
        else:
            self._start_download_mp4({"title": "Direct URL", "url": url})

    def _start_download_mp3(self, data):
        title = data.get('title', 'Unknown')
        url = data.get('url', '')

        # Auto switch to downloads page
        self._nav_click("downloads")

        # Create download card
        card = DownloadItemCard(self.downloads_scroll, title, "MP3")
        card.grid(row=len(self.downloads_scroll.winfo_children()), column=0, padx=4, pady=4, sticky="ew")

        # Hide empty state
        if hasattr(self, 'downloads_empty'):
            self.downloads_empty.grid_forget()

        def _callback(status, progress, message):
            if status == "done":
                self.after(0, lambda: card.set_done(message))
            elif status == "error":
                self.after(0, lambda: card.set_error(message))
            else:
                self.after(0, lambda: card.update_progress(progress, message))

        thread = self.downloader.download_mp3(url, callback=_callback)
        self.download_threads.append(thread)

    def _start_download_mp4(self, data):
        title = data.get('title', 'Unknown')
        url = data.get('url', '')
        quality = self.quality_var.get()

        # Auto switch to downloads page
        self._nav_click("downloads")

        # Create download card
        card = DownloadItemCard(self.downloads_scroll, title, "MP4")
        card.grid(row=len(self.downloads_scroll.winfo_children()), column=0, padx=4, pady=4, sticky="ew")

        # Hide empty state
        if hasattr(self, 'downloads_empty'):
            self.downloads_empty.grid_forget()

        def _callback(status, progress, message):
            if status == "done":
                self.after(0, lambda: card.set_done(message))
            elif status == "error":
                self.after(0, lambda: card.set_error(message))
            else:
                self.after(0, lambda: card.update_progress(progress, message))

        thread = self.downloader.download_mp4(url, quality=quality, callback=_callback)
        self.download_threads.append(thread)

    # ═══════════════════════════════════════════════════════════════════════
    # SETTINGS & FOLDER
    # ═══════════════════════════════════════════════════════════════════════

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder Download")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.downloader.output_dir = folder
            os.makedirs(folder, exist_ok=True)
            save_settings({"output_dir": folder})

    def _save_github_settings(self):
        owner = self.github_owner_entry.get().strip()
        repo = self.github_repo_entry.get().strip()
        save_settings({"github_owner": owner, "github_repo": repo})
        if owner and repo:
            messagebox.showinfo("Tersimpan", f"GitHub disimpan:\n{owner}/{repo}\n\nNanti tombol Cek Update akan baca repo ini.")
        else:
            messagebox.showinfo("Tersimpan", "GitHub dikosongin. Auto-update nonaktif sampai diisi.")

    def _open_download_folder(self):
        folder = self.downloader.output_dir
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            os.makedirs(folder, exist_ok=True)
            os.startfile(folder)

    # ═══════════════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════════════

    def _update_callback(self, status, progress):
        self.after(0, lambda: self.update_status_label.configure(text=status))

    def _check_update_silent(self):
        """Cek update diam-diam waktu app start."""
        updater = Updater(callback=self._update_callback)

        def _worker():
            has_update = updater.check_for_updates()
            if has_update:
                self.after(0, lambda: self._show_update_dialog(updater))

        threading.Thread(target=_worker, daemon=True).start()

    def _check_update_manual(self):
        """Cek update manual dari tombol."""
        updater = Updater(callback=self._update_callback)

        def _worker():
            has_update = updater.check_for_updates()
            if has_update:
                self.after(0, lambda: self._show_update_dialog(updater))
            else:
                self.after(0, lambda: messagebox.showinfo(
                    "Tidak Ada Update",
                    f"Sudah versi terbaru (v{APP_VERSION})"
                ))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_dialog(self, updater):
        result = messagebox.askyesno(
            "Update Tersedia! 🎉",
            f"Versi baru tersedia: v{updater.latest_version}\n"
            f"Versi sekarang: v{APP_VERSION}\n\n"
            f"📝 Release Notes:\n{updater.release_notes[:300]}\n\n"
            "Download dan install sekarang?"
        )
        if result:
            def _do_update():
                filepath = updater.download_update()
                if filepath:
                    updater.install_update(filepath)
            threading.Thread(target=_do_update, daemon=True).start()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
