"""Tema, warna status, dan font terpusat."""
import customtkinter as ctk

PRIMARY = "#1F4E8C"
PRIMARY_HOVER = "#173B6B"
BG = "#F4F6FA"
CARD = "#FFFFFF"
TEXT = "#1B2430"
MUTED = "#6B7686"
DANGER = "#C0392B"
OK = "#1E8449"
WARN = "#B9770E"

STATUS_COLORS = {
    "Tersedia": OK, "Dipinjam": PRIMARY, "Perbaikan": WARN, "Hilang": DANGER, "Dihapusbukukan": MUTED,
    "Ditemukan": OK, "Belum diperiksa": MUTED, "Belum ditemukan": WARN, "Hilang terkonfirmasi": DANGER,
    "Ditemukan ekstra": PRIMARY, "Lunas": OK, "Sebagian": WARN, "Belum bayar": DANGER,
    "Berjalan": PRIMARY, "Pemeriksaan ulang": WARN, "Final": OK,
}


def setup():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font(size=13, bold=False):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold" if bold else "normal")


def rupiah(n) -> str:
    return "Rp" + f"{int(n or 0):,}".replace(",", ".")
