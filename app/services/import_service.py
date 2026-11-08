"""FR-11: impor Excel dengan dry-run dan transaksi atomik."""
from openpyxl import Workbook, load_workbook

from app.database.connection import Tx
from app.utils.barcode import is_valid_barcode, normalize
from app.utils.validators import clean_isbn, isbn_valid
from .base import ServiceError

COLUMNS = [("isbn", "ISBN"), ("title", "Judul*"), ("author", "Penulis"), ("publisher", "Penerbit"),
           ("year", "Tahun"), ("category", "Kategori"), ("shelf", "Rak"), ("barcode", "Barcode (8 digit)"),
           ("inventory_code", "Kode Inventaris"), ("condition", "Kondisi")]
KEYS = [k for k, _ in COLUMNS]


class ImportService:
    def __init__(self, db, audit, books):
        self.db, self.audit, self.books = db, audit, books

    def write_template(self, path):
        wb = Workbook(); ws = wb.active; ws.title = "Impor"
        ws.append([h for _, h in COLUMNS])
        ws.append(["9786020333175", "Contoh Judul Buku", "Nama Penulis", "Penerbit", 2020, "Umum", "A-01", "", "", "Baik"])
        wb.save(path)

    def read_rows(self, path, mapping=None):
        """mapping: {kunci_internal: indeks_kolom}. Bawaan: urutan templat."""
        ws = load_workbook(path, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ServiceError("Berkas kosong.")
        mapping = mapping or {k: i for i, k in enumerate(KEYS)}
        out = []
        for n, r in enumerate(rows[1:], start=2):
            if all(v in (None, "") for v in r):
                continue
            d = {k: (r[i] if i < len(r) else None) for k, i in mapping.items()}
            d = {k: (str(v).strip() if v not in (None, "") else None) for k, v in d.items()}
            d["_row"] = n
            out.append(d)
        return out

    def dry_run(self, rows):
        """Validasi tanpa menyimpan. Kembalikan {'rows':[{row,status,messages}],'errors':n,'new_categories':[..]}"""
        seen_bc, seen_inv, seen_isbn = set(), set(), {}
        known_cats = set(self.books.categories()); known_shelves = set(self.books.shelves())
        result, errors, new_cat, new_shelf = [], 0, set(), set()
        for d in rows:
            msgs = []
            if not d.get("title"):
                msgs.append("Judul wajib diisi.")
            isbn = clean_isbn(d.get("isbn"))
            if not isbn_valid(isbn):
                msgs.append("ISBN tidak valid.")
            if d.get("year") and not str(d["year"]).split(".")[0].isdigit():
                msgs.append("Tahun harus angka.")
            bc = normalize(d.get("barcode"))
            if bc:
                if not is_valid_barcode(bc):
                    msgs.append("Barcode harus 8 digit angka.")
                elif bc in seen_bc or self.books.barcode_exists(bc):
                    msgs.append("Barcode ganda.")
                seen_bc.add(bc)
            inv = normalize(d.get("inventory_code"))
            if inv:
                if inv in seen_inv or self.db.execute("SELECT 1 FROM book_copies WHERE inventory_code=?", (inv,)).fetchone():
                    msgs.append("Kode inventaris ganda.")
                seen_inv.add(inv)
            if d.get("condition") and d["condition"] not in ("Baik", "Rusak ringan", "Rusak sedang", "Rusak berat", "Tidak layak pakai"):
                msgs.append("Kondisi tidak valid.")
            if isbn:
                existing = self.db.execute("SELECT id FROM books WHERE isbn=?", (isbn,)).fetchone()
                if existing:
                    d["_book_id"] = existing["id"]
                elif isbn in seen_isbn and seen_isbn[isbn] != d.get("title"):
                    msgs.append("ISBN sama dengan judul lain pada berkas.")
                seen_isbn[isbn] = d.get("title")
            if d.get("category") and d["category"] not in known_cats:
                new_cat.add(d["category"])
            if d.get("shelf") and d["shelf"] not in known_shelves:
                new_shelf.add(d["shelf"])
            errors += bool(msgs)
            result.append({"row": d["_row"], "status": "Error" if msgs else "OK", "messages": msgs})
        return {"rows": result, "errors": errors, "new_categories": sorted(new_cat), "new_shelves": sorted(new_shelf)}

    def commit(self, actor, rows):
        report = self.dry_run(rows)
        if report["errors"]:
            raise ServiceError(f"Impor dibatalkan: {report['errors']} baris bermasalah. Perbaiki lalu ulangi.")
        created_books = created_copies = 0
        with Tx(self.db):
            by_isbn = {}
            for d in rows:
                isbn = clean_isbn(d.get("isbn"))
                book_id = d.get("_book_id") or (by_isbn.get(isbn) if isbn else None)
                if not book_id:
                    book_id = self.books.add_book(actor, {
                        "isbn": isbn, "title": d["title"], "author": d.get("author"), "publisher": d.get("publisher"),
                        "year": (str(d["year"]).split(".")[0] if d.get("year") else None),
                        "category": d.get("category"), "shelf": d.get("shelf")})
                    created_books += 1
                    if isbn:
                        by_isbn[isbn] = book_id
                self.books.add_copy(actor, book_id, barcode=d.get("barcode"), inventory_code=d.get("inventory_code"),
                                    shelf=d.get("shelf"), condition=d.get("condition") or "Baik", _audit=False)
                created_copies += 1
            self.audit.log(actor, "import", None, "import", None, {"books": created_books, "copies": created_copies})
        return {"books": created_books, "copies": created_copies}
