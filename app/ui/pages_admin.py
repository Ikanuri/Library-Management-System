"""Stok Opname, Impor & Label, Laporan, Backup, Petugas & Log, Pengaturan."""
import tkinter as tk
from datetime import date
from tkinter import filedialog

import customtkinter as ctk

from app.services.base import ServiceError
from app.services.book_service import CONDITIONS
from . import theme
from .components import (Card, DataTable, FeedbackStrip, FormDialog, ScanEntry, StatCard, Toolbar, ask_int, caption,
                         confirm, guard, holder, info, make_button, section_label, style_entry, style_option)
from .pages_core import Page


def busy(widget):
    class _B:
        def __enter__(self_):
            widget.winfo_toplevel().configure(cursor="watch"); widget.update_idletasks()

        def __exit__(self_, *a):
            widget.winfo_toplevel().configure(cursor="")
    return _B()


def style_tabs(tv):
    tv.configure(fg_color="transparent", segmented_button_fg_color=theme.PANEL2, segmented_button_selected_color=theme.ACCENT,
                 segmented_button_selected_hover_color=theme.ACCENT_HOVER, segmented_button_unselected_color=theme.PANEL2,
                 segmented_button_unselected_hover_color=theme.PANEL3, text_color=theme.TEXT, corner_radius=theme.R_CARD)
    return tv


