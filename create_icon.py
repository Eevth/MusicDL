"""Generate icon.ico untuk MusicDL (headphones + waveform)."""
from PIL import Image, ImageDraw
import os


def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    bg = (15, 15, 15, 255)
    accent = (233, 69, 96, 255)
    accent_dark = (200, 30, 69, 255)
    white = (255, 255, 255, 255)
    green = (29, 185, 84, 255)

    pad = size * 0.06
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size * 0.22, fill=bg)

    cx, cy = size / 2, size / 2
    r = size * 0.32
    thickness = max(2, int(size * 0.07))

    # Headband
    d.arc(
        [cx - r, cy - r * 1.05, cx + r, cy + r * 0.35],
        start=200, end=340, fill=accent, width=thickness
    )

    ear_w = size * 0.16
    ear_h = size * 0.24
    left = [cx - r - ear_w * 0.15, cy - ear_h * 0.15, cx - r + ear_w * 0.85, cy + ear_h * 0.95]
    right = [cx + r - ear_w * 0.85, cy - ear_h * 0.15, cx + r + ear_w * 0.15, cy + ear_h * 0.95]
    d.rounded_rectangle(left, radius=size * 0.05, fill=accent)
    d.rounded_rectangle(right, radius=size * 0.05, fill=accent_dark)

    # Waveform
    bars = 5
    bar_w = max(1, size * 0.035)
    gap = size * 0.03
    heights = [0.22, 0.38, 0.55, 0.34, 0.2]
    total_w = bars * bar_w + (bars - 1) * gap
    start_x = cx - total_w / 2
    base_y = cy + size * 0.28
    for i, h in enumerate(heights):
        x0 = start_x + i * (bar_w + gap)
        y0 = base_y - size * h
        color = green if i % 2 == 0 else white
        d.rounded_rectangle([x0, y0, x0 + bar_w, base_y], radius=bar_w / 2, fill=color)

    return img


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "music_downloader", "assets")
    os.makedirs(out_dir, exist_ok=True)
    ico_path = os.path.join(out_dir, "icon.ico")
    png_path = os.path.join(out_dir, "icon.png")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    images[-1].save(png_path)
    images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"✅ Icon dibuat: {ico_path}")
    print(f"✅ Preview PNG: {png_path}")


if __name__ == "__main__":
    main()
