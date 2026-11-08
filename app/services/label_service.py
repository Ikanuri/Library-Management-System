"""FR-11: cetak label barcode (PDF, ReportLab)."""
import io

from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.utils.barcode import code128_png
from .base import ServiceError


class LabelService:
    def __init__(self, db):
        self.db = db

    def copies_for(self, book_ids=None, copy_ids=None):
        sql = ("SELECT c.barcode, c.inventory_code, c.shelf, b.title FROM book_copies c JOIN books b ON b.id=c.book_id "
               "WHERE c.archived_at IS NULL")
        args = []
        if book_ids:
            sql += f" AND c.book_id IN ({','.join('?'*len(book_ids))})"; args += list(book_ids)
        if copy_ids:
            sql += f" AND c.id IN ({','.join('?'*len(copy_ids))})"; args += list(copy_ids)
        return [dict(r) for r in self.db.execute(sql + " ORDER BY c.inventory_code", args)]

    def make_pdf(self, path, copies, label_w_mm=60, label_h_mm=30, cols=3, margin_mm=10, test_page=False):
        """Lembar A4 berisi label. test_page=True hanya mencetak satu baris pertama untuk uji pindai."""
        if not copies:
            raise ServiceError("Tidak ada eksemplar untuk dicetak.")
        from reportlab.lib.pagesizes import A4
        W, H = A4
        lw, lh, m = label_w_mm * mm, label_h_mm * mm, margin_mm * mm
        rows = max(1, int((H - 2 * m) // lh))
        per_page = cols * rows
        if test_page:
            copies = copies[:cols]
        c = canvas.Canvas(str(path), pagesize=A4)
        for idx, cp in enumerate(copies):
            pos = idx % per_page
            if idx and pos == 0:
                c.showPage()
            col, row = pos % cols, pos // cols
            x, y = m + col * lw, H - m - (row + 1) * lh
            c.rect(x, y, lw, lh)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x + 2 * mm, y + lh - 4 * mm, (cp["title"] or "")[:34])
            img = ImageReader(io.BytesIO(code128_png(cp["barcode"])))
            c.drawImage(img, x + 2 * mm, y + 8 * mm, width=lw - 4 * mm, height=lh - 14 * mm, preserveAspectRatio=True)
            c.setFont("Helvetica", 7)
            c.drawString(x + 2 * mm, y + 3 * mm, f"{cp['inventory_code']}  {cp['barcode']}")
            c.drawRightString(x + lw - 2 * mm, y + 3 * mm, cp.get("shelf") or "")
        c.save()
        return path
