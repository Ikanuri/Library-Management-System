"""Jendela utama: login, sidebar, navigasi, backup otomatis saat buka/tutup."""
from tkinter import messagebox

import customtkinter as ctk

import config
from app.context import Services
from app.services.base import ServiceError
from . import theme
from .components import guard
from .pages_admin import (BackupPage, ImportLabelPage, OpnamePage, ReportsPage, SettingsPage, UsersPage)
from .pages_circ import FinesPage, LoansPage, ReturnsPage
from .pages_core import BookDetailPage, BooksPage, DashboardPage, MembersPage

NAV = [("dashboard", "Dashboard", DashboardPage, False), ("books", "Koleksi Buku", BooksPage, False),
       ("members", "Anggota", MembersPage, False), ("loans", "Peminjaman", LoansPage, False),
       ("returns", "Pengembalian", ReturnsPage, False), ("fines", "Denda", FinesPage, False),
       ("opname", "Stok Opname", OpnamePage, False), ("import", "Impor & Label", ImportLabelPage, False),
       ("reports", "Laporan", ReportsPage, False), ("backup", "Backup & Restore", BackupPage, False),
       ("users", "Petugas & Log", UsersPage, True), ("settings", "Pengaturan", SettingsPage, True)]


class LibrisApp(ctk.CTk):
    def __init__(self, services: Services | None = None):
        super().__init__()
        theme.setup()
        self.title(f"{config.APP_NAME} — Sistem Manajemen Perpustakaan")
        self.geometry("1280x780"); self.minsize(1100, 680)
        self.configure(fg_color=theme.BG)
        self.services = services or Services(config.db_path(), config.backup_dir())
        self.actor = None
        self.pages, self.nav_buttons, self.current = {}, {}, None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._auto_backup("buka")
        self.show_login()

    # ---------- login ----------
    def show_login(self):
        self.actor = None
        for w in self.winfo_children():
            w.destroy()
        self.pages, self.nav_buttons = {}, {}
        box = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=12, width=380)
        box.place(relx=0.5, rely=0.5, anchor="center")
        first = self.services.auth.user_count() == 0
        ctk.CTkLabel(box, text="Libris", font=theme.font(30, True), text_color=theme.PRIMARY).pack(padx=40, pady=(28, 0))
        ctk.CTkLabel(box, text="Pengaturan awal: buat akun Administrator" if first else "Masuk untuk melanjutkan",
                     text_color=theme.MUTED).pack(pady=(0, 14))
        self.u = ctk.CTkEntry(box, placeholder_text="Username", width=280); self.u.pack(pady=4)
        self.n = None
        if first:
            self.n = ctk.CTkEntry(box, placeholder_text="Nama lengkap", width=280); self.n.pack(pady=4)
        self.p = ctk.CTkEntry(box, placeholder_text="Password", show="*", width=280); self.p.pack(pady=4)
        self.err = ctk.CTkLabel(box, text="", text_color=theme.DANGER, wraplength=280); self.err.pack()
        ctk.CTkButton(box, text="Buat akun" if first else "Masuk", command=lambda: self.do_login(first), width=280).pack(pady=(4, 28), padx=40)
        self.p.bind("<Return>", lambda e: self.do_login(first)); self.u.focus_set()

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
        for w in self.winfo_children():
            w.destroy()
        side = ctk.CTkFrame(self, width=210, fg_color=theme.PRIMARY, corner_radius=0)
        side.pack(side="left", fill="y"); side.pack_propagate(False)
        ctk.CTkLabel(side, text="Libris", font=theme.font(24, True), text_color="white").pack(anchor="w", padx=18, pady=(18, 2))
        ctk.CTkLabel(side, text=f"{self.actor.full_name} · {'Administrator' if self.actor.is_admin else 'Petugas'}",
                     text_color="#C9D8EE", font=theme.font(11)).pack(anchor="w", padx=18, pady=(0, 12))
        self.content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        for key, label, cls, admin_only in NAV:
            if admin_only and not self.actor.is_admin:
                continue
            b = ctk.CTkButton(side, text=label, anchor="w", fg_color="transparent", hover_color=theme.PRIMARY_HOVER,
                              command=lambda k=key: self.show(k), corner_radius=6)
            b.pack(fill="x", padx=10, pady=1); self.nav_buttons[key] = b
            self.pages[key] = cls(self.content, self)
        self.pages["detail"] = BookDetailPage(self.content, self)
        ctk.CTkButton(side, text="Keluar", fg_color="#12315A", hover_color=theme.PRIMARY_HOVER, command=self.logout).pack(side="bottom", fill="x", padx=10, pady=14)
        self.show("dashboard")

    def show(self, key, **kw):
        if self.current:
            self.current.pack_forget()
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        self.current = page
        for k, b in self.nav_buttons.items():
            b.configure(fg_color=theme.PRIMARY_HOVER if k == key or (key == "detail" and k == "books") else "transparent")
        try:
            page.refresh(**kw)
        except ServiceError as e:
            messagebox.showwarning("Libris", str(e))

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
