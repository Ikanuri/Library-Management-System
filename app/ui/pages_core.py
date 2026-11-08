"""Dashboard, Katalog Buku, Detail Buku, Anggota."""
import tkinter as tk

import customtkinter as ctk

from app.services.book_service import ARCHIVE_REASONS, CONDITIONS
from . import theme
from .components import (Card, DataTable, FormDialog, StatCard, Toolbar, caption, confirm, guard, holder, info, make_button,
                         section_label, toast)


class Page(ctk.CTkFrame):
    """Halaman standar: header (judul, subjudul opsional, area aksi kanan) + `self.body` berpadding 24."""
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG, corner_radius=0)
        self.app, self.s = app, app.services
        head = ctk.CTkFrame(self, fg_color="transparent"); head.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, theme.SP4))
        left = ctk.CTkFrame(head, fg_color="transparent"); left.pack(side="left")
        ctk.CTkLabel(left, text=self.title, font=theme.font(theme.FS_TITLE, True), text_color=theme.TEXT).pack(anchor="w")
        self.subtitle_lbl = ctk.CTkLabel(left, text=self.subtitle, font=theme.font(theme.FS_CAPTION), text_color=theme.MUTED)
        if self.subtitle:
            self.subtitle_lbl.pack(anchor="w")
        self.actions = holder(head); self.actions.pack(side="right")
        self.body = ctk.CTkFrame(self, fg_color="transparent"); self.body.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, theme.PAD))

    def add_action(self, text, cmd, variant="primary"):
        b = make_button(self.actions, text, guard(cmd), variant); b.pack(side="left", padx=(theme.SP2, 0)); return b

    def set_subtitle(self, text):
        self.subtitle_lbl.configure(text=text)
        if text:
            self.subtitle_lbl.pack(anchor="w")

    @property
    def actor(self):
        return self.app.actor

    def refresh(self, **kw):
        pass

    def toast(self, msg, kind="ok"):
        toast(self, msg, kind)


