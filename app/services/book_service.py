"""FR-03: bibliografi dan eksemplar (proposal 3.3, 3.3.1, 3.3.2)."""
from datetime import date

from app.database.connection import Tx
from app.utils.barcode import generate_barcode, is_valid_barcode, normalize
from app.utils.validators import clean_isbn, isbn_valid
from .base import ServiceError, now, row_dict

CIRC_STATUSES = ["Tersedia", "Dipinjam", "Perbaikan", "Hilang", "Dihapusbukukan"]
CONDITIONS = ["Baik", "Rusak ringan", "Rusak sedang", "Rusak berat", "Tidak layak pakai"]
ARCHIVE_REASONS = ["Hilang", "Rusak tidak layak", "Dihibahkan", "Lainnya"]
CASCADE_REASON = "Lainnya: judul diarsipkan"
BOOK_FIELDS = ["isbn", "title", "author", "publisher", "year", "category", "description", "shelf", "cover_path"]
EDITABLE_STATUS = ("Tersedia", "Perbaikan")


class BookService:
    def __init__(self, db, audit):
        self.db, self.audit = db, audit

    # ---------- util ----------
    def barcode_exists(self, code):
        return self.db.execute("SELECT 1 FROM book_copies WHERE barcode=?", (code,)).fetchone() is not None

    def next_inventory_code(self):
        year = date.today().year
        n = self.db.execute("SELECT COALESCE(MAX(id),0)+1 FROM book_copies").fetchone()[0]
        while True:
            code = f"INV-{year}-{n:05d}"
            if not self.db.execute("SELECT 1 FROM book_copies WHERE inventory_code=?", (code,)).fetchone():
                return code
            n += 1

    def copy_has_history(self, copy_id):
        q = ("SELECT 1 FROM loan_items WHERE copy_id=? UNION ALL "
             "SELECT 1 FROM stock_opname_items WHERE copy_id=? UNION ALL "
             "SELECT 1 FROM fines f JOIN loan_items li ON li.id=f.loan_item_id WHERE li.copy_id=? LIMIT 1")
        return self.db.execute(q, (copy_id,) * 3).fetchone() is not None

    def copy_is_borrowed(self, copy_id):
        return self.db.execute("SELECT 1 FROM loan_items WHERE copy_id=? AND returned_at IS NULL",
                               (copy_id,)).fetchone() is not None

    def book_has_history(self, book_id):
        return any(self.copy_has_history(r["id"]) for r in
                   self.db.execute("SELECT id FROM book_copies WHERE book_id=?", (book_id,)))

    # ---------- judul ----------
    def _validate_book(self, data, book_id=None):
        if not (data.get("title") or "").strip():
            raise ServiceError("Judul wajib diisi.")
        isbn = clean_isbn(data.get("isbn"))
        if not isbn_valid(isbn):
            raise ServiceError("ISBN tidak valid.")
        if isbn:
            r = self.db.execute("SELECT id FROM books WHERE isbn=? AND id<>?", (isbn, book_id or -1)).fetchone()
            if r:
                raise ServiceError("ISBN sudah dipakai judul lain.")
        year = data.get("year")
        if year not in (None, ""):
            try:
                year = int(year)
            except ValueError:
                raise ServiceError("Tahun terbit harus berupa angka.")
        else:
            year = None
        return isbn, year

    def add_book(self, actor, data):
        isbn, year = self._validate_book(data)
        vals = {k: (data.get(k) or None) for k in BOOK_FIELDS}
        vals.update(isbn=isbn, year=year, title=data["title"].strip())
        with Tx(self.db):
            cur = self.db.execute(
                f"INSERT INTO books({','.join(BOOK_FIELDS)},updated_by) VALUES ({','.join('?'*len(BOOK_FIELDS))},?)",
                [vals[k] for k in BOOK_FIELDS] + [actor.id if actor else None])
            self.audit.log(actor, "book", cur.lastrowid, "create", None, vals)
        return cur.lastrowid

    def get_book(self, book_id):
        return row_dict(self.db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone())

    def update_book(self, actor, book_id, data):
        old = self.get_book(book_id)
        if not old:
            raise ServiceError("Judul tidak ditemukan.")
        merged = {**old, **data}
        isbn, year = self._validate_book(merged, book_id)
        new = {k: (merged.get(k) or None) for k in BOOK_FIELDS}
        new.update(isbn=isbn, year=year, title=merged["title"].strip())
        with Tx(self.db):
            self.db.execute(
                f"UPDATE books SET {','.join(k+'=?' for k in BOOK_FIELDS)},updated_at=?,updated_by=? WHERE id=?",
                [new[k] for k in BOOK_FIELDS] + [now(), actor.id, book_id])
            self.audit.log(actor, "book", book_id, "update", {k: old[k] for k in BOOK_FIELDS}, new)

    def list_books(self, search="", category=None, shelf=None, view="Aktif", limit=1000):
        """view: Aktif | Diarsipkan | Semua."""
        sql = """SELECT b.*,
            (SELECT COUNT(*) FROM book_copies c WHERE c.book_id=b.id AND c.archived_at IS NULL) AS copies_total,
            (SELECT COUNT(*) FROM book_copies c WHERE c.book_id=b.id AND c.archived_at IS NULL
                AND c.circulation_status='Tersedia') AS copies_available
            FROM books b WHERE 1=1"""
        args = []
        if view == "Aktif":
            sql += " AND b.is_active=1"
        elif view == "Diarsipkan":
            sql += " AND b.is_active=0"
        if category:
            sql += " AND b.category=?"; args.append(category)
        if shelf:
            sql += " AND b.shelf=?"; args.append(shelf)
        s = normalize(search)
        if s:
            like = f"%{s}%"
            sql += """ AND (UPPER(b.title) LIKE ? OR UPPER(IFNULL(b.author,'')) LIKE ? OR IFNULL(b.isbn,'') LIKE ?
                OR EXISTS (SELECT 1 FROM book_copies c WHERE c.book_id=b.id
                    AND (c.barcode LIKE ? OR UPPER(c.inventory_code) LIKE ?)))"""
            args += [like] * 5
        sql += " ORDER BY b.title LIMIT ?"; args.append(limit)
        return [dict(r) for r in self.db.execute(sql, args)]

    def categories(self):
        return [r[0] for r in self.db.execute(
            "SELECT DISTINCT category FROM books WHERE category IS NOT NULL ORDER BY category")]

    def shelves(self):
        return [r[0] for r in self.db.execute(
            "SELECT DISTINCT shelf FROM (SELECT shelf FROM books UNION SELECT shelf FROM book_copies) "
            "WHERE shelf IS NOT NULL ORDER BY shelf")]

    def archive_book(self, actor, book_id, reason="Lainnya"):
        b = self.get_book(book_id)
        if not b:
            raise ServiceError("Judul tidak ditemukan.")
        if not b["is_active"]:
            raise ServiceError("Judul sudah diarsipkan.")
        copies = self.db.execute("SELECT id FROM book_copies WHERE book_id=? AND archived_at IS NULL",
                                 (book_id,)).fetchall()
        for c in copies:
            if self.copy_is_borrowed(c["id"]):
                raise ServiceError("Judul memiliki eksemplar yang sedang dipinjam; tidak dapat diarsipkan.")
        with Tx(self.db):
            t = now()
            for c in copies:
                self.db.execute(
                    "UPDATE book_copies SET circulation_status='Dihapusbukukan', archived_at=?, archived_by=?,"
                    "archived_reason=?, updated_at=?, updated_by=? WHERE id=?",
                    (t, actor.id, CASCADE_REASON, t, actor.id, c["id"]))
            self.db.execute("UPDATE books SET is_active=0, archived_at=?, archived_by=?, archived_reason=?,"
                            "updated_at=?, updated_by=? WHERE id=?", (t, actor.id, reason, t, actor.id, book_id))
            self.audit.log(actor, "book", book_id, "archive", {"is_active": 1},
                           {"is_active": 0, "reason": reason, "copies": len(copies)})

    def restore_book(self, actor, book_id):
        b = self.get_book(book_id)
        if not b or b["is_active"]:
            raise ServiceError("Judul tidak dalam arsip.")
        with Tx(self.db):
            t = now()
            self.db.execute(
                "UPDATE book_copies SET circulation_status='Tersedia', archived_at=NULL, archived_by=NULL,"
                "archived_reason=NULL, updated_at=?, updated_by=? WHERE book_id=? AND archived_reason=?",
                (t, actor.id, book_id, CASCADE_REASON))
            self.db.execute("UPDATE books SET is_active=1, archived_at=NULL, archived_by=NULL,"
                            "archived_reason=NULL, updated_at=?, updated_by=? WHERE id=?", (t, actor.id, book_id))
            self.audit.log(actor, "book", book_id, "restore", {"is_active": 0}, {"is_active": 1})

    def delete_book(self, actor, book_id):
        actor.require_admin()
        b = self.get_book(book_id)
        if not b:
            raise ServiceError("Judul tidak ditemukan.")
        for c in self.db.execute("SELECT id FROM book_copies WHERE book_id=?", (book_id,)):
            if self.copy_is_borrowed(c["id"]):
                raise ServiceError("Judul memiliki eksemplar yang sedang dipinjam; tidak dapat dihapus.")
        if self.book_has_history(book_id):
            raise ServiceError("Judul memiliki riwayat transaksi/opname; gunakan Arsipkan.")
        with Tx(self.db):
            n = self.db.execute("DELETE FROM book_copies WHERE book_id=?", (book_id,)).rowcount
            self.db.execute("DELETE FROM books WHERE id=?", (book_id,))
            self.audit.log(actor, "book", book_id, "delete", {**b, "copies_deleted": n}, None)

    # ---------- eksemplar ----------
    def get_copy(self, copy_id):
        return row_dict(self.db.execute(
            "SELECT c.*, b.title FROM book_copies c JOIN books b ON b.id=c.book_id WHERE c.id=?",
            (copy_id,)).fetchone())

    def find_copy_by_code(self, code):
        code = normalize(code)
        r = self.db.execute(
            "SELECT c.*, b.title FROM book_copies c JOIN books b ON b.id=c.book_id "
            "WHERE c.barcode=? OR UPPER(c.inventory_code)=?", (code, code)).fetchone()
        return row_dict(r)

    def add_copy(self, actor, book_id, barcode=None, inventory_code=None, shelf=None, condition="Baik",
                 acquired_at=None, acquisition_source=None, _audit=True):
        b = self.get_book(book_id)
        if not b or not b["is_active"]:
            raise ServiceError("Judul tidak ditemukan atau diarsipkan.")
        if condition not in CONDITIONS:
            raise ServiceError("Kondisi tidak valid.")
        barcode = normalize(barcode)
        if barcode:
            if not is_valid_barcode(barcode):
                raise ServiceError("Barcode harus 8 digit angka.")
            if self.barcode_exists(barcode):
                raise ServiceError("Barcode sudah dipakai eksemplar lain.")
        else:
            barcode = generate_barcode(self.barcode_exists)
        inventory_code = normalize(inventory_code) or self.next_inventory_code()
        if self.db.execute("SELECT 1 FROM book_copies WHERE inventory_code=?", (inventory_code,)).fetchone():
            raise ServiceError("Kode inventaris sudah dipakai.")
        shelf = shelf or b["shelf"]
        cur = self.db.execute(
            "INSERT INTO book_copies(book_id,inventory_code,barcode,shelf,condition,acquired_at,"
            "acquisition_source,updated_by) VALUES (?,?,?,?,?,?,?,?)",
            (book_id, inventory_code, barcode, shelf, condition, acquired_at, acquisition_source,
             actor.id if actor else None))
        if _audit:
            self.audit.log(actor, "copy", cur.lastrowid, "create", None,
                           {"book_id": book_id, "barcode": barcode, "inventory_code": inventory_code})
        return cur.lastrowid

    def list_copies(self, book_id, view="Aktif"):
        sql = "SELECT * FROM book_copies WHERE book_id=?"
        if view == "Aktif":
            sql += " AND archived_at IS NULL"
        elif view == "Keluar koleksi":
            sql += " AND archived_at IS NOT NULL"
        return [dict(r) for r in self.db.execute(sql + " ORDER BY inventory_code", (book_id,))]

    def update_copy(self, actor, copy_id, data):
        """Kembalikan peringatan (list str) misalnya cetak ulang label."""
        old = self.get_copy(copy_id)
        if not old:
            raise ServiceError("Eksemplar tidak ditemukan.")
        warnings, new = [], {}
        if old["archived_at"]:
            raise ServiceError("Eksemplar diarsipkan; pulihkan terlebih dahulu.")
        if "barcode" in data and normalize(data["barcode"]) != old["barcode"]:
            bc = normalize(data["barcode"])
            if not is_valid_barcode(bc):
                raise ServiceError("Barcode harus 8 digit angka.")
            if self.barcode_exists(bc):
                raise ServiceError("Barcode sudah dipakai eksemplar lain.")
            new["barcode"] = bc
            warnings.append("Barcode berubah: cetak ulang label eksemplar ini.")
        if "inventory_code" in data and normalize(data["inventory_code"]) != old["inventory_code"]:
            ic = normalize(data["inventory_code"])
            if not ic:
                raise ServiceError("Kode inventaris wajib diisi.")
            if self.db.execute("SELECT 1 FROM book_copies WHERE inventory_code=?", (ic,)).fetchone():
                raise ServiceError("Kode inventaris sudah dipakai.")
            new["inventory_code"] = ic
            warnings.append("Kode inventaris berubah: cetak ulang label eksemplar ini.")
        if "shelf" in data and (data["shelf"] or None) != old["shelf"]:
            new["shelf"] = data["shelf"] or None
        if "condition" in data and data["condition"] != old["condition"]:
            if data["condition"] not in CONDITIONS:
                raise ServiceError("Kondisi tidak valid.")
            new["condition"] = data["condition"]
        if "circulation_status" in data and data["circulation_status"] != old["circulation_status"]:
            st = data["circulation_status"]
            if old["circulation_status"] == "Dipinjam" or st == "Dipinjam":
                raise ServiceError("Status Dipinjam hanya diubah oleh sirkulasi.")
            if st not in EDITABLE_STATUS:
                raise ServiceError("Status hanya dapat diubah ke Tersedia atau Perbaikan; gunakan Arsipkan untuk lainnya.")
            new["circulation_status"] = st
        if not new:
            return warnings
        with Tx(self.db):
            self.db.execute(f"UPDATE book_copies SET {','.join(k+'=?' for k in new)},updated_at=?,updated_by=? WHERE id=?",
                            list(new.values()) + [now(), actor.id, copy_id])
            self.audit.log(actor, "copy", copy_id, "update", {k: old[k] for k in new}, new)
        return warnings

    def archive_copy(self, actor, copy_id, status="Dihapusbukukan", reason="Lainnya"):
        c = self.get_copy(copy_id)
        if not c:
            raise ServiceError("Eksemplar tidak ditemukan.")
        if c["archived_at"]:
            raise ServiceError("Eksemplar sudah diarsipkan.")
        if status not in ("Hilang", "Dihapusbukukan"):
            raise ServiceError("Status arsip harus Hilang atau Dihapusbukukan.")
        if reason not in ARCHIVE_REASONS:
            raise ServiceError("Alasan arsip tidak valid.")
        if self.copy_is_borrowed(copy_id) or c["circulation_status"] == "Dipinjam":
            raise ServiceError("Eksemplar sedang dipinjam; tidak dapat diarsipkan.")
        with Tx(self.db):
            t = now()
            self.db.execute(
                "UPDATE book_copies SET circulation_status=?, archived_at=?, archived_by=?, archived_reason=?,"
                "updated_at=?, updated_by=? WHERE id=?", (status, t, actor.id, reason, t, actor.id, copy_id))
            self.audit.log(actor, "copy", copy_id, "archive", {"circulation_status": c["circulation_status"]},
                           {"circulation_status": status, "reason": reason})

    def restore_copy(self, actor, copy_id):
        c = self.get_copy(copy_id)
        if not c or not c["archived_at"]:
            raise ServiceError("Eksemplar tidak dalam arsip.")
        b = self.get_book(c["book_id"])
        if not b["is_active"]:
            raise ServiceError("Pulihkan judulnya terlebih dahulu.")
        with Tx(self.db):
            self.db.execute("UPDATE book_copies SET circulation_status='Tersedia', archived_at=NULL,"
                            "archived_by=NULL, archived_reason=NULL, updated_at=?, updated_by=? WHERE id=?",
                            (now(), actor.id, copy_id))
            self.audit.log(actor, "copy", copy_id, "restore", {"circulation_status": c["circulation_status"]},
                           {"circulation_status": "Tersedia"})

    def delete_copy(self, actor, copy_id):
        actor.require_admin()
        c = self.get_copy(copy_id)
        if not c:
            raise ServiceError("Eksemplar tidak ditemukan.")
        if self.copy_is_borrowed(copy_id) or c["circulation_status"] == "Dipinjam":
            raise ServiceError("Eksemplar sedang dipinjam; tidak dapat dihapus.")
        if self.copy_has_history(copy_id):
            raise ServiceError("Eksemplar memiliki riwayat; gunakan Arsipkan.")
        with Tx(self.db):
            self.db.execute("DELETE FROM book_copies WHERE id=?", (copy_id,))
            self.audit.log(actor, "copy", copy_id, "delete", c, None)

    # ---------- massal ----------
    def bulk_update_copies(self, actor, copy_ids, data):
        """Ubah rak/kondisi/status massal. Kembalikan {'ok':n,'skipped':[(id,alasan)]}."""
        ok, skipped = 0, []
        for cid in copy_ids:
            try:
                self.update_copy(actor, cid, data)
                ok += 1
            except ServiceError as e:
                skipped.append((cid, str(e)))
        return {"ok": ok, "skipped": skipped}

    def bulk_remove_copies(self, actor, copy_ids, mode="auto", status="Dihapusbukukan", reason="Lainnya"):
        """mode: 'auto' (hapus jika tanpa riwayat & admin, selain itu arsip), 'archive', 'delete'."""
        ok, skipped = 0, []
        for cid in copy_ids:
            try:
                if mode == "archive":
                    self.archive_copy(actor, cid, status, reason)
                elif mode == "delete":
                    self.delete_copy(actor, cid)
                else:
                    if actor.is_admin and not self.copy_has_history(cid):
                        self.delete_copy(actor, cid)
                    else:
                        self.archive_copy(actor, cid, status, reason)
                ok += 1
            except ServiceError as e:
                skipped.append((cid, str(e)))
        return {"ok": ok, "skipped": skipped}
