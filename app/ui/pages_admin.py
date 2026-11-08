"""Stok Opname, Impor & Label, Laporan, Backup, Petugas & Log, Pengaturan."""
import tkinter as tk
from datetime import date
from tkinter import filedialog

import customtkinter as ctk

from app.services.base import ServiceError
from app.services.book_service import CONDITIONS
from . import theme
from .components import ask_int, Card, DataTable, FormDialog, ScanEntry, StatCard, Toolbar, confirm, guard, info
from .pages_core import Page


def busy(widget):
    class _B:
        def __enter__(self_):
            widget.winfo_toplevel().configure(cursor="watch"); widget.update_idletasks()
        def __exit__(self_, *a):
            widget.winfo_toplevel().configure(cursor="")
    return _B()


class OpnamePage(Page):
    title = "Stok Opname"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sid = None
        self.tabs = ctk.CTkTabview(self, fg_color=theme.BG); self.tabs.pack(fill="both", expand=True, padx=14)
        scan_t, rec_t, hist_t = (self.tabs.add(n) for n in ("Pemeriksaan scan", "Rekonsiliasi", "Riwayat sesi"))
        # --- scan
        self.stats = ctk.CTkLabel(scan_t, text="", justify="left", font=theme.font(12)); self.stats.pack(anchor="w")
        self.bar = ctk.CTkProgressBar(scan_t); self.bar.pack(fill="x", pady=4); self.bar.set(0)
        row = ctk.CTkFrame(scan_t, fg_color="transparent"); row.pack(fill="x", pady=6)
        self.scan = ScanEntry(row, self.do_scan, width=260); self.scan.pack(side="left")
        self.cond = tk.StringVar(value="Baik")
        ctk.CTkOptionMenu(row, values=CONDITIONS, variable=self.cond, width=140).pack(side="left", padx=8)
        self.extra_btn = ctk.CTkButton(row, text="Catat sebagai ekstra", command=guard(self.record_extra), fg_color=theme.WARN)
        self.msg = ctk.CTkLabel(scan_t, text="", anchor="w", justify="left"); self.msg.pack(anchor="w")
        self.last_code = None
        self.scan_table = DataTable(scan_t, [("scanned_at", "Waktu", 130), ("barcode", "Barcode", 100), ("outcome", "Hasil", 180)], height=8)
        self.scan_table.pack(fill="both", expand=True, pady=6)
        # --- rekonsiliasi
        self.rec_sum = ctk.CTkLabel(rec_t, text="", justify="left"); self.rec_sum.pack(anchor="w")
        tb = Toolbar(rec_t); tb.pack(fill="x", pady=4)
        tb.button("1. Selesaikan pemeriksaan pertama", self.close_first)
        tb.button("2. Konfirmasi hilang (terpilih)", self.confirm_lost, secondary=True)
        tb.button("3. Setujui & finalisasi", self.finalize)
        tb.button("Ekspor belum diperiksa", self.export_unchecked, secondary=True)
        self.filter = tb.combo(["Belum diperiksa", "Belum ditemukan", "Dipinjam", "Ditemukan", "Hilang terkonfirmasi", "Ditemukan ekstra"],
                               self.refresh_rec, width=170)
        self.items = DataTable(rec_t, [("barcode_snapshot", "Barcode", 90), ("book_title_snapshot", "Judul", 260), ("location_snapshot", "Rak", 70),
                                       ("result", "Hasil", 140), ("physical_condition", "Kondisi", 110)], status_key="result", multi=True, height=9)
        self.items.pack(fill="both", expand=True)
        self.props = ctk.CTkLabel(rec_t, text="", justify="left", text_color=theme.MUTED, anchor="w"); self.props.pack(anchor="w")
        # --- riwayat
        tb2 = Toolbar(hist_t); tb2.pack(fill="x")
        tb2.button("Sesi baru", self.new_session); tb2.button("Laporan final (Excel)", self.report_xlsx, secondary=True)
        self.hist = DataTable(hist_t, [("year", "Tahun", 60), ("name", "Nama", 220), ("start_date", "Mulai", 90),
                                       ("end_date", "Selesai", 90), ("status", "Status", 120)], status_key="status")
        self.hist.pack(fill="both", expand=True, pady=6)

    def refresh(self, **kw):
        a = self.s.opname.active_session()
        self.sid = a["id"] if a else None
        self.hist.load(self.s.opname.sessions())
        if not self.sid:
            self.stats.configure(text="Tidak ada sesi aktif. Buat sesi baru pada tab Riwayat sesi.")
            self.rec_sum.configure(text=""); self.items.load([]); self.scan_table.load([]); self.bar.set(0); return
        p = self.s.opname.progress(self.sid)
        txt = (f"{a['name']} · status {a['status']}\nBelum diperiksa {p['unchecked']} · Ditemukan {p['found']} (rusak {p['damaged']}) · "
               f"Dipinjam {p['borrowed']} (verifikasi sirkulasi) · Belum ditemukan {p['not_found']} · Hilang {p['lost']} · Ekstra {p['extras']}\n"
               f"Cakupan rak {p['shelf_scope']} · progres {p['percent']}%")
        self.stats.configure(text=txt); self.rec_sum.configure(text=txt); self.bar.set(p["percent"] / 100)
        self.scan_table.load(self.s.opname.recent_scans(self.sid, 15))
        self.refresh_rec()

    def refresh_rec(self):
        if not self.sid: return
        self.items.load(self.s.opname.items(self.sid, self.filter.get()))
        pr = self.s.opname.proposals(self.sid)
        self.props.configure(text="Usulan penyesuaian: " + ("; ".join(f"{p['barcode']} → {p['new_status']}" for p in pr[:6]) or "-"))

    def do_scan(self, code):
        if not self.sid: raise ServiceError("Belum ada sesi aktif.")
        r = self.s.opname.scan(self.actor, self.sid, code, self.cond.get())
        colors = {"ok": theme.OK, "duplikat": theme.WARN, "dipinjam": theme.ACCENT, "ekstra_dikenal": theme.WARN, "tidak_dikenal": theme.DANGER}
        self.msg.configure(text=r["message"], text_color=colors[r["status"]])
        self.last_code = code
        if r["status"] in ("tidak_dikenal", "ekstra_dikenal"): self.extra_btn.pack(side="left")
        else: self.extra_btn.pack_forget()
        self.refresh()

    def record_extra(self):
        self.s.opname.record_extra(self.actor, self.sid, self.last_code, self.cond.get())
        self.extra_btn.pack_forget(); self.msg.configure(text="Temuan ekstra dicatat untuk ditinjau.", text_color=theme.OK); self.refresh()

    def new_session(self):
        y = ask_int("Stok opname baru", "Tahun stok opname", date.today().year, 1900)
        if y: self.s.opname.create_session(self.actor, y); self.refresh()

    def close_first(self):
        if self.sid and confirm("Tutup pemeriksaan pertama? Yang belum dipindai menjadi 'Belum ditemukan'."):
            n = self.s.opname.close_first_pass(self.actor, self.sid); info(f"{n} eksemplar menjadi Belum ditemukan."); self.refresh()

    def confirm_lost(self):
        sel = self.items.selected()
        if sel and confirm(f"Konfirmasi {len(sel)} eksemplar hilang?"):
            self.s.opname.confirm_lost(self.actor, self.sid, [r["id"] for r in sel]); self.refresh()

    def finalize(self):
        if self.sid and confirm("Setujui semua usulan penyesuaian dan finalisasi sesi? Sesi akan terkunci."):
            self.s.opname.finalize(self.actor, self.sid); info("Sesi difinalisasi."); self.refresh()

    def _export(self, rows, headers, name):
        from openpyxl import Workbook
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=name)
        if not path: return
        wb = Workbook(); ws = wb.active; ws.append(headers)
        for r in rows: ws.append(r)
        wb.save(path); info(f"Tersimpan: {path}")

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

    def __init__(self, master, app):
        super().__init__(master, app)
        self.rows, self.book_id = [], None
        tb = Toolbar(self); tb.pack(fill="x", padx=20)
        tb.button("Unduh templat", self.template, secondary=True); tb.button("Pilih berkas Excel", self.pick)
        tb.button("Validasi uji coba", self.check, secondary=True); tb.button("Impor", self.do_import)
        self.info = ctk.CTkLabel(self, text="Pilih berkas .xlsx sesuai templat.", justify="left", anchor="w"); self.info.pack(anchor="w", padx=20)
        self.table = DataTable(self, [("row", "Baris", 50), ("status", "Hasil", 70), ("msg", "Pesan", 600)], height=9)
        self.table.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(self, text="Cetak label barcode", font=theme.font(15, True)).pack(anchor="w", padx=20, pady=(10, 0))
        tb2 = Toolbar(self); tb2.pack(fill="x", padx=20, pady=4)
        tb2.button("Label semua eksemplar", lambda: self.labels(False)); tb2.button("Label judul terpilih", lambda: self.labels(True), secondary=True)
        tb2.button("Cetak uji 1 baris", lambda: self.labels(False, True), secondary=True)
        self.lbl_info = ctk.CTkLabel(self, text="Lakukan cetak uji dan uji pindai dengan scanner asli sebelum mencetak massal.", text_color=theme.MUTED)
        self.lbl_info.pack(anchor="w", padx=20)

    def refresh(self, book_id=None, **kw):
        self.book_id = book_id

    def template(self):
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="templat_impor_libris.xlsx")
        if p: self.s.imports.write_template(p); info("Templat tersimpan.")

    def pick(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p:
            self.rows = self.s.imports.read_rows(p); self.info.configure(text=f"{len(self.rows)} baris dibaca. Jalankan validasi uji coba."); self.check()

    def check(self):
        if not self.rows: return info("Pilih berkas terlebih dahulu.")
        rep = self.s.imports.dry_run(self.rows)
        self.table.load([{"id": i, "row": r["row"], "status": r["status"], "msg": "; ".join(r["messages"])} for i, r in enumerate(rep["rows"])])
        self.info.configure(text=f"{len(rep['rows'])} baris · {rep['errors']} bermasalah · kategori baru: {', '.join(rep['new_categories']) or '-'} · rak baru: {', '.join(rep['new_shelves']) or '-'}")

    def do_import(self):
        if self.rows and confirm("Impor semua baris? Jika ada kesalahan, tidak ada data yang disimpan."):
            with busy(self):
                res = self.s.imports.commit(self.actor, self.rows)
            info(f"Impor selesai: {res['books']} judul, {res['copies']} eksemplar."); self.rows = []

    def labels(self, only_book, test=False):
        copies = self.s.labels.copies_for(book_ids=[self.book_id] if only_book and self.book_id else None)
        p = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="label_libris.pdf")
        if p:
            with busy(self):
                self.s.labels.make_pdf(p, copies, test_page=test)
            info(f"Label tersimpan: {p}")