class DashboardPage(Page):
    title = "Dashboard"
    subtitle = "Ringkasan operasional perpustakaan"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.banner_slot = holder(self.body); self.banner_slot.pack(fill="x")
        grid = ctk.CTkFrame(self.body, fg_color="transparent"); grid.pack(fill="x")
        accents = {"titles": theme.ACCENT, "copies": theme.BLUE, "available": theme.OK, "borrowed": theme.BLUE,
                   "members": theme.PURPLE, "loans_today": theme.ACCENT, "overdue": theme.DANGER, "fine": theme.WARN}
        spec = [("titles", "Total judul"), ("copies", "Total eksemplar"), ("available", "Tersedia"), ("borrowed", "Dipinjam"),
                ("members", "Anggota aktif"), ("loans_today", "Pinjam hari ini"), ("overdue", "Terlambat"), ("fine", "Denda belum lunas")]
        self.cards = {}
        for i, (k, lbl) in enumerate(spec):
            c = StatCard(grid, lbl, color=accents[k])
            c.grid(row=i // 4, column=i % 4, padx=(0 if i % 4 == 0 else theme.GAP // 2, 0 if i % 4 == 3 else theme.GAP // 2), pady=theme.GAP // 2, sticky="ew")
            grid.columnconfigure(i % 4, weight=1, uniform="stat"); self.cards[k] = c
        lower = ctk.CTkFrame(self.body, fg_color="transparent"); lower.pack(fill="both", expand=True, pady=(theme.SP2, 0))
        lower.columnconfigure(0, weight=3); lower.columnconfigure(1, weight=2); lower.rowconfigure(0, weight=1)
        chart_card = Card(lower, "Peminjaman per bulan", "Enam bulan terakhir"); chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, theme.GAP // 2))
        self.chart = tk.Canvas(chart_card, height=210, bg=theme.PANEL, highlightthickness=0)
        self.chart.pack(fill="both", expand=True, padx=theme.PAD_CARD, pady=theme.PAD_CARD)
        self._monthly, self._redraw_job = [], None
        self.chart.bind("<Configure>", self._debounced_redraw)
        self.op_card = Card(lower, "Stok opname"); self.op_card.grid(row=0, column=1, sticky="nsew", padx=(theme.GAP // 2, 0))
        self.op_text = ctk.CTkLabel(self.op_card, text="", font=theme.font(theme.FS_BODY), text_color=theme.SOFT, justify="left", anchor="w", wraplength=300)
        self.op_text.pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(theme.SP2, theme.SP2))
        self.op_bar = ctk.CTkProgressBar(self.op_card, progress_color=theme.ACCENT, fg_color=theme.PANEL3, height=8)
        self.op_bar.pack(fill="x", padx=theme.PAD_CARD + 2, pady=(0, theme.PAD_CARD)); self.op_bar.set(0)

    def refresh(self, **kw):
        d = self.s.reports.dashboard()
        for k in ("titles", "copies", "available", "borrowed", "members", "loans_today", "overdue"):
            self.cards[k].set(d[k])
        self.cards["fine"].set(theme.rupiah(d["fines"]["outstanding"]))
        self._banner(self.s.backups.warnings())
        self._monthly = d["monthly"]; self._draw_chart()
        o = d["opname"]
        if o:
            self.op_text.configure(text=f"{o['session']['name']}\n{o['percent']}% cakupan rak diperiksa ({o['found']}/{o['shelf_scope']})\nDipinjam {o['borrowed']} · Belum ditemukan {o['not_found']}")
            self.op_bar.set(o["percent"] / 100)
        else:
            self.op_text.configure(text="Tidak ada sesi stok opname yang sedang berjalan.")
            self.op_bar.set(0)

    def _banner(self, warnings):
        for w in self.banner_slot.winfo_children():
            w.destroy()
        if not warnings:
            return
        fg, bg, line = theme.badge_style("amber")
        b = ctk.CTkFrame(self.banner_slot, fg_color=bg, border_width=1, border_color=line, corner_radius=theme.R_CARD)
        b.pack(fill="x", pady=(0, theme.GAP // 2))
        ctk.CTkLabel(b, text="!", width=26, height=26, corner_radius=13, fg_color=line, text_color=fg, font=theme.font(14, True)).pack(side="left", padx=theme.PAD_CARD, pady=theme.SP3)
        ctk.CTkLabel(b, text="\n".join(warnings), text_color=fg, font=theme.font(theme.FS_CAPTION), justify="left", anchor="w", wraplength=760).pack(side="left", pady=theme.SP3)

    def _debounced_redraw(self, _):
        if self._redraw_job:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(120, self._draw_chart)

    def _draw_chart(self):
        c = self.chart; c.delete("all"); c.configure(bg=theme.PANEL)
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 160)
        if not self._monthly:
            c.create_text(w / 2, h / 2, text="Belum ada data peminjaman", fill=theme.MUTED, font=(theme.FONT_FAMILY, theme.FS_CAPTION)); return
        left, bottom, top = 40, h - 28, 16
        mx = max(n for _, n in self._monthly); mx = max(mx, 1)
        steps = mx if mx <= 4 else 4          # tick bulat; hindari label ganda saat nilai kecil
        for i in range(steps + 1):                          # garis bantu horizontal tipis + label sumbu
            y = bottom - (bottom - top) * i / steps
            c.create_line(left, y, w - 8, y, fill=theme.LINE)
            c.create_text(left - 8, y, text=str(round(mx * i / steps)), anchor="e", fill=theme.MUTED, font=(theme.FONT_FAMILY, 9))
        n = len(self._monthly); slot = (w - left - 8) / n; bw = min(64, slot * 0.55)
        for i, (m, v) in enumerate(self._monthly):
            x = left + slot * i + (slot - bw) / 2; y = bottom - (bottom - top) * v / mx
            c.create_rectangle(x, y, x + bw, bottom, fill=theme.ACCENT, outline="")
            c.create_text(x + bw / 2, y - 8, text=str(v), fill=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"))
            c.create_text(x + bw / 2, bottom + 14, text=m, fill=theme.MUTED, font=(theme.FONT_FAMILY, 9))


BOOK_FIELDS = [("title", "Judul*", "entry"), ("author", "Penulis", "entry"), ("isbn", "ISBN", "entry"),
               ("publisher", "Penerbit", "entry"), ("year", "Tahun terbit", "entry"), ("category", "Kategori", "entry"),
               ("shelf", "Rak", "entry"), ("description", "Deskripsi", "text")]


class BooksPage(Page):
    title = "Katalog Buku"
    subtitle = "Judul dan eksemplar koleksi"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("+ Tambah buku", self.add)
        tb = Toolbar(self.body); tb.pack(fill="x", pady=(0, theme.SP3))
        self.q = tb.search(self.refresh, "Judul, penulis, ISBN, barcode")
        self.view = tb.combo(["Aktif", "Diarsipkan", "Semua"], self.refresh, width=120)
        tb.button("Detail & eksemplar", self.detail); tb.button("Edit", self.edit, variant="secondary")
        tb.button("Arsipkan / Pulihkan", self.toggle_archive, variant="secondary"); tb.button("Hapus permanen", self.delete, variant="danger")
        self.table = DataTable(self.body, [("title", "Judul", 230), ("author", "Penulis", 150), ("isbn", "ISBN", 110),
                                           ("category", "Kategori", 100), ("shelf", "Rak", 60), ("copies_total", "Eksemplar", 100),
                                           ("copies_available", "Tersedia", 100), ("state", "Status", 90)], status_key="state", on_double=self.detail)
        self.table.pack(fill="both", expand=True)

    def refresh(self, **kw):
        rows = self.s.books.list_books(self.q.get(), view=self.view.get())
        for r in rows:
            r["state"] = "Aktif" if r["is_active"] else "Arsip"
        self.table.load(rows)
        self.set_subtitle(f"{len(rows)} judul ditampilkan")

    def add(self):
        def save(v):
            self.s.books.add_book(self.actor, v); self.refresh(); self.toast("Buku ditambahkan")
        FormDialog(self, "Tambah buku", BOOK_FIELDS, on_save=save)

    def edit(self):
        r = self.table.selected_one()
        if r:
            def save(v):
                self.s.books.update_book(self.actor, r["id"], v); self.refresh(); self.toast("Perubahan disimpan")
            FormDialog(self, "Edit buku", BOOK_FIELDS, r, save)

    def detail(self):
        r = self.table.selected_one()
        if r:
            self.app.show("detail", book_id=r["id"])

    def toggle_archive(self):
        r = self.table.selected_one()
        if not r:
            return
        if r["is_active"]:
            if confirm(f"Arsipkan '{r['title']}' beserta eksemplar aktifnya?", yes="Arsipkan"):
                self.s.books.archive_book(self.actor, r["id"]); self.toast("Judul diarsipkan")
        else:
            self.s.books.restore_book(self.actor, r["id"]); self.toast("Judul dipulihkan")
        self.refresh()

    def delete(self):
        r = self.table.selected_one()
        if r and confirm(f"Hapus permanen '{r['title']}'? Tindakan ini tidak dapat dibatalkan.", yes="Hapus", danger=True):
            self.s.books.delete_book(self.actor, r["id"]); self.refresh(); self.toast("Judul dihapus")


class BookDetailPage(Page):
    title = "Detail Buku"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.book_id = None
        self.add_action("← Katalog", lambda: self.app.show("books"), "secondary")
        self.info_card = Card(self.body); self.info_card.pack(fill="x", pady=(0, theme.GAP))
        self.info_grid = holder(self.info_card); self.info_grid.pack(fill="x", padx=theme.PAD_CARD + 2, pady=theme.PAD_CARD)
        tb = Toolbar(self.body); tb.pack(fill="x", pady=(0, theme.SP3))
        self.view = tb.combo(["Aktif", "Keluar koleksi", "Semua"], self.refresh, width=140)
        tb.button("+ Tambah eksemplar", self.add); tb.button("Ubah terpilih", self.edit, variant="secondary")
        tb.button("Arsipkan terpilih", self.archive, variant="secondary"); tb.button("Pulihkan", self.restore, variant="secondary")
        tb.button("Hapus terpilih", self.remove, variant="danger"); tb.button("Cetak label", self.labels, variant="ghost")
        self.table = DataTable(self.body, [("barcode", "Barcode", 90), ("inventory_code", "Kode inventaris", 130), ("shelf", "Rak", 70),
                                           ("circulation_status", "Status", 120), ("condition", "Kondisi", 110), ("archived_reason", "Alasan arsip", 170)],
                               status_key="circulation_status", multi=True)
        self.table.pack(fill="both", expand=True)

    def refresh(self, book_id=None, **kw):
        self.book_id = book_id or self.book_id
        b = self.s.books.get_book(self.book_id)
        if not b:
            return
        for w in self.info_grid.winfo_children():
            w.destroy()
        items = [("Judul", b["title"]), ("Penulis", b["author"]), ("ISBN", b["isbn"]), ("Penerbit", b["publisher"]),
                 ("Tahun", b["year"]), ("Kategori", b["category"]), ("Rak", b["shelf"]), ("Status", "Aktif" if b["is_active"] else "Diarsipkan")]
        for i, (k, v) in enumerate(items):
            f = ctk.CTkFrame(self.info_grid, fg_color="transparent"); f.grid(row=i // 4, column=i % 4, sticky="w", padx=(0, 28), pady=4)
            ctk.CTkLabel(f, text=k.upper(), font=theme.font(theme.FS_TH - 1, True), text_color=theme.MUTED).pack(anchor="w")
            ctk.CTkLabel(f, text=str(v or "-"), font=theme.font(theme.FS_BODY, k == "Judul"), text_color=theme.TEXT).pack(anchor="w")
        self.set_subtitle(b["title"])
        self.table.load(self.s.books.list_copies(self.book_id, self.view.get()))

    def add(self):
        fields = [("barcode", "Barcode (8 digit, kosong = otomatis)", "entry"), ("inventory_code", "Kode inventaris (kosong = otomatis)", "entry"),
                  ("shelf", "Rak", "entry"), ("condition", "Kondisi", "combo", CONDITIONS)]
        def save(v):
            self.s.books.add_copy(self.actor, self.book_id, v["barcode"] or None, v["inventory_code"] or None, v["shelf"] or None, v["condition"])
            self.refresh(); self.toast("Eksemplar ditambahkan")
        FormDialog(self, "Tambah eksemplar", fields, on_save=save)

    def edit(self):
        sel = self.table.selected()
        if not sel:
            return info("Pilih eksemplar terlebih dahulu.")
        if len(sel) == 1:
            r = sel[0]
            fields = [("barcode", "Barcode", "entry"), ("inventory_code", "Kode inventaris", "entry"), ("shelf", "Rak", "entry"),
                      ("condition", "Kondisi", "combo", CONDITIONS),
                      ("circulation_status", "Status (Tersedia/Perbaikan)", "combo", ["Tersedia", "Perbaikan"] if r["circulation_status"] != "Dipinjam" else ["Dipinjam"])]
            def save(v):
                w = self.s.books.update_copy(self.actor, r["id"], v)
                self.refresh()
                if w:
                    info("\n".join(w))
                else:
                    self.toast("Perubahan disimpan")
            FormDialog(self, "Ubah eksemplar", fields, r, save)
        else:
            fields = [("shelf", "Rak baru (kosong = tidak diubah)", "entry"), ("condition", "Kondisi", "combo", ["(tidak diubah)"] + CONDITIONS),
                      ("circulation_status", "Status", "combo", ["(tidak diubah)", "Tersedia", "Perbaikan"])]
            def save(v):
                data = {k: x for k, x in v.items() if x and not x.startswith("(")}
                res = self.s.books.bulk_update_copies(self.actor, [r["id"] for r in sel], data)
                self.refresh(); self._summary(res)
            FormDialog(self, f"Ubah {len(sel)} eksemplar", fields, on_save=save)

    def _summary(self, res):
        msg = f"Berhasil: {res['ok']}. Dilewati: {len(res['skipped'])}."
        if res["skipped"]:
            msg += "\n" + "\n".join(f"- #{i}: {why}" for i, why in res["skipped"][:8])
        info(msg, "Ringkasan operasi massal")

    def archive(self):
        sel = self.table.selected()
        if not sel:
            return info("Pilih eksemplar terlebih dahulu.")
        fields = [("status", "Status", "combo", ["Hilang", "Dihapusbukukan"]), ("reason", "Alasan", "combo", ARCHIVE_REASONS)]
        def save(v):
            res = self.s.books.bulk_remove_copies(self.actor, [r["id"] for r in sel], "archive", v["status"], v["reason"])
            self.refresh(); self._summary(res)
        FormDialog(self, f"Arsipkan {len(sel)} eksemplar", fields, on_save=save)

    def restore(self):
        for r in self.table.selected():
            try:
                self.s.books.restore_copy(self.actor, r["id"])
            except Exception as e:
                info(str(e))
        self.refresh()

    def remove(self):
        sel = self.table.selected()
        if sel and confirm(f"Hapus permanen {len(sel)} eksemplar? Yang berriwayat akan dilewati (gunakan Arsipkan).", yes="Hapus", danger=True):
            res = self.s.books.bulk_remove_copies(self.actor, [r["id"] for r in sel], "delete")
            self.refresh(); self._summary(res)

    def labels(self):
        self.app.show("import", book_id=self.book_id)


MEMBER_FIELDS = [("member_no", "Nomor anggota*", "entry"), ("name", "Nama*", "entry"),
                 ("member_type", "Jenis anggota", "combo", ["Umum", "Siswa", "Guru", "Staf"]),
                 ("phone", "Telepon", "entry"), ("email", "Email", "entry"), ("address", "Alamat", "text"), ("notes", "Catatan", "text")]


class MembersPage(Page):
    title = "Anggota"
    subtitle = "Data keanggotaan dan riwayat pinjam"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("+ Tambah anggota", self.add)
        tb = Toolbar(self.body); tb.pack(fill="x", pady=(0, theme.SP3))
        self.q = tb.search(self.refresh, "Nama, nomor anggota, telepon")
        self.status = tb.combo(["Semua", "Aktif", "Nonaktif"], self.refresh, width=120)
        tb.button("Edit", self.edit, variant="secondary"); tb.button("Aktif / Nonaktif", self.toggle, variant="secondary")
        tb.button("Riwayat", self.history, variant="secondary")
        self.table = DataTable(self.body, [("member_no", "No. Anggota", 110), ("name", "Nama", 220), ("member_type", "Jenis", 80),
                                           ("phone", "Telepon", 120), ("active_loans", "Pinjaman aktif", 110), ("state", "Status", 90)], status_key="state")
        self.table.pack(fill="both", expand=True)

    def refresh(self, **kw):
        rows = self.s.members.list(self.q.get(), self.status.get())
        for r in rows:
            r["state"] = "Aktif" if r["is_active"] else "Nonaktif"
        self.table.load(rows)
        self.set_subtitle(f"{len(rows)} anggota ditampilkan")

    def add(self):
        def save(v):
            self.s.members.add(self.actor, v); self.refresh(); self.toast("Anggota ditambahkan")
        FormDialog(self, "Tambah anggota", MEMBER_FIELDS, on_save=save)

    def edit(self):
        r = self.table.selected_one()
        if r:
            def save(v):
                self.s.members.update(self.actor, r["id"], v); self.refresh(); self.toast("Perubahan disimpan")
            FormDialog(self, "Edit anggota", MEMBER_FIELDS, r, save)

    def toggle(self):
        r = self.table.selected_one()
        if r:
            self.s.members.set_active(self.actor, r["id"], not r["is_active"]); self.refresh()

    def history(self):
        r = self.table.selected_one()
        if not r:
            return
        win = ctk.CTkToplevel(self); win.title(f"Riwayat {r['name']}"); win.geometry("780x400"); win.configure(fg_color=theme.BG)
        win.transient(self.winfo_toplevel())
        ctk.CTkLabel(win, text=f"Riwayat {r['name']}", font=theme.font(theme.FS_SECTION, True), text_color=theme.TEXT).pack(anchor="w", padx=theme.PAD, pady=(theme.PAD, theme.SP2))
        t = DataTable(win, [("loan_date", "Pinjam", 90), ("due_date", "Jatuh tempo", 90), ("returned_at", "Kembali", 90),
                            ("title", "Judul", 240), ("fine_amount", "Denda", 80), ("fine_status", "Status denda", 100)], status_key="fine_status")
        t.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, theme.PAD))
        t.load(self.s.members.history(r["id"]))
        win.bind("<Escape>", lambda e: win.destroy())
