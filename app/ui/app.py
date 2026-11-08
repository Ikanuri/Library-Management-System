"""Jendela utama: login, sidebar berkelompok, topbar, navigasi, backup otomatis saat buka/tutup."""
import customtkinter as ctk

import config
from app.context import Services
from app.services.base import ServiceError
from . import theme
from .components import make_button, style_entry, warn
from .pages_admin import (BackupPage, ImportLabelPage, OpnamePage, ReportsPage, SettingsPage, UsersPage)
from .pages_circ import FinesPage, LoansPage, ReturnsPage
from .pages_core import BookDetailPage, BooksPage, DashboardPage, MembersPage

# (kunci, label, ikon, kelas, admin_only) per kelompok — mengikuti sidebar prototipe v1.2
NAV_GROUPS = [
    ("WORKSPACE", [("dashboard", "Dashboard", "◫", DashboardPage, False), ("books", "Katalog Buku", "▤", BooksPage, False),
                   ("members", "Anggota", "♙", MembersPage, False)]),
    ("SIRKULASI", [("loans", "Peminjaman", "↗", LoansPage, False), ("returns", "Pengembalian", "↙", ReturnsPage, False),
                   ("fines", "Denda", "◈", FinesPage, False)]),
    ("PENGELOLAAN", [("opname", "Stok Opname", "▦", OpnamePage, False), ("import", "Impor & Label", "↑", ImportLabelPage, False),
                     ("reports", "Laporan", "▥", ReportsPage, False), ("backup", "Backup & Restore", "↓", BackupPage, False)]),
    ("SISTEM", [("users", "Petugas & Log", "☰", UsersPage, True), ("settings", "Pengaturan", "⚙", SettingsPage, True)]),
]
TITLES = {k: label for _, items in NAV_GROUPS for k, label, *_ in items} | {"detail": "Detail Buku"}


class NavItem(ctk.CTkFrame):
    """Item menu: ikon + teks, garis kiri 3 px ACCENT dan latar PANEL3 saat aktif, PANEL2 saat hover."""

    def __init__(self, master, icon, text, command):
        super().__init__(master, fg_color="transparent", corner_radius=theme.R_BTN, height=36)
        self.command, self.active = command, False
        self.bar = ctk.CTkFrame(self, width=3, corner_radius=2, fg_color="transparent")
        self.bar.pack(side="left", fill="y", padx=(2, 0), pady=6)
        self.ico = ctk.CTkLabel(self, text=icon, width=22, font=ctk.CTkFont(family="Segoe UI Symbol", size=14), text_color=theme.MUTED)
        self.ico.pack(side="left", padx=(10, 6))
        self.lbl = ctk.CTkLabel(self, text=text, anchor="w", font=theme.font(theme.FS_BODY), text_color=theme.SOFT)
        self.lbl.pack(side="left", fill="x", expand=True)
        for w in (self, self.bar, self.ico, self.lbl):
            w.bind("<Button-1>", lambda e: self.command())
            w.bind("<Enter>", lambda e: self._paint(hover=True))
            w.bind("<Leave>", lambda e: self._paint())
        self.configure(cursor="hand2")

    def _paint(self, hover=False):
        bg = theme.PANEL3 if self.active else (theme.PANEL2 if hover else "transparent")
        self.configure(fg_color=bg)
        self.bar.configure(fg_color=theme.ACCENT if self.active else "transparent")
        self.ico.configure(text_color=theme.ACCENT if self.active else theme.MUTED)
        self.lbl.configure(text_color=theme.TEXT if self.active else theme.SOFT,
                           font=theme.font(theme.FS_BODY, self.active))

    def set_active(self, on):
        self.active = on
        self._paint()