class ReportsPage(Page):
    title = "Laporan"

    def __init__(self, master, app):
        super().__init__(master, app)
        names = [f"{cat} › {n}" for cat, ns in self.s.reports.CATEGORIES.items() for n in ns]
        tb = Toolbar(self); tb.pack(fill="x", padx=20)
        self.name = tb.combo(names, lambda: None, width=330)
        self.f = tk.StringVar(); self.t = tk.StringVar()
        ctk.CTkEntry(tb, textvariable=self.f, placeholder_text="Dari YYYY-MM-DD", width=130).pack(side="left", padx=4)
        ctk.CTkEntry(tb, textvariable=self.t, placeholder_text="Sampai YYYY-MM-DD", width=130).pack(side="left", padx=4)
        tb.button("Pratinjau", self.preview); tb.button("Excel", lambda: self.export("xlsx"), secondary=True); tb.button("PDF", lambda: self.export("pdf"), secondary=True)
        self.holder = ctk.CTkFrame(self, fg_color="transparent"); self.holder.pack(fill="both", expand=True, padx=20, pady=8)
        self.table = None

    def _key(self):
        return self.name.get().split("› ")[-1]

    def preview(self):
        title, headers, rows = self.s.reports.generate(self._key(), self.f.get() or None, self.t.get() or None)
        if self.table: self.table.destroy()
        cols = [(f"c{i}", h, 130) for i, h in enumerate(headers)]
        self.table = DataTable(self.holder, cols, height=16); self.table.pack(fill="both", expand=True)
        self.table.load([{f"c{i}": v for i, v in enumerate(r)} for r in rows[:2000]])

    def export(self, kind):
        p = filedialog.asksaveasfilename(defaultextension=f".{kind}", initialfile=f"{self._key().replace(' ', '_')}.{kind}")
        if not p: return
        with busy(self):
            fn = self.s.reports.export_xlsx if kind == "xlsx" else self.s.reports.export_pdf
            n = fn(p, self._key(), self.actor, self.f.get() or None, self.t.get() or None)
        info(f"{n} baris diekspor ke {p}")