class OpnamePage(Page):
    title = "Stok Opname"
    subtitle = "Pemeriksaan inventaris tahunan berbasis barcode"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sid, self.last_code = None, None
        self.add_action("+ Sesi baru", self.new_session)
        self.tabs = ctk.CTkTabview(self.body); self.tabs.pack(fill="both", expand=True)
        scan_t, rec_t, hist_t = (self.tabs.add(n) for n in ("Pemeriksaan scan", "Rekonsiliasi", "Riwayat sesi"))
        style_tabs(self.tabs)
        # --- scan
        grid = ctk.CTkFrame(scan_t, fg_color="transparent"); grid.pack(fill="x", pady=(theme.SP2, theme.SP3))
        spec = [("unchecked", "Belum diperiksa", theme.MUTED), ("found", "Ditemukan", theme.OK), ("borrowed", "Dipinjam", theme.BLUE),
                ("not_found", "Belum ditemukan", theme.WARN), ("lost", "Hilang", theme.DANGER), ("extras", "Ekstra", theme.PURPLE)]
        self.cards = {}
        for i, (k, lbl, col) in enumerate(spec):
            c = StatCard(grid, lbl, color=col, small=True); c.grid(row=0, column=i, sticky="ew", padx=3); grid.columnconfigure(i, weight=1, uniform="o")
            self.cards[k] = c
        prog = ctk.CTkFrame(scan_t, fg_color="transparent"); prog.pack(fill="x", pady=(0, theme.SP3))
        self.prog_lbl = caption(prog, "Cakupan rak"); self.prog_lbl.pack(anchor="w")
        self.bar = ctk.CTkProgressBar(prog, progress_color=theme.ACCENT, fg_color=theme.PANEL3, height=8); self.bar.pack(fill="x", pady=(4, 0)); self.bar.set(0)
        row = ctk.CTkFrame(scan_t, fg_color="transparent"); row.pack(fill="x")
        self.scan = ScanEntry(row, self.do_scan, "Pindai barcode lalu Enter", on_error=self._scan_error, width=340); self.scan.pack(side="left")
        self.cond = tk.StringVar(value="Baik"); style_option(row, CONDITIONS, self.cond, 150).pack(side="left", padx=theme.SP2)
        self.extra_btn = make_button(row, "Catat sebagai ekstra", guard(self.record_extra), "secondary")
        self.strip = FeedbackStrip(scan_t); self.strip.pack(fill="x", pady=theme.SP3)
        self.scan_table = DataTable(scan_t, [("scanned_at", "Waktu", 140), ("barcode", "Barcode", 110), ("outcome", "Hasil", 200)], height=7)
        self.scan_table.pack(fill="both", expand=True)
        # --- rekonsiliasi
        tb = Toolbar(rec_t); tb.pack(fill="x", pady=(theme.SP2, theme.SP3))
        tb.button("1. Selesaikan pemeriksaan pertama", self.close_first)
        tb.button("2. Konfirmasi hilang", self.confirm_lost, variant="secondary")
        tb.button("3. Setujui & finalisasi", self.finalize, variant="danger")
        tb.button("Ekspor belum diperiksa", self.export_unchecked, variant="ghost")
        self.filter = tb.combo(["Belum diperiksa", "Belum ditemukan", "Dipinjam", "Ditemukan", "Hilang terkonfirmasi", "Ditemukan ekstra"], self.refresh_rec, width=180)
        self.rec_sum = caption(rec_t, ""); self.rec_sum.pack(anchor="w", pady=(0, theme.SP2))
        self.items = DataTable(rec_t, [("barcode_snapshot", "Barcode", 90), ("book_title_snapshot", "Judul", 260), ("location_snapshot", "Rak", 70),
                                       ("result", "Hasil", 150), ("physical_condition", "Kondisi", 110)], status_key="result", multi=True, height=9)
        self.items.pack(fill="both", expand=True)
        self.props = caption(rec_t, ""); self.props.pack(anchor="w", pady=(theme.SP2, 0))
        # --- riwayat
        tb2 = Toolbar(hist_t); tb2.pack(fill="x", pady=(theme.SP2, theme.SP3))
        tb2.button("Laporan final (Excel)", self.report_xlsx, variant="secondary")
        self.hist = DataTable(hist_t, [("year", "Tahun", 60), ("name", "Nama", 240), ("start_date", "Mulai", 90), ("end_date", "Selesai", 90), ("status", "Status", 130)], status_key="status")
        self.hist.pack(fill="both", expand=True)

    def refresh(self, **kw):
        a = self.s.opname.active_session()
        self.sid = a["id"] if a else None
        self.hist.load(self.s.opname.sessions())
        if not self.sid:
            self.set_subtitle("Tidak ada sesi aktif. Buat sesi baru dengan tombol di kanan atas.")
            for c in self.cards.values():
                c.set(0)
            self.items.load([]); self.scan_table.load([]); self.bar.set(0); self.rec_sum.configure(text=""); return
        p = self.s.opname.progress(self.sid)
        self.set_subtitle(f"{a['name']} · status {a['status']}")
        for k, c in self.cards.items():
            c.set(p[k])
        self.bar.set(p["percent"] / 100)
        self.prog_lbl.configure(text=f"Cakupan rak {p['shelf_scope']} · diperiksa {p['found']} · progres {p['percent']}% (Dipinjam {p['borrowed']} = verifikasi sirkulasi)")
        self.rec_sum.configure(text=f"Snapshot {p['snapshot']} · rusak {p['damaged']} · ekstra {p['extras']}")
        self.scan_table.load(self.s.opname.recent_scans(self.sid, 15))
        self.refresh_rec()
        self.scan.focus_soon()

    def refresh_rec(self):
        if not self.sid:
            return
        self.items.load(self.s.opname.items(self.sid, self.filter.get()))
        pr = self.s.opname.proposals(self.sid)
        self.props.configure(text="Usulan penyesuaian: " + ("; ".join(f"{p['barcode']} → {p['new_status']}" for p in pr[:6]) or "-"))

    def _scan_error(self, msg):
        self.strip.fail("Pemindaian gagal", msg)

    def do_scan(self, code):
        if not self.sid:
            raise ServiceError("Belum ada sesi aktif.")
        r = self.s.opname.scan(self.actor, self.sid, code, self.cond.get())
        self.last_code = code
        {"ok": self.strip.ok, "duplikat": self.strip.warn, "dipinjam": self.strip.note,
         "ekstra_dikenal": self.strip.warn, "tidak_dikenal": self.strip.fail}[r["status"]](r["message"])
        if r["status"] in ("tidak_dikenal", "ekstra_dikenal"):
            self.extra_btn.pack(side="left")
        else:
            self.extra_btn.pack_forget()
        self.refresh()

    def record_extra(self):
        self.s.opname.record_extra(self.actor, self.sid, self.last_code, self.cond.get())
        self.extra_btn.pack_forget(); self.strip.ok("Temuan ekstra dicatat", "Ditinjau sebelum masuk inventaris."); self.refresh()

    def new_session(self):
        y = ask_int("Stok opname baru", "Tahun stok opname", date.today().year, 1900)
        if y:
            self.s.opname.create_session(self.actor, y); self.refresh(); self.toast("Sesi opname dibuat")

    def close_first(self):
        if self.sid and confirm("Tutup pemeriksaan pertama? Yang belum dipindai menjadi 'Belum ditemukan'.", yes="Tutup"):
            n = self.s.opname.close_first_pass(self.actor, self.sid); self.refresh(); self.toast(f"{n} eksemplar menjadi Belum ditemukan", "warn")

    def confirm_lost(self):
        sel = self.items.selected()
        if sel and confirm(f"Konfirmasi {len(sel)} eksemplar hilang?", yes="Konfirmasi", danger=True):
            self.s.opname.confirm_lost(self.actor, self.sid, [r["id"] for r in sel]); self.refresh()

    def finalize(self):
        if self.sid and confirm("Setujui semua usulan penyesuaian dan finalisasi sesi? Sesi akan terkunci.", yes="Finalisasi", danger=True):
            self.s.opname.finalize(self.actor, self.sid); self.refresh(); self.toast("Sesi difinalisasi")

    def _export(self, rows, headers, name):
        from openpyxl import Workbook
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=name)
        if not path:
            return
        wb = Workbook(); ws = wb.active; ws.append(headers)
        for r in rows:
            ws.append(r)
        wb.save(path); self.toast(f"Tersimpan: {path}")

    def export_unchecked(self):
        if self.sid:
            rows = [[i["barcode_snapshot"], i["book_title_snapshot"], i["location_snapshot"], i["result"]]
                    for i in self.s.opname.items(self.sid) if i["result"] in ("Belum diperiksa", "Belum ditemukan")]
            self._export(rows, ["Barcode", "Judul", "Rak", "Hasil"], "opname_belum_diperiksa.xlsx")

    def report_xlsx(self):
        r = self.hist.selected_one()
        if r:
            rp = self.s.opname.report(r["id"]); p = rp["progress"]
            rows = [["Sesi", rp["session"]["name"]], ["Mulai", rp["session"]["start_date"]], ["Selesai", rp["session"]["end_date"] or "-"],
                    ["Snapshot", p["snapshot"]], ["Diperiksa (ditemukan)", p["found"]], ["Belum diperiksa", p["unchecked"]],
                    ["Dipinjam", p["borrowed"]], ["Belum ditemukan", p["not_found"]], ["Hilang terkonfirmasi", p["lost"]], ["Ekstra", p["extras"]]]
            rows += [[f"Rusak: {k}", v] for k, v in rp["damage_by_condition"].items()]
            rows += [[f"Penyesuaian {a['barcode']}", f"{a['old_status']} → {a['new_status']} ({a['reason']})"] for a in rp["adjustments"]]
            self._export(rows, ["Butir", "Nilai"], f"laporan_opname_{r['year']}.xlsx")


