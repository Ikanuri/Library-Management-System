"""Peminjaman, Pengembalian, Denda."""
import tkinter as tk
from datetime import date, datetime

import customtkinter as ctk

from app.services.base import ServiceError
from app.services.book_service import CONDITIONS
from app.services.return_service import HEAVY, PROPOSED_STATUS
from . import theme
from .components import (Card, DataTable, FeedbackStrip, FormDialog, ScanEntry, StatCard, Toolbar, ask_int, caption,
                         confirm, guard, info, make_button, section_label, style_entry, style_option)
from .pages_core import Page


class LoansPage(Page):
    title = "Peminjaman"
    subtitle = "Pindai anggota dan eksemplar, lalu konfirmasi"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.member, self.pending_rows = None, []
        top = ctk.CTkFrame(self.body, fg_color="transparent"); top.pack(fill="x")
        top.columnconfigure(0, weight=1, uniform="c"); top.columnconfigure(1, weight=1, uniform="c")
        # --- kiri: anggota + scan
        left = Card(top, "1. Anggota dan eksemplar"); left.grid(row=0, column=0, sticky="nsew", padx=(0, theme.GAP // 2))
        pad = dict(padx=theme.PAD_CARD + 2)
        self.member_entry = ScanEntry(left, self.pick_member, "No. anggota / nama, lalu Enter", on_error=self._member_error, height=theme.H_CTRL)
        self.member_entry.pack(fill="x", pady=(theme.SP3, theme.SP2), **pad)
        self.member_card = ctk.CTkFrame(left, fg_color=theme.PANEL2, corner_radius=theme.R_BTN)
        self.member_card.pack(fill="x", pady=(0, theme.SP3), **pad)
        self.member_lbl = ctk.CTkLabel(self.member_card, text="Belum ada anggota dipilih", font=theme.font(theme.FS_BODY, True), text_color=theme.MUTED, anchor="w", justify="left")
        self.member_lbl.pack(anchor="w", padx=theme.SP3, pady=(theme.SP2, 0))
        self.member_sub = caption(self.member_card, ""); self.member_sub.pack(anchor="w", padx=theme.SP3, pady=(0, theme.SP2))
        self.scan = ScanEntry(left, self.add_code, "Pindai barcode eksemplar lalu Enter", on_error=self._scan_error)
        self.scan.pack(fill="x", pady=(0, theme.SP3), **pad)
        self.strip = FeedbackStrip(left); self.strip.pack(fill="x", pady=(0, theme.PAD_CARD), **pad)
        # --- kanan: daftar sementara
        right = Card(top, "2. Akan dipinjam"); right.grid(row=0, column=1, sticky="nsew", padx=(theme.GAP // 2, 0))
        self.pending = DataTable(right, [("title", "Judul", 190), ("barcode", "Barcode", 90), ("due", "Jatuh tempo", 120)], height=6)
        self.pending.pack(fill="both", expand=True, padx=theme.PAD_CARD, pady=(theme.SP3, theme.SP2))
        bar = ctk.CTkFrame(right, fg_color="transparent"); bar.pack(fill="x", padx=theme.PAD_CARD, pady=(0, theme.PAD_CARD))
        make_button(bar, "Konfirmasi pinjam", guard(self.confirm_loan), "primary").pack(side="left")
        make_button(bar, "Hapus item", guard(self.remove_item), "secondary").pack(side="left", padx=theme.SP2)
        make_button(bar, "Kosongkan", self.reset, "ghost").pack(side="left")
        # --- bawah: pinjaman aktif
        row = ctk.CTkFrame(self.body, fg_color="transparent"); row.pack(fill="x", pady=(theme.GAP, theme.SP2))
        section_label(row, "Pinjaman aktif").pack(side="left")
        tb = Toolbar(row); tb.pack(side="right"); self.q = tb.search(self.refresh, "Anggota, judul, barcode")
        self.table = DataTable(self.body, [("loan_date", "Pinjam", 100), ("due_date", "Jatuh tempo", 120), ("member_name", "Anggota", 160),
                                           ("title", "Judul", 240), ("barcode", "Barcode", 90), ("days_late", "Hari terlambat", 130),
                                           ("fine_txt", "Denda proyeksi", 140)], height=7)
        self.table.pack(fill="both", expand=True)

    # --- umpan balik
    def _member_error(self, msg):
        self.strip.fail("Anggota tidak dapat dipilih", msg)

    def _scan_error(self, msg):
        self.strip.fail("Eksemplar ditolak", msg)

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
        limit = self.s.settings.get_int("max_loans_per_member", 3)
        self.member_lbl.configure(text=m["name"], text_color=theme.TEXT)
        self.member_sub.configure(text=f"{m['member_no']} · pinjaman aktif {self.s.loans.active_count(m['id'])} dari maks. {limit}")
        self.strip.note("Anggota dipilih", f"{m['name']} ({m['member_no']}). Pindai eksemplar berikutnya.")
        self.scan.focus_set()

    def add_code(self, code):
        c = self.s.books.find_copy_by_code(code)
        if not c:
            raise ServiceError(f"Kode '{code}' tidak ditemukan.")
        if c["circulation_status"] != "Tersedia" or c["archived_at"]:
            raise ServiceError(f"{c['title']} berstatus {c['circulation_status']}; tidak dapat dipinjam.")
        if any(r["barcode"] == c["barcode"] for r in self.pending_rows):
            raise ServiceError(f"{c['title']} sudah ada dalam daftar.")
        b = self.s.books.get_book(c["book_id"])
        due = self._due()
        self.pending_rows.append({"id": c["barcode"], "title": c["title"], "barcode": c["barcode"], "due": due})
        self.pending.load(self.pending_rows)
        self.strip.ok(c["title"], f"{b['author'] or '-'} · {c['barcode']} · {c['inventory_code']}")

    def _due(self):
        from datetime import timedelta
        return (date.today() + timedelta(days=self.s.settings.get_int("loan_days", 7))).isoformat()

    def remove_item(self):
        r = self.pending.selected_one()
        if r:
            self.pending_rows = [x for x in self.pending_rows if x["barcode"] != r["barcode"]]
            self.pending.load(self.pending_rows)
            self.strip.note("Item dihapus", r["title"])

    def reset(self):
        self.member, self.pending_rows = None, []
        self.member_lbl.configure(text="Belum ada anggota dipilih", text_color=theme.MUTED); self.member_sub.configure(text="")
        self.pending.load([]); self.strip.clear(); self.member_entry.focus_set()

    def confirm_loan(self):
        if not self.member:
            raise ServiceError("Pilih anggota terlebih dahulu.")
        lid = self.s.loans.checkout(self.actor, self.member["id"], [r["barcode"] for r in self.pending_rows])
        loan = self.s.loans.get(lid)
        self.reset(); self.refresh()
        self.strip.ok(f"Peminjaman #{lid} tersimpan", f"Jatuh tempo {loan['due_date']} · " + ", ".join(i["title"] for i in loan["items"]))
        self.toast(f"Peminjaman #{lid} tersimpan")

    def refresh(self, **kw):
        rows = self.s.loans.active_items(self.q.get())
        for r in rows:
            r["fine_txt"] = theme.rupiah(r["projected_fine"]) if r["days_late"] > 0 else "-"
        self.table.load(rows, tag=lambda r: "late" if r["days_late"] > 0 else None)
        self.member_entry.focus_soon()


class ReturnsPage(Page):
    title = "Pengembalian"
    subtitle = "Pindai eksemplar yang dikembalikan"

    def __init__(self, master, app):
        super().__init__(master, app)
        card = Card(self.body); card.pack(fill="x")
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(fill="x", padx=theme.PAD_CARD + 2, pady=(theme.PAD_CARD, theme.SP2))
        self.scan = ScanEntry(row, self.scan_code, "Pindai barcode eksemplar lalu Enter", on_error=self._error, width=360)
        self.scan.pack(side="left")
        ctk.CTkLabel(row, text="KONDISI", font=theme.font(theme.FS_TH - 1, True), text_color=theme.MUTED).pack(side="left", padx=(theme.GAP, 6))
        self.cond = tk.StringVar(value="Baik"); style_option(row, CONDITIONS, self.cond, 150).pack(side="left")
        ctk.CTkLabel(row, text="TGL KEMBALI", font=theme.font(theme.FS_TH - 1, True), text_color=theme.MUTED).pack(side="left", padx=(theme.GAP, 6))
        self.date = tk.StringVar(value=date.today().isoformat()); style_entry(row, textvariable=self.date, width=110).pack(side="left")
        self.strip = FeedbackStrip(card); self.strip.pack(fill="x", padx=theme.PAD_CARD + 2, pady=(theme.SP2, theme.PAD_CARD))
        section_label(self.body, "Pengembalian sesi ini").pack(anchor="w", pady=(theme.GAP, theme.SP2))
        self.table = DataTable(self.body, [("time", "Waktu", 70), ("title", "Judul", 260), ("member", "Anggota", 160),
                                           ("new_status", "Status baru", 110), ("fine_txt", "Denda", 100)], status_key="new_status")
        self.table.pack(fill="both", expand=True)
        self.log = []

    def _error(self, msg):
        self.strip.fail("Pengembalian ditolak", msg)

    def scan_code(self, code):
        cond, when = self.cond.get(), self.date.get().strip() or None
        pv = self.s.returns.preview(code, when)
        status = None
        if cond in HEAVY:
            prop = PROPOSED_STATUS[cond]
            if not confirm(f"Kondisi {cond}. Ubah status eksemplar menjadi '{prop}'?", yes="Ubah status"):
                self.strip.warn("Pengembalian dibatalkan", "Petugas tidak mengonfirmasi perubahan status.")
                return
            status = prop
        fee = 0
        if cond in HEAVY:
            fee = ask_int("Biaya penggantian", f"Kebijakan: {self.s.settings.get('lost_policy')}. Biaya penggantian (Rp), 0 bila buku diganti/tanpa biaya", 0, 0) or 0
        r = self.s.returns.return_item(self.actor, code, cond, when, status, fee)
        fine = r["fine"]["amount"] if r["fine"] else 0
        detail = f"{r['member']} · status {r['new_status']} · terlambat {pv['days_late']} hari · denda {theme.rupiah(fine)}"
        (self.strip.warn if fine else self.strip.ok)(f"{r['title']} dikembalikan", detail)
        self.log.insert(0, {"time": datetime.now().strftime("%H:%M"), "title": r["title"], "member": r["member"],
                            "new_status": r["new_status"], "fine_txt": theme.rupiah(fine)})
        self.table.load(self.log)

    def refresh(self, **kw):
        self.scan.focus_soon()


class FinesPage(Page):
    title = "Denda dan Pembayaran"
    subtitle = "Denda ditetapkan saat pengembalian; yang masih berjalan hanya proyeksi"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.add_action("Catat pembayaran", self.pay)
        grid = ctk.CTkFrame(self.body, fg_color="transparent"); grid.pack(fill="x", pady=(0, theme.GAP))
        self.cards = {}
        for i, (k, lbl, col) in enumerate([("assessed", "Ditetapkan", theme.BLUE), ("paid", "Dibayar", theme.OK), ("outstanding", "Sisa", theme.WARN)]):
            c = StatCard(grid, lbl, color=col, small=True)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else theme.GAP // 2, 0 if i == 2 else theme.GAP // 2)); grid.columnconfigure(i, weight=1, uniform="f")
            self.cards[k] = c
        run = Card(self.body, "Denda berjalan", "Belum dapat dibayar sampai buku dikembalikan"); run.pack(fill="x", pady=(0, theme.GAP))
        self.running = DataTable(run, [("member_name", "Anggota", 150), ("title", "Judul", 240), ("due_date", "Jatuh tempo", 90),
                                       ("days_late", "Hari", 50), ("fine_txt", "Proyeksi", 100)], height=4)
        self.running.pack(fill="x", padx=theme.PAD_CARD, pady=theme.PAD_CARD)
        tb = Toolbar(self.body); tb.pack(fill="x", pady=(0, theme.SP2))
        section_label(tb, "Denda ditetapkan").pack(side="left", padx=(0, theme.GAP))
        self.status = tb.combo(["Semua", "Belum bayar", "Sebagian", "Lunas"], self.refresh, width=130)
        self.table = DataTable(self.body, [("assessed_at", "Ditetapkan", 130), ("member_name", "Anggota", 150), ("title", "Judul", 220),
                                           ("kind", "Jenis", 130), ("amount_txt", "Nominal", 90), ("paid_txt", "Dibayar", 90),
                                           ("remaining_txt", "Sisa", 90), ("status", "Status", 100)], status_key="status")
        self.table.pack(fill="both", expand=True)

    def refresh(self, **kw):
        sm = self.s.fines.summary()
        for k, c in self.cards.items():
            c.set(theme.rupiah(sm[k]))
        od = self.s.loans.overdue()
        for r in od:
            r["fine_txt"] = theme.rupiah(r["projected_fine"])
        self.running.load(od, tag=lambda r: "late")
        rows = self.s.fines.list(self.status.get())
        for r in rows:
            r["amount_txt"], r["paid_txt"], r["remaining_txt"] = theme.rupiah(r["amount"]), theme.rupiah(r["paid"]), theme.rupiah(r["remaining"])
        self.table.load(rows)

    def pay(self):
        r = self.table.selected_one()
        if not r:
            return
        if r["remaining"] <= 0:
            return info("Denda ini sudah lunas.")
        def save(v):
            try:
                amt = int(v["amount"])
            except ValueError:
                raise ServiceError("Nominal harus bilangan bulat.")
            self.s.fines.pay(self.actor, r["id"], amt); self.refresh(); self.toast("Pembayaran dicatat")
        FormDialog(self, f"Pembayaran (sisa {theme.rupiah(r['remaining'])})", [("amount", "Nominal (Rp)", "entry")], {"amount": r["remaining"]}, save)