class BackupPage(Page):
    title = "Backup dan Restore"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.warn = ctk.CTkLabel(self, text="", text_color=theme.WARN, justify="left", anchor="w", wraplength=900); self.warn.pack(anchor="w", padx=20)
        tb = Toolbar(self); tb.pack(fill="x", padx=20, pady=6)
        tb.button("Backup sekarang", self.backup); tb.button("Backup ke lokasi lain…", self.backup_to, secondary=True)
        tb.button("Restore dari berkas…", self.restore, danger=True)
        self.table = DataTable(self, [("created_at", "Waktu", 140), ("kind", "Jenis", 90), ("size_bytes", "Ukuran (B)", 90), ("path", "Lokasi", 460)])
        self.table.pack(fill="both", expand=True, padx=20, pady=8)

    def refresh(self, **kw):
        self.warn.configure(text="\n".join("⚠ " + w for w in self.s.backups.warnings()))
        self.table.load(self.s.backups.history())

    def backup(self):
        with busy(self): p = self.s.backups.backup(self.actor)
        info(f"Backup tersimpan: {p}"); self.refresh()

    def backup_to(self):
        d = filedialog.askdirectory()
        if d:
            with busy(self): p = self.s.backups.backup(self.actor, dest_dir=d)
            info(f"Backup tersimpan: {p}"); self.refresh()

    def restore(self):
        self.actor.require_admin()
        p = filedialog.askopenfilename(filetypes=[("Backup Libris", "*.db")])
        if p and confirm("Restore akan MENIMPA database aktif (database aktif dicadangkan dahulu). Lanjutkan?"):
            self.s.restore(self.actor, p)
            info("Restore berhasil. Silakan login kembali."); self.app.logout()