class ImportLabelPage(Page):
    title = "Impor Data dan Label"
    subtitle = "Impor koleksi dari Excel dan cetak label barcode"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.rows, self.book_id = [], None
        imp = Card(self.body, "Impor Excel", "Unduh templat, isi, lalu validasi uji coba sebelum impor"); imp.pack(fill="both", expand=True, pady=(0, theme.GAP))
        tb = Toolbar(imp); tb.pack(fill="x", padx=theme.PAD_CARD + 2, pady=(theme.SP3, theme.SP2))
        tb.button("Unduh templat", self.template, variant="secondary"); tb.button("Pilih berkas Excel", self.pick)
        tb.button("Validasi uji coba", self.check, variant="secondary"); tb.button("Impor", self.do_import)
        self.info = caption(imp, "Pilih berkas .xlsx sesuai templat."); self.info.pack(anchor="w", padx=theme.PAD_CARD + 2)
        self.table = DataTable(imp, [("row", "Baris", 60), ("status", "Hasil", 80), ("msg", "Pesan", 560)], height=8)
        self.table.pack(fill="both", expand=True, padx=theme.PAD_CARD, pady=theme.PAD_CARD)
        lab = Card(self.body, "Cetak label barcode", "Lakukan cetak uji dan uji pindai dengan scanner asli sebelum mencetak massal"); lab.pack(fill="x")
        tb2 = Toolbar(lab); tb2.pack(fill="x", padx=theme.PAD_CARD + 2, pady=theme.PAD_CARD)
        tb2.button("Label semua eksemplar", lambda: self.labels(False)); tb2.button("Label judul terpilih", lambda: self.labels(True), variant="secondary")
        tb2.button("Cetak uji 1 baris", lambda: self.labels(False, True), variant="ghost")

    def refresh(self, book_id=None, **kw):
        self.book_id = book_id

    def template(self):
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="templat_impor_libris.xlsx")
        if p:
            self.s.imports.write_template(p); self.toast("Templat tersimpan")

    def pick(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p:
            self.rows = self.s.imports.read_rows(p); self.info.configure(text=f"{len(self.rows)} baris dibaca."); self.check()

    def check(self):
        if not self.rows:
            return info("Pilih berkas terlebih dahulu.")
        rep = self.s.imports.dry_run(self.rows)
        self.table.load([{"id": i, "row": r["row"], "status": "OK" if r["status"] == "OK" else "Error", "msg": "; ".join(r["messages"])} for i, r in enumerate(rep["rows"])])
        self.info.configure(text=f"{len(rep['rows'])} baris · {rep['errors']} bermasalah · kategori baru: {', '.join(rep['new_categories']) or '-'} · rak baru: {', '.join(rep['new_shelves']) or '-'}")

    def do_import(self):
        if self.rows and confirm("Impor semua baris? Jika ada kesalahan, tidak ada data yang disimpan.", yes="Impor"):
            with busy(self):
                res = self.s.imports.commit(self.actor, self.rows)
            self.toast(f"Impor selesai: {res['books']} judul, {res['copies']} eksemplar"); self.rows = []

    def labels(self, only_book, test=False):
        copies = self.s.labels.copies_for(book_ids=[self.book_id] if only_book and self.book_id else None)
        p = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="label_libris.pdf")
        if p:
            with busy(self):
                self.s.labels.make_pdf(p, copies, test_page=test)
            self.toast(f"Label tersimpan: {p}")