class LibrisApp(ctk.CTk):
    def __init__(self, services: Services | None = None):
        super().__init__()
        theme.apply("dark")       # setelah root Tk ada, agar gaya ttk ikut terkonfigurasi
        self.title(f"{config.APP_NAME} — Sistem Manajemen Perpustakaan")
        self.geometry("1280x780"); self.minsize(1100, 680)
        self.configure(fg_color=theme.BG)
        self.services = services or Services(config.db_path(), config.backup_dir())
        self.actor = None
        self.pages, self.nav_buttons, self.current, self.current_key = {}, {}, None, None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._auto_backup("buka")
        self.show_login()

    # ---------- login ----------
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()
        self.pages, self.nav_buttons, self.current = {}, {}, None

    def show_login(self):
        self.actor = None
        self._clear()
        first = self.services.auth.user_count() == 0
        box = ctk.CTkFrame(self, fg_color=theme.PANEL, border_width=1, border_color=theme.LINE, corner_radius=theme.R_CARD + 2)
        box.place(relx=0.5, rely=0.5, anchor="center")
        self._brand(box).pack(anchor="w", padx=36, pady=(32, 8))
        ctk.CTkLabel(box, text="Pengaturan awal: buat akun Administrator pertama." if first else "Masuk untuk mengelola perpustakaan.",
                     text_color=theme.MUTED, font=theme.font(theme.FS_CAPTION), wraplength=300, justify="left").pack(anchor="w", padx=36, pady=(0, 14))
        self.u = style_entry(box, height=38, placeholder_text="Username", width=320); self.u.pack(padx=36, pady=4)
        self.n = None
        if first:
            self.n = style_entry(box, height=38, placeholder_text="Nama lengkap", width=320); self.n.pack(padx=36, pady=4)
        self.p = style_entry(box, height=38, placeholder_text="Password", show="*", width=320); self.p.pack(padx=36, pady=4)
        self.err = ctk.CTkLabel(box, text="", text_color=theme.DANGER, font=theme.font(theme.FS_CAPTION), wraplength=320, justify="left")
        self.err.pack(anchor="w", padx=36, pady=(4, 0))
        make_button(box, "Buat akun" if first else "Masuk", lambda: self.do_login(first), "primary", width=320, height=38).pack(padx=36, pady=(8, 32))
        for w in (self.u, self.p) + ((self.n,) if self.n else ()):
            w.bind("<Return>", lambda e: self.do_login(first))
        self.u.focus_set()

    def _brand(self, master, color=None):
        row = ctk.CTkFrame(master, fg_color="transparent")
        mark = ctk.CTkFrame(row, width=38, height=38, corner_radius=10, fg_color=theme.ACCENT); mark.pack(side="left"); mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="L", text_color=theme.ON_ACCENT, font=theme.font(18, True)).pack(expand=True)
        col = ctk.CTkFrame(row, fg_color="transparent"); col.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(col, text="LIBRIS", font=theme.font(theme.FS_SECTION, True), text_color=theme.TEXT).pack(anchor="w")
        ctk.CTkLabel(col, text="Library system", font=theme.font(theme.FS_TH - 1), text_color=theme.MUTED).pack(anchor="w")
        return row

    def do_login(self, first):
        try:
            if first:
                self.services.auth.create_user(None, self.u.get(), self.p.get(), self.n.get() or self.u.get(), "admin")
            self.actor = self.services.auth.login(self.u.get(), self.p.get())
        except ServiceError as e:
            self.err.configure(text=str(e)); return
        self.build_main()

    def logout(self):
        if self.actor:
            self.services.auth.logout(self.actor)
        self.show_login()

    # ---------- layout utama ----------
    def build_main(self):
        self._clear()
        side = ctk.CTkFrame(self, width=250, fg_color=theme.SIDEBAR, corner_radius=0, border_width=0)
        side.pack(side="left", fill="y"); side.pack_propagate(False)
        ctk.CTkFrame(self, width=1, fg_color=theme.LINE, corner_radius=0).pack(side="left", fill="y")
        self._brand(side).pack(anchor="w", padx=18, pady=(22, 14))
        main = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0); main.pack(side="left", fill="both", expand=True)
        self._topbar(main)
        self.content = ctk.CTkFrame(main, fg_color=theme.BG, corner_radius=0); self.content.pack(fill="both", expand=True)
        nav = ctk.CTkScrollableFrame(side, fg_color="transparent", corner_radius=0); nav.pack(fill="both", expand=True, padx=6)
        for group, items in NAV_GROUPS:
            visible = [i for i in items if self.actor.is_admin or not i[4]]
            if not visible:
                continue
            ctk.CTkLabel(nav, text=group, font=theme.font(theme.FS_TH - 2, True), text_color=theme.MUTED).pack(anchor="w", padx=14, pady=(14, 4))
            for key, label, icon, cls, _ in visible:
                item = NavItem(nav, icon, label, lambda k=key: self.show(k)); item.pack(fill="x", pady=1)
                self.nav_buttons[key] = item
                self.pages[key] = cls(self.content, self)
        self.pages["detail"] = BookDetailPage(self.content, self)
        prof = ctk.CTkFrame(side, fg_color="transparent"); prof.pack(side="bottom", fill="x", padx=14, pady=16)
        ctk.CTkFrame(side, height=1, fg_color=theme.LINE, corner_radius=0).pack(side="bottom", fill="x")
        av = ctk.CTkFrame(prof, width=36, height=36, corner_radius=18, fg_color=theme.PANEL3); av.pack(side="left"); av.pack_propagate(False)
        name = (self.actor.full_name or self.actor.username or "?")
        ctk.CTkLabel(av, text=name[:1].upper(), text_color=theme.ACCENT, font=theme.font(14, True)).pack(expand=True)
        info = ctk.CTkFrame(prof, fg_color="transparent"); info.pack(side="left", padx=10)
        ctk.CTkLabel(info, text=name[:22], font=theme.font(theme.FS_CAPTION, True), text_color=theme.TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text="Akses penuh" if self.actor.is_admin else "Petugas", font=theme.font(theme.FS_TH - 1), text_color=theme.MUTED).pack(anchor="w")
        make_button(prof, "Keluar", self.logout, "ghost", width=56, height=28).pack(side="right")
        self.show("dashboard")

    def _topbar(self, master):
        bar = ctk.CTkFrame(master, height=48, fg_color=theme.PANEL, corner_radius=0); bar.pack(fill="x"); bar.pack_propagate(False)
        ctk.CTkFrame(master, height=1, fg_color=theme.LINE, corner_radius=0).pack(fill="x")
        self.crumb = ctk.CTkLabel(bar, text="", font=theme.font(theme.FS_CAPTION), text_color=theme.MUTED)
        self.crumb.pack(side="left", padx=theme.PAD)
        fg, bg, line = theme.badge_style("green")
        pill = ctk.CTkFrame(bar, fg_color=bg, border_width=1, border_color=line, corner_radius=12)
        pill.pack(side="right", padx=theme.PAD)
        ctk.CTkLabel(pill, text="●  MODE OFFLINE", text_color=fg, font=theme.font(theme.FS_TH - 1, True)).pack(padx=10, pady=2)

    def show(self, key, **kw):
        if self.current:
            self.current.pack_forget()
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        self.current, self.current_key = page, key
        self.crumb.configure(text=f"LIBRIS  /  {TITLES.get(key, key)}")
        for k, b in self.nav_buttons.items():
            b.set_active(k == key or (key == "detail" and k == "books"))
        try:
            page.refresh(**kw)
        except ServiceError as e:
            warn(str(e))

    # ---------- backup otomatis ----------
    def _auto_backup(self, kind):
        try:
            self.services.backups.backup(None, kind=f"otomatis-{kind}")
        except Exception:
            pass   # kegagalan backup otomatis tidak boleh menghalangi aplikasi; peringatan tampil di dashboard

    def on_close(self):
        self._auto_backup("tutup")
        self.services.close()
        self.destroy()