class UsersPage(Page):
    title = "Petugas dan Log Aktivitas"

    def __init__(self, master, app):
        super().__init__(master, app)
        tb = Toolbar(self); tb.pack(fill="x", padx=20)
        tb.button("Tambah petugas", self.add); tb.button("Aktif/Nonaktif", self.toggle, secondary=True)
        tb.button("Reset password", self.reset_pw, secondary=True); tb.button("Ekspor log", self.export_log, secondary=True)
        self.users = DataTable(self, [("username", "Username", 120), ("full_name", "Nama", 200), ("role", "Peran", 90), ("state", "Status", 80)], height=5)
        self.users.pack(fill="x", padx=20, pady=6)
        self.log = DataTable(self, [("created_at", "Waktu", 130), ("username", "Pengguna", 90), ("entity", "Entitas", 90), ("entity_id", "ID", 60),
                                    ("action", "Aksi", 110), ("new_value", "Nilai baru", 380)], height=12)
        self.log.pack(fill="both", expand=True, padx=20, pady=6)

    def refresh(self, **kw):
        rows = self.s.auth.list_users()
        for r in rows: r["state"] = "Aktif" if r["is_active"] else "Nonaktif"
        self.users.load(rows); self.log.load(self.s.audit.list(300))

    def add(self):
        fields = [("username", "Username", "entry"), ("full_name", "Nama lengkap", "entry"), ("password", "Password (min. 6)", "password"),
                  ("role", "Peran", "combo", ["staff", "admin"])]
        def save(v):
            self.s.auth.create_user(self.actor, v["username"], v["password"], v["full_name"], v["role"]); self.refresh()
        FormDialog(self, "Tambah petugas", fields, on_save=save)

    def toggle(self):
        r = self.users.selected_one()
        if r: self.s.auth.set_active(self.actor, r["id"], not r["is_active"]); self.refresh()

    def reset_pw(self):
        r = self.users.selected_one()
        if r:
            def save(v): self.s.auth.change_password(self.actor, r["id"], v["password"])
            FormDialog(self, f"Reset password {r['username']}", [("password", "Password baru", "password")], on_save=save)

    def export_log(self):
        from openpyxl import Workbook
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="log_aktivitas.xlsx")
        if p:
            wb = Workbook(); ws = wb.active; ws.append(["Waktu", "Pengguna", "Entitas", "ID", "Aksi", "Lama", "Baru"])
            for a in self.s.audit.list(100000):
                ws.append([a["created_at"], a["username"], a["entity"], a["entity_id"], a["action"], a["old_value"], a["new_value"]])
            wb.save(p); info("Log diekspor.")