class ReportsPage(Page):
    title = "Laporan"
    subtitle = "Pratinjau dan ekspor ke Excel atau PDF"

    def __init__(self, master, app):
        super().__init__(master, app)
        names = [f"{cat} › {n}" for cat, ns in self.s.reports.CATEGORIES.items() for n in ns]
        card = Card(self.body, "Pilih laporan"); card.pack(fill="x", pady=(0, theme.GAP))
        tb = Toolbar(card); tb.pack(fill="x", padx=theme.PAD_CARD + 2, pady=theme.PAD_CARD)
        self.name = tb.combo(names, lambda: None, width=340)
        self.f = style_entry(tb, placeholder_text="Dari YYYY-MM-DD", width=140); self.f.pack(side="left", padx=(0, theme.SP2))
        self.t = style_entry(tb, placeholder_text="Sampai YYYY-MM-DD", width=150); self.t.pack(side="left", padx=(0, theme.SP2))
        tb.button("Pratinjau", self.preview); tb.button("Excel", lambda: self.export("xlsx"), variant="secondary"); tb.button("PDF", lambda: self.export("pdf"), variant="secondary")
        self.holder = holder(self.body); self.holder.pack(fill="both", expand=True)
        self.table = None

    def _key(self):
        return self.name.get().split("› ")[-1]

    def preview(self):
        title, headers, rows = self.s.reports.generate(self._key(), self.f.get() or None, self.t.get() or None)
        if self.table:
            self.table.destroy()
        self.table = DataTable(self.holder, [(f"c{i}", h, 130) for i, h in enumerate(headers)], height=14); self.table.pack(fill="both", expand=True)
        self.table.load([{f"c{i}": v for i, v in enumerate(r)} for r in rows[:2000]])
        self.set_subtitle(f"{title}: {len(rows)} baris")

    def export(self, kind):
        p = filedialog.asksaveasfilename(defaultextension=f".{kind}", initialfile=f"{self._key().replace(' ', '_')}.{kind}")
        if not p:
            return
        with busy(self):
            fn = self.s.reports.export_xlsx if kind == "xlsx" else self.s.reports.export_pdf
            n = fn(p, self._key(), self.actor, self.f.get() or None, self.t.get() or None)
        self.toast(f"{n} baris diekspor ke {p}")


