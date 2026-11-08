"""Peminjaman, Pengembalian, Denda."""
import tkinter as tk
from datetime import date, datetime

import customtkinter as ctk

from app.services.base import ServiceError
from app.services.book_service import CONDITIONS
from app.services.return_service import HEAVY, PROPOSED_STATUS
from . import theme
from .components import ask_int, Card, DataTable, FormDialog, ScanEntry, Toolbar, confirm, guard, info
from .pages_core import Page


class LoansPage(Page):
    title = "Peminjaman"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.member, self.codes = None, []
        top = Card(self); top.pack(fill="x", padx=20)
        row = ctk.CTkFrame(top, fg_color="transparent"); row.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(row, text="Anggota:").pack(side="left")
        self.member_entry = ScanEntry(row, self.pick_member, "No. anggota atau nama lalu Enter", width=280)
        self.member_entry.pack(side="left", padx=8)
        self.member_lbl = ctk.CTkLabel(row, text="(belum dipilih)", text_color=theme.MUTED); self.member_lbl.pack(side="left")
        row2 = ctk.CTkFrame(top, fg_color="transparent"); row2.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row2, text="Eksemplar:").pack(side="left")
        self.scan = ScanEntry(row2, self.add_code, width=280); self.scan.pack(side="left", padx=8)
        ctk.CTkButton(row2, text="Konfirmasi pinjam", command=guard(self.confirm_loan), fg_color=theme.ACCENT).pack(side="left", padx=6)
        ctk.CTkButton(row2, text="Kosongkan", command=self.reset, fg_color=theme.PANEL2, text_color=theme.TEXT).pack(side="left")
        self.pending = ctk.CTkLabel(top, text="", justify="left", anchor="w"); self.pending.pack(anchor="w", padx=12, pady=(0, 10))
        tb = Toolbar(self); tb.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(tb, text="Pinjaman aktif", font=theme.font(14, True)).pack(side="left", padx=(0, 10))
        self.q = tb.search(self.refresh, "Anggota, judul, barcode")
        self.table = DataTable(self, [("loan_date", "Pinjam", 90), ("due_date", "Jatuh tempo", 90), ("member_name", "Anggota", 160),
                                      ("title", "Judul", 260), ("barcode", "Barcode", 90), ("days_late", "Hari terlambat", 90),
                                      ("fine_txt", "Denda proyeksi", 110)])
        self.table.pack(fill="both", expand=True, padx=20, pady=8)

    def pick_member(self, text):
        m = self.s.members.find_by_no(text)
        if not m:
            found = self.s.members.list(text, "Aktif")
            if len(found) != 1:
                raise ServiceError("Anggota tidak ditemukan atau lebih dari satu hasil; gunakan nomor anggota.")
            m = found[0]
        if not m["is_active"]:
            raise ServiceError("Anggota nonaktif tidak dapat meminjam.")
        self.member = m
        self.member_lbl.configure(text=f"{m['name']} ({m['member_no']}) · pinjaman aktif {self.s.loans.active_count(m['id'])}", text_color=theme.TEXT)
        self.scan.focus_set()

    def add_code(self, code):
        c = self.s.books.find_copy_by_code(code)
        if not c: raise ServiceError(f"Kode '{code}' tidak ditemukan.")
        if c["circulation_status"] != "Tersedia" or c["archived_at"]:
            raise ServiceError(f"{c['title']} berstatus {c['circulation_status']}; tidak dapat dipinjam.")
        if c["barcode"] in self.codes: raise ServiceError("Eksemplar sudah dipindai.")
        self.codes.append(c["barcode"])
        self._show_pending(c["title"])

    def _show_pending(self, last=None):
        self.pending.configure(text="Akan dipinjam: " + ", ".join(self.codes) + (f"  (terakhir: {last})" if last else ""))

    def reset(self):
        self.member, self.codes = None, []
        self.member_lbl.configure(text="(belum dipilih)", text_color=theme.MUTED); self.pending.configure(text="")

    def confirm_loan(self):
        if not self.member: raise ServiceError("Pilih anggota terlebih dahulu.")
        lid = self.s.loans.checkout(self.actor, self.member["id"], self.codes)
        loan = self.s.loans.get(lid)
        info(f"Peminjaman #{lid} tersimpan.\nJatuh tempo: {loan['due_date']}\n" + "\n".join("• " + i["title"] for i in loan["items"]))
        self.reset(); self.refresh()

    def refresh(self, **kw):
        rows = self.s.loans.active_items(self.q.get())
        for r in rows:
            r["fine_txt"] = theme.rupiah(r["projected_fine"]) if r["days_late"] > 0 else "-"
        self.table.load(rows, tag=lambda r: "late" if r["days_late"] > 0 else None)