class SettingsPage(Page):
    title = "Pengaturan"
    FIELDS = [("library_name", "Nama perpustakaan"), ("loan_days", "Durasi pinjam (hari)"), ("fine_rate", "Tarif denda per hari (Rp)"),
              ("fine_cap", "Batas maksimum denda (Rp, 0 = tanpa batas)"), ("grace_days", "Masa tenggang (hari)"),
              ("max_loans_per_member", "Batas pinjam per anggota"), ("backup_retention", "Jumlah salinan backup disimpan"),
              ("backup_dir", "Folder backup (kosong = bawaan)")]

    def __init__(self, master, app):
        super().__init__(master, app)
        card = Card(self); card.pack(anchor="w", padx=20, fill="x")
        self.vars = {}
        for k, label in self.FIELDS:
            r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(r, text=label, width=300, anchor="w").pack(side="left")
            self.vars[k] = tk.StringVar(); ctk.CTkEntry(r, textvariable=self.vars[k], width=260).pack(side="left")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(r, text="Kebijakan buku hilang/rusak berat", width=300, anchor="w").pack(side="left")
        self.policy = tk.StringVar()
        ctk.CTkOptionMenu(r, values=["Ganti buku", "Bayar harga buku", "Ditentukan petugas"], variable=self.policy, width=260).pack(side="left")
        ctk.CTkButton(card, text="Simpan", command=guard(self.save), fg_color=theme.ACCENT).pack(anchor="w", padx=12, pady=12)

    def refresh(self, **kw):
        for k, v in self.vars.items(): v.set(self.s.settings.get(k, ""))
        self.policy.set(self.s.settings.get("lost_policy", "Ditentukan petugas"))

    def save(self):
        self.actor.require_admin()
        for k, v in self.vars.items(): self.s.settings.set(k, v.get(), self.actor)
        self.s.settings.set("lost_policy", self.policy.get(), self.actor)
        info("Pengaturan disimpan.")