class BackupPage(Page):
    title = "Backup dan Restore"
    subtitle = "Salin database secara aman dan pulihkan bila perlu"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("Backup sekarang", self.backup)
        self.add_action("Backup ke lokasi lain…", self.backup_to, "secondary")
        self.add_action("Restore…", self.restore, "danger")
        self.warn_slot = holder(self.body); self.warn_slot.pack(fill="x")
        self.table = DataTable(self.body, [("created_at", "Waktu", 150), ("kind", "Jenis", 130), ("size_bytes", "Ukuran (B)", 100), ("path", "Lokasi", 460)])
        self.table.pack(fill="both", expand=True)

    def refresh(self, **kw):
        for w in self.warn_slot.winfo_children():
            w.destroy()
        w = self.s.backups.warnings()
        if w:
            fg, bg, line = theme.badge_style("amber")
            b = ctk.CTkFrame(self.warn_slot, fg_color=bg, border_width=1, border_color=line, corner_radius=theme.R_CARD); b.pack(fill="x", pady=(0, theme.GAP))
            ctk.CTkLabel(b, text="\n".join(w), text_color=fg, justify="left", anchor="w", wraplength=860, font=theme.font(theme.FS_CAPTION)).pack(anchor="w", padx=theme.PAD_CARD, pady=theme.SP3)
        self.table.load(self.s.backups.history())

    def backup(self):
        with busy(self):
            p = self.s.backups.backup(self.actor)
        self.refresh(); self.toast(f"Backup tersimpan: {p.name}")

    def backup_to(self):
        d = filedialog.askdirectory()
        if d:
            with busy(self):
                p = self.s.backups.backup(self.actor, dest_dir=d)
            self.refresh(); self.toast(f"Backup tersimpan: {p}")

    def restore(self):
        self.actor.require_admin()
        p = filedialog.askopenfilename(filetypes=[("Backup Libris", "*.db")])
        if p and confirm("Restore akan MENIMPA database aktif (database aktif dicadangkan dahulu). Lanjutkan?", yes="Restore", danger=True):
            self.s.restore(self.actor, p)
            info("Restore berhasil. Silakan login kembali."); self.app.logout()


class UsersPage(Page):
    title = "Petugas dan Log Aktivitas"
    subtitle = "Kelola akun petugas dan telusuri perubahan data"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("+ Tambah petugas", self.add)
        tb = Toolbar(self.body); tb.pack(fill="x", pady=(0, theme.SP3))
        tb.button("Aktif / Nonaktif", self.toggle, variant="secondary"); tb.button("Reset password", self.reset_pw, variant="secondary")
        tb.button("Ekspor log", self.export_log, variant="ghost")
        self.users = DataTable(self.body, [("username", "Username", 130), ("full_name", "Nama", 220), ("role", "Peran", 90), ("state", "Status", 90)], status_key="state", height=5)
        self.users.pack(fill="x", pady=(0, theme.GAP))
        section_label(self.body, "Log aktivitas").pack(anchor="w", pady=(0, theme.SP2))
        self.log = DataTable(self.body, [("created_at", "Waktu", 140), ("username", "Pengguna", 100), ("entity", "Entitas", 90), ("entity_id", "ID", 60),
                                         ("action", "Aksi", 120), ("new_value", "Nilai baru", 360)], height=10)
        self.log.pack(fill="both", expand=True)

    def refresh(self, **kw):
        rows = self.s.auth.list_users()
        for r in rows:
            r["state"] = "Aktif" if r["is_active"] else "Nonaktif"
        self.users.load(rows); self.log.load(self.s.audit.list(300))

    def add(self):
        fields = [("username", "Username", "entry"), ("full_name", "Nama lengkap", "entry"), ("password", "Password (min. 6)", "password"), ("role", "Peran", "combo", ["staff", "admin"])]
        def save(v):
            self.s.auth.create_user(self.actor, v["username"], v["password"], v["full_name"], v["role"]); self.refresh(); self.toast("Petugas ditambahkan")
        FormDialog(self, "Tambah petugas", fields, on_save=save)

    def toggle(self):
        r = self.users.selected_one()
        if r:
            self.s.auth.set_active(self.actor, r["id"], not r["is_active"]); self.refresh()

    def reset_pw(self):
        r = self.users.selected_one()
        if r:
            def save(v):
                self.s.auth.change_password(self.actor, r["id"], v["password"]); self.toast("Password diperbarui")
            FormDialog(self, f"Reset password {r['username']}", [("password", "Password baru", "password")], on_save=save)

    def export_log(self):
        from openpyxl import Workbook
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="log_aktivitas.xlsx")
        if p:
            wb = Workbook(); ws = wb.active; ws.append(["Waktu", "Pengguna", "Entitas", "ID", "Aksi", "Lama", "Baru"])
            for a in self.s.audit.list(100000):
                ws.append([a["created_at"], a["username"], a["entity"], a["entity_id"], a["action"], a["old_value"], a["new_value"]])
            wb.save(p); self.toast("Log diekspor")


