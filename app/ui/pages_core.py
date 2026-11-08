"""Dashboard, Koleksi Buku, Detail Buku, Anggota."""
import tkinter as tk

import customtkinter as ctk

from app.services.book_service import ARCHIVE_REASONS, CONDITIONS
from . import theme
from .components import Card, DataTable, FormDialog, StatCard, Toolbar, confirm, guard, info


class Page(ctk.CTkFrame):
    title = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG)
        self.app, self.s = app, app.services
        ctk.CTkLabel(self, text=self.title, font=theme.font(22, True), text_color=theme.TEXT).pack(anchor="w", padx=20, pady=(16, 8))

    @property
    def actor(self):
        return self.app.actor

    def refresh(self, **kw):
        pass


class DashboardPage(Page):
    title = "Dashboard"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.warn = ctk.CTkLabel(self, text="", text_color=theme.WARN, justify="left", wraplength=900)
        self.warn.pack(anchor="w", padx=20)
        grid = ctk.CTkFrame(self, fg_color="transparent"); grid.pack(fill="x", padx=14)
        self.cards = {}
        spec = [("titles", "Total judul"), ("copies", "Total eksemplar"), ("available", "Tersedia"), ("borrowed", "Dipinjam"),
                ("members", "Anggota aktif"), ("loans_today", "Pinjam hari ini"), ("overdue", "Terlambat"), ("fine", "Denda belum lunas")]
        for i, (k, lbl) in enumerate(spec):
            c = StatCard(grid, lbl); c.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")
            grid.columnconfigure(i % 4, weight=1); self.cards[k] = c
        self.chart = tk.Canvas(self, height=200, bg=theme.PANEL, highlightthickness=0)
        self.chart.pack(fill="x", padx=20, pady=10)
        self.opname = ctk.CTkLabel(self, text="", font=theme.font(13), text_color=theme.TEXT)
        self.opname.pack(anchor="w", padx=20)

    def refresh(self, **kw):
        d = self.s.reports.dashboard()
        for k in ("titles", "copies", "available", "borrowed", "members", "loans_today", "overdue"):
            self.cards[k].set(d[k])
        self.cards["fine"].set(theme.rupiah(d["fines"]["outstanding"]))
        self.warn.configure(text="\n".join("⚠ " + w for w in self.s.backups.warnings()))
        self._chart(d["monthly"])
        o = d["opname"]
        self.opname.configure(text=(f"Stok opname '{o['session']['name']}': {o['percent']}% cakupan rak diperiksa "
                                    f"({o['found']}/{o['shelf_scope']}), dipinjam {o['borrowed']}") if o else "")

    def _chart(self, monthly):
        c = self.chart; c.delete("all")
        c.create_text(12, 12, anchor="w", text="Peminjaman per bulan", font=("Segoe UI", 11, "bold"), fill=theme.TEXT)
        if not monthly:
            c.create_text(300, 100, text="Belum ada data peminjaman", fill=theme.MUTED); return
        w = max(c.winfo_width(), 600); mx = max(n for _, n in monthly)
        bw = min(70, (w - 80) // len(monthly) - 12)
        for i, (m, n) in enumerate(monthly):
            x = 50 + i * (bw + 14); h = int(120 * n / mx)
            c.create_rectangle(x, 160 - h, x + bw, 160, fill=theme.ACCENT, outline="")
            c.create_text(x + bw / 2, 150 - h, text=str(n), font=("Segoe UI", 9), fill=theme.TEXT)
            c.create_text(x + bw / 2, 175, text=m, font=("Segoe UI", 9), fill=theme.MUTED)


BOOK_FIELDS = [("title", "Judul*", "entry"), ("author", "Penulis", "entry"), ("isbn", "ISBN", "entry"),
               ("publisher", "Penerbit", "entry"), ("year", "Tahun terbit", "entry"), ("category", "Kategori", "entry"),
               ("shelf", "Rak", "entry"), ("description", "Deskripsi", "text")]


class BooksPage(Page):
    title = "Koleksi Buku"

    def __init__(self, master, app):
        super().__init__(master, app)
        tb = Toolbar(self); tb.pack(fill="x", padx=20)
        self.q = tb.search(self.refresh, "Judul, penulis, ISBN, barcode, kode inventaris")
        self.view = tb.combo(["Aktif", "Diarsipkan", "Semua"], self.refresh, width=110)
        tb.button("Tambah buku", self.add); tb.button("Edit", self.edit, secondary=True)
        tb.button("Detail & eksemplar", self.detail, secondary=True)
        tb.button("Arsipkan / Pulihkan", self.toggle_archive, secondary=True); tb.button("Hapus permanen", self.delete, danger=True)
        self.table = DataTable(self, [("title", "Judul", 280), ("author", "Penulis", 160), ("isbn", "ISBN", 120),
                                      ("category", "Kategori", 100), ("shelf", "Rak", 70),
                                      ("copies_total", "Eksemplar", 80), ("copies_available", "Tersedia", 70),
                                      ("state", "Status", 80)], on_double=self.detail)
        self.table.pack(fill="both", expand=True, padx=20, pady=10)

    def refresh(self, **kw):
        rows = self.s.books.list_books(self.q.get(), view=self.view.get())
        for r in rows:
            r["state"] = "Aktif" if r["is_active"] else "Arsip"
        self.table.load(rows)

    def add(self):
        def save(v):
            self.s.books.add_book(self.actor, v); self.refresh()
        FormDialog(self, "Tambah buku", BOOK_FIELDS, on_save=save)

    def edit(self):
        r = self.table.selected_one()
        if r:
            def save(v):
                self.s.books.update_book(self.actor, r["id"], v); self.refresh()
            FormDialog(self, "Edit buku", BOOK_FIELDS, r, save)

    def detail(self):
        r = self.table.selected_one()
        if r:
            self.app.show("detail", book_id=r["id"])

    def toggle_archive(self):
        r = self.table.selected_one()
        if not r: return
        if r["is_active"]:
            if confirm(f"Arsipkan '{r['title']}' beserta eksemplar aktifnya?"):
                self.s.books.archive_book(self.actor, r["id"])
        else:
            self.s.books.restore_book(self.actor, r["id"])
        self.refresh()

    def delete(self):
        r = self.table.selected_one()
        if r and confirm(f"Hapus permanen '{r['title']}'? Tindakan ini tidak dapat dibatalkan."):
            self.s.books.delete_book(self.actor, r["id"]); self.refresh()


class BookDetailPage(Page):
    title = "Detail Buku"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.book_id = None
        self.head = ctk.CTkLabel(self, text="", font=theme.font(14), justify="left", anchor="w")
        self.head.pack(anchor="w", padx=20)
        tb = Toolbar(self); tb.pack(fill="x", padx=20, pady=6)
        tb.button("← Koleksi", lambda: self.app.show("books"), secondary=True)
        self.view = tb.combo(["Aktif", "Keluar koleksi", "Semua"], self.refresh, width=130)
        tb.button("Tambah eksemplar", self.add); tb.button("Ubah terpilih", self.edit, secondary=True)
        tb.button("Arsipkan terpilih", self.archive, secondary=True); tb.button("Pulihkan", self.restore, secondary=True)
        tb.button("Hapus terpilih", self.remove, danger=True); tb.button("Cetak label", self.labels, secondary=True)
        self.table = DataTable(self, [("barcode", "Barcode", 90), ("inventory_code", "Kode inventaris", 130),
                                      ("shelf", "Rak", 70), ("circulation_status", "Status", 110),
                                      ("condition", "Kondisi", 110), ("archived_reason", "Alasan arsip", 150)],
                               status_key="circulation_status", multi=True)
        self.table.pack(fill="both", expand=True, padx=20, pady=6)

    def refresh(self, book_id=None, **kw):
        self.book_id = book_id or self.book_id
        b = self.s.books.get_book(self.book_id)
        if not b: return
        self.head.configure(text=f"{b['title']}\n{b['author'] or '-'} · ISBN {b['isbn'] or '-'} · {b['category'] or '-'} · Rak {b['shelf'] or '-'}"
                                 + ("   [DIARSIPKAN]" if not b["is_active"] else ""))
        self.table.load(self.s.books.list_copies(self.book_id, self.view.get()))

    def add(self):
        fields = [("barcode", "Barcode (8 digit, kosong = otomatis)", "entry"), ("inventory_code", "Kode inventaris (kosong = otomatis)", "entry"),
                  ("shelf", "Rak", "entry"), ("condition", "Kondisi", "combo", CONDITIONS)]
        def save(v):
            self.s.books.add_copy(self.actor, self.book_id, v["barcode"] or None, v["inventory_code"] or None, v["shelf"] or None, v["condition"])
            self.refresh()
        FormDialog(self, "Tambah eksemplar", fields, on_save=save)

    def edit(self):
        sel = self.table.selected()
        if not sel: return info("Pilih eksemplar terlebih dahulu.")
        if len(sel) == 1:
            r = sel[0]
            fields = [("barcode", "Barcode", "entry"), ("inventory_code", "Kode inventaris", "entry"), ("shelf", "Rak", "entry"),
                      ("condition", "Kondisi", "combo", CONDITIONS),
                      ("circulation_status", "Status (Tersedia/Perbaikan)", "combo", ["Tersedia", "Perbaikan"] if r["circulation_status"] != "Dipinjam" else ["Dipinjam"])]
            def save(v):
                w = self.s.books.update_copy(self.actor, r["id"], v)
                self.refresh()
                if w: info("\n".join(w))
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
        info(msg)

    def archive(self):
        sel = self.table.selected()
        if not sel: return info("Pilih eksemplar terlebih dahulu.")
        fields = [("status", "Status", "combo", ["Hilang", "Dihapusbukukan"]), ("reason", "Alasan", "combo", ARCHIVE_REASONS)]
        def save(v):
            res = self.s.books.bulk_remove_copies(self.actor, [r["id"] for r in sel], "archive", v["status"], v["reason"])
            self.refresh(); self._summary(res)
        FormDialog(self, f"Arsipkan {len(sel)} eksemplar", fields, on_save=save)

    def restore(self):
        for r in self.table.selected():
            try: self.s.books.restore_copy(self.actor, r["id"])
            except Exception as e: info(str(e))
        self.refresh()

    def remove(self):
        sel = self.table.selected()
        if sel and confirm(f"Hapus permanen {len(sel)} eksemplar? Yang berriwayat akan dilewati (gunakan Arsipkan)."):
            res = self.s.books.bulk_remove_copies(self.actor, [r["id"] for r in sel], "delete")
            self.refresh(); self._summary(res)

    def labels(self):
        self.app.show("import", book_id=self.book_id)


MEMBER_FIELDS = [("member_no", "Nomor anggota*", "entry"), ("name", "Nama*", "entry"),
                 ("member_type", "Jenis anggota", "combo", ["Umum", "Siswa", "Guru", "Staf"]),
                 ("phone", "Telepon", "entry"), ("email", "Email", "entry"), ("address", "Alamat", "text"), ("notes", "Catatan", "text")]


class MembersPage(Page):
    title = "Anggota"

    def __init__(self, master, app):
        super().__init__(master, app)
        tb = Toolbar(self); tb.pack(fill="x", padx=20)
        self.q = tb.search(self.refresh, "Nama, nomor anggota, telepon")
        self.status = tb.combo(["Semua", "Aktif", "Nonaktif"], self.refresh, width=110)
        tb.button("Tambah", self.add); tb.button("Edit", self.edit, secondary=True)
        tb.button("Aktif/Nonaktif", self.toggle, secondary=True); tb.button("Riwayat", self.history, secondary=True)
        self.table = DataTable(self, [("member_no", "No. Anggota", 110), ("name", "Nama", 200), ("member_type", "Jenis", 80),
                                      ("phone", "Telepon", 110), ("active_loans", "Pinjaman aktif", 100), ("state", "Status", 80)])
        self.table.pack(fill="both", expand=True, padx=20, pady=10)

    def refresh(self, **kw):
        rows = self.s.members.list(self.q.get(), self.status.get())
        for r in rows:
            r["state"] = "Aktif" if r["is_active"] else "Nonaktif"
        self.table.load(rows)

    def add(self):
        def save(v):
            self.s.members.add(self.actor, v); self.refresh()
        FormDialog(self, "Tambah anggota", MEMBER_FIELDS, on_save=save)

    def edit(self):
        r = self.table.selected_one()
        if r:
            def save(v):
                self.s.members.update(self.actor, r["id"], v); self.refresh()
            FormDialog(self, "Edit anggota", MEMBER_FIELDS, r, save)

    def toggle(self):
        r = self.table.selected_one()
        if r:
            self.s.members.set_active(self.actor, r["id"], not r["is_active"]); self.refresh()

    def history(self):
        r = self.table.selected_one()
        if not r: return
        win = ctk.CTkToplevel(self); win.title(f"Riwayat {r['name']}"); win.geometry("760x380")
        t = DataTable(win, [("loan_date", "Pinjam", 90), ("due_date", "Jatuh tempo", 90), ("returned_at", "Kembali", 90),
                            ("title", "Judul", 260), ("fine_amount", "Denda", 80), ("fine_status", "Status denda", 100)])
        t.pack(fill="both", expand=True, padx=10, pady=10)
        t.load(self.s.members.history(r["id"]))
