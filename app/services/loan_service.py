"""FR-05 peminjaman."""
from datetime import timedelta

from app.database.connection import Tx
from app.utils.barcode import normalize
from .base import ServiceError, parse_date, today


class LoanService:
    def __init__(self, db, audit, settings):
        self.db, self.audit, self.settings = db, audit, settings

    def active_count(self, member_id):
        return self.db.execute(
            "SELECT COUNT(*) FROM loan_items li JOIN loans l ON l.id=li.loan_id "
            "WHERE l.member_id=? AND li.returned_at IS NULL", (member_id,)).fetchone()[0]

    def checkout(self, actor, member_id, codes, loan_date=None):
        """Pinjamkan satu atau beberapa eksemplar secara atomik. Mengembalikan id transaksi."""
        m = self.db.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
        if not m:
            raise ServiceError("Anggota tidak ditemukan.")
        if not m["is_active"]:
            raise ServiceError("Anggota nonaktif tidak dapat meminjam.")
        codes = [normalize(c) for c in codes if normalize(c)]
        if not codes:
            raise ServiceError("Belum ada eksemplar yang dipindai.")
        if len(set(codes)) != len(codes):
            raise ServiceError("Ada kode eksemplar ganda dalam satu transaksi.")
        limit = self.settings.get_int("max_loans_per_member", 3)
        if self.active_count(member_id) + len(codes) > limit:
            raise ServiceError(f"Melebihi batas pinjam ({limit} eksemplar per anggota).")
        loan_date = loan_date or today()
        due = (parse_date(loan_date) + timedelta(days=self.settings.get_int("loan_days", 7))).isoformat()
        with Tx(self.db):
            copies = []
            for code in codes:
                c = self.db.execute(
                    "SELECT c.*, b.title, b.is_active FROM book_copies c JOIN books b ON b.id=c.book_id "
                    "WHERE c.barcode=? OR UPPER(c.inventory_code)=?", (code, code)).fetchone()
                if not c:
                    raise ServiceError(f"Eksemplar '{code}' tidak ditemukan.")
                if c["archived_at"] or not c["is_active"]:
                    raise ServiceError(f"Eksemplar '{code}' sudah keluar koleksi.")
                if c["circulation_status"] != "Tersedia":
                    raise ServiceError(f"Eksemplar '{code}' ({c['title']}) berstatus {c['circulation_status']}; tidak dapat dipinjam.")
                copies.append(c)
            cur = self.db.execute("INSERT INTO loans(member_id,user_id,loan_date,due_date) VALUES (?,?,?,?)",
                                  (member_id, actor.id, loan_date, due))
            loan_id = cur.lastrowid
            for c in copies:
                self.db.execute("INSERT INTO loan_items(loan_id,copy_id) VALUES (?,?)", (loan_id, c["id"]))
                self.db.execute("UPDATE book_copies SET circulation_status='Dipinjam' WHERE id=?", (c["id"],))
                # cakupan rak dinamis: eksemplar belum diperiksa yang dipinjam keluar dari cakupan rak
                self.db.execute(
                    "UPDATE stock_opname_items SET result='Dipinjam' WHERE copy_id=? AND result='Belum diperiksa' "
                    "AND session_id IN (SELECT id FROM stock_opname_sessions WHERE status<>'Final')", (c["id"],))
            self.audit.log(actor, "loan", loan_id, "create", None,
                           {"member_id": member_id, "copies": [c["barcode"] for c in copies], "due": due})
        return loan_id

    def get(self, loan_id):
        loan = self.db.execute(
            "SELECT l.*, m.name AS member_name, m.member_no FROM loans l JOIN members m ON m.id=l.member_id "
            "WHERE l.id=?", (loan_id,)).fetchone()
        if not loan:
            return None
        items = [dict(r) for r in self.db.execute(
            "SELECT li.*, b.title, c.barcode, c.inventory_code FROM loan_items li "
            "JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id WHERE li.loan_id=?", (loan_id,))]
        return dict(loan) | {"items": items}

    def active_items(self, search=""):
        """Pinjaman aktif beserta status terlambat dan denda proyeksi (tidak dapat dibayar)."""
        sql = """SELECT li.id AS loan_item_id, l.id AS loan_id, l.loan_date, l.due_date, m.name AS member_name,
                 m.member_no, b.title, c.barcode FROM loan_items li JOIN loans l ON l.id=li.loan_id
                 JOIN members m ON m.id=l.member_id JOIN book_copies c ON c.id=li.copy_id
                 JOIN books b ON b.id=c.book_id WHERE li.returned_at IS NULL"""
        args = []
        s = (search or "").strip()
        if s:
            sql += " AND (m.name LIKE ? OR m.member_no LIKE ? OR b.title LIKE ? OR c.barcode LIKE ?)"
            args += [f"%{s}%"] * 4
        rate, grace, cap = (self.settings.get_int("fine_rate"), self.settings.get_int("grace_days"),
                            self.settings.get_int("fine_cap"))
        from .fine_service import compute_fine
        out = []
        for r in self.db.execute(sql + " ORDER BY l.due_date", args):
            d = dict(r)
            d["days_late"], d["projected_fine"] = compute_fine(d["due_date"], today(), rate, grace, cap)
            out.append(d)
        return out

    def overdue(self):
        return [r for r in self.active_items() if r["days_late"] > 0]
