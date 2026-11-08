"""Token desain Libris: dua palet (DARK bawaan, LIGHT), skala jarak/huruf, dan helper status.

Seluruh warna aplikasi HARUS berasal dari modul ini (sumber: :root prototipe v1.2).
`apply(mode)` mengisi variabel modul (BG, PANEL, ...) sehingga widget membaca `theme.BG` saat dibuat.
"""
import customtkinter as ctk

DARK = {
    "BG": "#0b1020", "PANEL": "#111a2d", "PANEL2": "#172238", "PANEL3": "#1d2a43", "LINE": "#263550",
    "TEXT": "#edf3ff", "SOFT": "#c5d0e2", "MUTED": "#91a0ba",
    "ACCENT": "#54d6e8", "BLUE": "#6b8cff", "PURPLE": "#a78bfa",
    "OK": "#43c99a", "WARN": "#f3bd62", "DANGER": "#fb7185",
    # turunan (dari prototipe): sidebar, input, teks di atas aksen, hover
    "SIDEBAR": "#0e1729", "INPUT": "#111c30", "ON_ACCENT": "#06222a",
    "ACCENT_HOVER": "#3fc2d5", "DANGER_HOVER": "#e25a70", "ON_DANGER": "#2b0a12",
}
LIGHT = {
    "BG": "#F4F6FA", "PANEL": "#FFFFFF", "PANEL2": "#E8EEF7", "PANEL3": "#DCE6F5", "LINE": "#D5DCE8",
    "TEXT": "#1B2430", "SOFT": "#3D4858", "MUTED": "#6B7686",
    "ACCENT": "#1F4E8C", "BLUE": "#2F6FDB", "PURPLE": "#6D4AC9",
    "OK": "#1E8449", "WARN": "#B9770E", "DANGER": "#C0392B",
    "SIDEBAR": "#1F4E8C", "INPUT": "#FFFFFF", "ON_ACCENT": "#FFFFFF",
    "ACCENT_HOVER": "#173B6B", "DANGER_HOVER": "#922B21", "ON_DANGER": "#FFFFFF",
}

# badge: (teks, latar, garis)
BADGES_DARK = {
    "green": ("#78e0b3", "#153a31", "#245b49"), "blue": ("#8bb6ff", "#1b2f50", "#2c4773"),
    "amber": ("#f5cb7b", "#42351d", "#6c5428"), "red": ("#ff9cac", "#442330", "#713548"),
    "purple": ("#c3aaff", "#30264c", "#514076"), "gray": ("#b0bfd3", "#273448", "#3a4b63"),
}
BADGES_LIGHT = {
    "green": ("#14653A", "#DDF3E8", "#A9DCC0"), "blue": ("#1F4E8C", "#DCE8FA", "#A8C3EA"),
    "amber": ("#8A5A06", "#FBEFD2", "#EACB86"), "red": ("#A12A1F", "#FADDD9", "#EBAAA3"),
    "purple": ("#4F2FA3", "#E8E0FA", "#C3B2EE"), "gray": ("#4B5666", "#E6EAF0", "#C3CBD6"),
}

# status -> jenis badge
STATUS_KIND = {
    "Tersedia": "green", "Ditemukan": "green", "Lunas": "green", "Final": "green",
    "Dipinjam": "blue", "Berjalan": "blue", "Ditemukan ekstra": "purple",
    "Perbaikan": "amber", "Sebagian": "amber", "Belum ditemukan": "amber", "Pemeriksaan ulang": "amber",
    "Hilang": "red", "Belum bayar": "red", "Hilang terkonfirmasi": "red",
    "Dihapusbukukan": "gray", "Belum diperiksa": "gray",
    "Aktif": "green", "Nonaktif": "gray", "Arsip": "gray",
}
KIND_TOKEN = {"green": "OK", "blue": "BLUE", "amber": "WARN", "red": "DANGER", "purple": "PURPLE", "gray": "MUTED"}

# skala (px / pt)
SP1, SP2, SP3, SP4, SP6 = 4, 8, 12, 16, 24
PAD = 24          # padding halaman
GAP = 16          # jarak antarkartu
PAD_CARD = 16     # padding dalam kartu
FS_TITLE, FS_SECTION, FS_BODY, FS_CAPTION, FS_TH, FS_TABLE, FS_STAT, FS_SCAN = 22, 15, 13, 12, 11, 10, 26, 15
R_CARD, R_BTN, R_INPUT = 14, 9, 9
H_CTRL, H_SCAN = 34, 42
ROW_H = 34
FONT_FAMILY = "Segoe UI"

MODE = "dark"
_badges = BADGES_DARK
STATUS_COLORS = {}


def apply(mode="dark"):
    """Pilih palet, isi variabel token modul, atur mode CustomTkinter dan gaya ttk (sekali)."""
    global MODE, _badges
    MODE = "light" if str(mode).lower() == "light" else "dark"
    palette = LIGHT if MODE == "light" else DARK
    _badges = BADGES_LIGHT if MODE == "light" else BADGES_DARK
    globals().update(palette)
    STATUS_COLORS.clear()
    STATUS_COLORS.update({s: palette[KIND_TOKEN[k]] for s, k in STATUS_KIND.items()})
    ctk.set_appearance_mode(MODE)
    ctk.set_default_color_theme("blue")
    configure_ttk()


def configure_ttk(scale=None):
    """Gaya Treeview/Scrollbar/Combobox. Dipanggil sekali oleh apply bila root Tk sudah ada."""
    import tkinter as tk
    from tkinter import ttk
    root = tk._default_root
    if root is None:
        return
    f = scale if scale is not None else dpi_factor(root)
    p = DARK if MODE == "dark" else LIGHT
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure("Libris.Treeview", rowheight=int(ROW_H * f), font=(FONT_FAMILY, FS_TABLE), background=p["PANEL"],
                 fieldbackground=p["PANEL"], foreground=p["TEXT"], borderwidth=0, relief="flat")
    st.map("Libris.Treeview", background=[("selected", p["PANEL3"])], foreground=[("selected", p["TEXT"])])
    st.configure("Libris.Treeview.Heading", font=(FONT_FAMILY, FS_TH, "bold"), background=p["PANEL2"],
                 foreground=p["MUTED"], borderwidth=0, relief="flat", padding=(8, 8))
    st.map("Libris.Treeview.Heading", background=[("active", p["PANEL3"])])
    st.layout("Libris.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    for orient in ("Vertical", "Horizontal"):
        st.configure(f"Libris.{orient}.TScrollbar", background=p["PANEL3"], troughcolor=p["PANEL"], bordercolor=p["PANEL"],
                     arrowcolor=p["MUTED"], lightcolor=p["PANEL3"], darkcolor=p["PANEL3"], relief="flat")


def dpi_factor(widget) -> float:
    """Faktor skala layar (1.0 = 96 dpi). Treeview tidak mengikuti skala CustomTkinter."""
    try:
        return max(1.0, widget.winfo_fpixels("1i") / 96.0)
    except Exception:
        return 1.0


def font(size=FS_BODY, bold=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold" if bold else "normal")


def status_kind(status) -> str:
    return STATUS_KIND.get(status, "gray")


def badge_style(kind):
    """(teks, latar, garis) untuk jenis badge: green|blue|amber|red|purple|gray."""
    return _badges.get(kind, _badges["gray"])


def rupiah(n) -> str:
    return "Rp" + f"{int(n or 0):,}".replace(",", ".")


apply("dark")   # nilai bawaan agar token tersedia saat modul diimpor
