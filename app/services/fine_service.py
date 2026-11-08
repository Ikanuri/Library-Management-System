"""FR-07: denda (proposal 3.7). Uang = bilangan bulat rupiah."""
from datetime import date

from app.database.connection import Tx
from .base import ServiceError, parse_date, today


def compute_fine(due, returned, rate, grace=0, cap=0):
    """Denda = max(0, hari_terlambat - tenggang) x tarif, dibatasi cap bila cap > 0."""
    days_late = max(0, (parse_date(returned) - parse_date(due)).days)
    amount = max(0, days_late - grace) * rate
    if cap and amount > cap:
        amount = cap
    return days_late, amount


class FineService:
    def __init__(self, db, audit, settings):
        self.db, self.audit, self.settings = db, audit, settings

    def rate_params(self):
        s = self.settings
        return s.get_int("fine_rate"), s.get_int("grace_days"), s.get_int("fine_cap")

    def projected(self, due, as_of=None):
        """Denda proyeksi untuk pinjaman terlambat yang belum kembali (tidak dapat dibayar)."""
        rate, grace, cap = self.rate_params()
        return compute_fine(due, as_of or today(), rate, grace, cap)

    def assess(self, loan_item_id, due, returned, replacement_fee=0):
        """Tetapkan denda final saat pengembalian. Dipanggil dalam transaksi pengembalian."""
        rate, grace, cap = self.rate_params()
        days_late, late_amt = compute_fine(due, returned, rate, grace, cap)
        total = late_amt + max(0, int(replacement_fee))
        if total <= 0:
            return None
        kinds = []
        if late_amt:
            kinds.append("Keterlambatan")
        if replacement_fee:
            kinds.append("Penggantian")
        cur = self.db.execute(
            "INSERT INTO fines(loan_item_id,days_late,rate,amount,kind) VALUES (?,?,?,?,?)",
            (loan_item_id, days_late, rate, total, " + ".join(kinds)))
        self.db.execute("UPDATE loan_items SET fine_id=? WHERE id=?", (cur.lastrowid, loan_item_id))
        return cur.lastrowid

    def paid(self, fine_id):
        return self.db.execute("SELECT COALESCE(SUM(amount),0) FROM fine_payments WHERE fine_id=?",
                               (fine_id,)).fetchone()[0]

    def pay(self, actor, fine_id, amount):
        f = self.db.execute("SELECT * FROM fines WHERE id=?", (fine_id,)).fetchone()
        if not f:
            raise ServiceError("Denda tidak ditemukan.")
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise ServiceError("Nominal harus berupa bilangan bulat.")
        if amount <= 0:
            raise ServiceError("Nominal harus lebih dari 0.")
        remaining = f["amount"] - self.paid(fine_id)
        if amount > remaining:
            raise ServiceError(f"Nominal melebihi sisa denda (Rp{remaining:,}).".replace(",", "."))
        with Tx(self.db):
            self.db.execute("INSERT INTO fine_payments(fine_id,amount,received_by) VALUES (?,?,?)",
                            (fine_id, amount, actor.id))
            status = "Lunas" if amount == remaining else "Sebagian"
            self.db.execute("UPDATE fines SET status=? WHERE id=?", (status, fine_id))
            self.audit.log(actor, "fine", fine_id, "pay", None, {"amount": amount, "status": status})
        return status

    def list(self, status="Semua"):
        sql = """SELECT f.*, m.name AS member_name, m.member_no, b.title, c.barcode,
                 COALESCE((SELECT SUM(amount) FROM fine_payments p WHERE p.fine_id=f.id),0) AS paid
                 FROM fines f JOIN loan_items li ON li.id=f.loan_item_id JOIN loans l ON l.id=li.loan_id
                 JOIN members m ON m.id=l.member_id JOIN book_copies c ON c.id=li.copy_id
                 JOIN books b ON b.id=c.book_id"""
        args = []
        if status != "Semua":
            sql += " WHERE f.status=?"; args.append(status)
        return [dict(r) | {"remaining": r["amount"] - r["paid"]}
                for r in self.db.execute(sql + " ORDER BY f.id DESC", args)]

    def summary(self):
        r = self.db.execute("SELECT COALESCE(SUM(amount),0) a FROM fines").fetchone()["a"]
        p = self.db.execute("SELECT COALESCE(SUM(amount),0) a FROM fine_payments").fetchone()["a"]
        return {"assessed": r, "paid": p, "outstanding": r - p}