class ReturnsPage(Page):
    title = "Pengembalian"

    def __init__(self, master, app):
        super().__init__(master, app)
        card = Card(self); card.pack(fill="x", padx=20)
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(row, text="Eksemplar:").pack(side="left")
        self.scan = ScanEntry(row, self.scan_code, width=280); self.scan.pack(side="left", padx=8)
        ctk.CTkLabel(row, text="Kondisi:").pack(side="left")
        self.cond = tk.StringVar(value="Baik")
        ctk.CTkOptionMenu(row, values=CONDITIONS, variable=self.cond, width=140).pack(side="left", padx=6)
        ctk.CTkLabel(row, text="Tgl kembali:").pack(side="left", padx=(10, 0))
        self.date = tk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(row, textvariable=self.date, width=100).pack(side="left", padx=6)
        self.result = ctk.CTkLabel(card, text="", justify="left", anchor="w", wraplength=900); self.result.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(self, text="Pengembalian hari ini", font=theme.font(14, True)).pack(anchor="w", padx=20, pady=(10, 0))
        self.table = DataTable(self, [("time", "Waktu", 70), ("title", "Judul", 260), ("member", "Anggota", 160),
                                      ("new_status", "Status baru", 100), ("fine_txt", "Denda", 100)])
        self.table.pack(fill="both", expand=True, padx=20, pady=8)
        self.log = []

    def scan_code(self, code):
        cond, when = self.cond.get(), self.date.get().strip() or None
        pv = self.s.returns.preview(code, when)
        status = None
        if cond in HEAVY:
            prop = PROPOSED_STATUS[cond]
            if not confirm(f"Kondisi {cond}. Ubah status eksemplar menjadi '{prop}'?\n(Pilih Tidak untuk membatalkan.)"):
                return
            status = prop
        fee = 0
        if cond in HEAVY:
            fee = ask_int("Biaya penggantian", f"Kebijakan: {self.s.settings.get('lost_policy')}. Biaya penggantian (Rp), 0 bila buku diganti/tanpa biaya", 0, 0) or 0
        r = self.s.returns.return_item(self.actor, code, cond, when, status, fee)
        fine = r["fine"]["amount"] if r["fine"] else 0
        self.result.configure(text=f"✔ {r['title']} dikembalikan oleh {r['member']}. Status: {r['new_status']}. "
                                   f"Terlambat {pv['days_late']} hari. Denda: {theme.rupiah(fine)}",
                              text_color=theme.WARN if fine else theme.OK)
        self.log.insert(0, {"time": datetime.now().strftime("%H:%M"),
                            "title": r["title"], "member": r["member"], "new_status": r["new_status"], "fine_txt": theme.rupiah(fine)})
        self.table.load(self.log)

    def refresh(self, **kw):
        self.scan.focus_set()


class FinesPage(Page):
    title = "Denda dan Pembayaran"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sum = ctk.CTkLabel(self, text="", font=theme.font(13)); self.sum.pack(anchor="w", padx=20)
        tb = Toolbar(self); tb.pack(fill="x", padx=20, pady=6)
        self.status = tb.combo(["Semua", "Belum bayar", "Sebagian", "Lunas"], self.refresh, width=130)
        tb.button("Catat pembayaran", self.pay)
        ctk.CTkLabel(self, text="Denda berjalan (belum dapat dibayar sampai buku dikembalikan):", text_color=theme.MUTED).pack(anchor="w", padx=20)
        self.running = DataTable(self, [("member_name", "Anggota", 150), ("title", "Judul", 240), ("due_date", "Jatuh tempo", 90),
                                        ("days_late", "Hari", 50), ("fine_txt", "Proyeksi", 100)], height=4)
        self.running.pack(fill="x", padx=20, pady=4)
        self.table = DataTable(self, [("assessed_at", "Ditetapkan", 130), ("member_name", "Anggota", 150), ("title", "Judul", 220),
                                      ("kind", "Jenis", 130), ("amount_txt", "Nominal", 90), ("paid_txt", "Dibayar", 90),
                                      ("remaining_txt", "Sisa", 90), ("status", "Status", 90)], status_key="status")
        self.table.pack(fill="both", expand=True, padx=20, pady=8)

    def refresh(self, **kw):
        sm = self.s.fines.summary()
        self.sum.configure(text=f"Ditetapkan {theme.rupiah(sm['assessed'])} · Dibayar {theme.rupiah(sm['paid'])} · Sisa {theme.rupiah(sm['outstanding'])}")
        od = self.s.loans.overdue()
        for r in od: r["fine_txt"] = theme.rupiah(r["projected_fine"])
        self.running.load(od)
        rows = self.s.fines.list(self.status.get())
        for r in rows:
            r["amount_txt"], r["paid_txt"], r["remaining_txt"] = (theme.rupiah(r["amount"]), theme.rupiah(r["paid"]), theme.rupiah(r["remaining"]))
        self.table.load(rows)

    def pay(self):
        r = self.table.selected_one()
        if not r: return
        if r["remaining"] <= 0: return info("Denda ini sudah lunas.")
        def save(v):
            try: amt = int(v["amount"])
            except ValueError: raise ServiceError("Nominal harus bilangan bulat.")
            self.s.fines.pay(self.actor, r["id"], amt); self.refresh()
        FormDialog(self, f"Pembayaran (sisa {theme.rupiah(r['remaining'])})", [("amount", "Nominal (Rp)", "entry")],
                   {"amount": r["remaining"]}, save)
