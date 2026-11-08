"""FR-06 pengembalian."""
from app.database.connection import Tx
from app.utils.barcode import normalize
from .base import ServiceError, now, today
from .book_service import CONDITIONS

HEAVY = ("Rusak berat", "Tidak layak pakai")
PROPOSED_STATUS = {"Rusak berat": "Perbaikan", "Tidak layak pakai": "Dihapusbukukan"}


class ReturnService:
    def __init__(self, db, audit, settings, fines):
        self.db, self.audit, self.settings, self.fines = db, audit, settings, fines

    def find_active(self, code):
        code = normalize(code)
        r = self.db.execute(
            """SELECT li.id AS loan_item_id, li.copy_id, l.id AS loan_id, l.loan_date, l.due_date,
                      m.name AS member_name, m.member_no, b.title, c.barcode, c.condition
               FROM loan_items li JOIN loans l ON l.id=li.loan_id JOIN members m ON m.id=l.member_id
               JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id
               WHERE li.returned_at IS NULL AND (c.barcode=? OR UPPER(c.inventory_code)=?)""", (code, code)).fetchone()
        if not r:
            raise ServiceError("Tidak ada pinjaman aktif untuk kode ini (belum dipinjam atau sudah dikembalikan).")
        return dict(r)

    def preview(self, code, returned_at=None):
        info = self.find_active(code)
        days, amount = self.fines.projected(info["due_date"], returned_at or today())
        return info | {"days_late": days, "late_fine": amount}

    def return_item(self, actor, code, condition="Baik", returned_at=None, confirmed_status=None,
                    replacement_fee=0):
        """Kembalikan satu eksemplar. Kondisi berat memerlukan `confirmed_status` (Perbaikan/Hilang/Dihapusbukukan)."""
        if condition not in CONDITIONS:
            raise ServiceError("Kondisi tidak valid.")
        returned_at = returned_at or today()
        info = self.find_active(code)
        if returned_at < info["loan_date"]:
            raise ServiceError("Tanggal kembali tidak boleh sebelum tanggal pinjam.")
        new_status = "Tersedia"
        if condition in HEAVY:
            if confirmed_status not in ("Perbaikan", "Hilang", "Dihapusbukukan"):
                raise ServiceError(
                    f"Kondisi {condition}: petugas harus mengonfirmasi status "
                    f"(usulan: {PROPOSED_STATUS[condition]}).")
            new_status = confirmed_status
        with Tx(self.db):
            self.db.execute("UPDATE loan_items SET returned_at=?, return_condition=? WHERE id=?",
                            (returned_at, condition, info["loan_item_id"]))
            if new_status in ("Hilang", "Dihapusbukukan"):
                self.db.execute(
                    "UPDATE book_copies SET circulation_status=?, condition=?, archived_at=?, archived_by=?,"
                    "archived_reason=?, updated_at=?, updated_by=? WHERE id=?",
                    (new_status, condition, now(), actor.id,
                     "Hilang" if new_status == "Hilang" else "Rusak tidak layak", now(), actor.id, info["copy_id"]))
            else:
                self.db.execute("UPDATE book_copies SET circulation_status=?, condition=?, updated_at=?,"
                                "updated_by=? WHERE id=?", (new_status, condition, now(), actor.id, info["copy_id"]))
            fine_id = self.fines.assess(info["loan_item_id"], info["due_date"], returned_at, replacement_fee)
            # cakupan rak dinamis: dikembalikan selama opname -> wajib dipindai lagi
            if new_status == "Tersedia":
                self.db.execute(
                    "UPDATE stock_opname_items SET result='Belum diperiksa' WHERE copy_id=? AND result='Dipinjam' "
                    "AND session_id IN (SELECT id FROM stock_opname_sessions WHERE status<>'Final')",
                    (info["copy_id"],))
            self.audit.log(actor, "loan_item", info["loan_item_id"], "return", None,
                           {"barcode": info["barcode"], "condition": condition, "status": new_status,
                            "fine_id": fine_id})
        fine = self.db.execute("SELECT * FROM fines WHERE id=?", (fine_id,)).fetchone() if fine_id else None
        return {"loan_item_id": info["loan_item_id"], "title": info["title"], "member": info["member_name"],
                "new_status": new_status, "fine": dict(fine) if fine else None}