class SettingsPage(Page):
    title = "Pengaturan"
    subtitle = "Kebijakan peminjaman, denda, backup, dan tampilan"
    GROUPS = [
        ("Kebijakan peminjaman", [("loan_days", "Durasi pinjam (hari)"), ("max_loans_per_member", "Batas pinjam per anggota")]),
        ("Denda", [("fine_rate", "Tarif denda per hari (Rp)"), ("fine_cap", "Batas maksimum denda (Rp, 0 = tanpa batas)"), ("grace_days", "Masa tenggang (hari)")]),
        ("Backup", [("backup_retention", "Jumlah salinan backup disimpan"), ("backup_dir", "Folder backup (kosong = bawaan)")]),
        ("Laporan", [("library_name", "Nama perpustakaan (kop laporan)")]),
    ]

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("Simpan", self.save)
        scroll = ctk.CTkScrollableFrame(self.body, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        self.vars = {}
        for title, fields in self.GROUPS:
            card = Card(scroll, title); card.pack(fill="x", pady=(0, theme.GAP))
            for k, label in fields:
                r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=theme.PAD_CARD + 2, pady=theme.SP2)
                ctk.CTkLabel(r, text=label, width=320, anchor="w", font=theme.font(theme.FS_BODY), text_color=theme.SOFT).pack(side="left")
                self.vars[k] = tk.StringVar(); style_entry(r, textvariable=self.vars[k], width=280).pack(side="left")
            ctk.CTkLabel(card, text="", height=6).pack()
        pol = Card(scroll, "Kebijakan buku hilang / rusak berat"); pol.pack(fill="x", pady=(0, theme.GAP))
        self.policy = tk.StringVar()
        style_option(pol, ["Ganti buku", "Bayar harga buku", "Ditentukan petugas"], self.policy, 280).pack(anchor="w", padx=theme.PAD_CARD + 2, pady=theme.PAD_CARD)
        look = Card(scroll, "Tampilan", "Tema diterapkan segera setelah disimpan"); look.pack(fill="x", pady=(0, theme.GAP))
        self.theme_var = tk.StringVar()
        style_option(look, ["Gelap", "Terang"], self.theme_var, 200).pack(anchor="w", padx=theme.PAD_CARD + 2, pady=theme.PAD_CARD)

    def refresh(self, **kw):
        for k, v in self.vars.items():
            v.set(self.s.settings.get(k, ""))
        self.policy.set(self.s.settings.get("lost_policy", "Ditentukan petugas"))
        self.theme_var.set("Terang" if self.s.settings.get("theme", "dark") == "light" else "Gelap")

    def save(self):
        self.actor.require_admin()
        for k, v in self.vars.items():
            self.s.settings.set(k, v.get(), self.actor)
        self.s.settings.set("lost_policy", self.policy.get(), self.actor)
        mode = "light" if self.theme_var.get() == "Terang" else "dark"
        changed = mode != self.s.settings.get("theme", "dark")
        self.s.settings.set("theme", mode, self.actor)
        if changed:
            self.app.apply_theme(mode)
        else:
            self.toast("Pengaturan disimpan")
