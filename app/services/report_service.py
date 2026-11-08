"""FR-08 laporan + FR-02 statistik dashboard."""
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .base import ServiceError, today


class ReportService:
    CATEGORIES = {
        "Koleksi dan katalog": ["Daftar bibliografi", "Daftar eksemplar", "Ringkasan inventaris"],
        "Keanggotaan": ["Daftar anggota"],
        "Sirkulasi": ["Peminjaman", "Pengembalian", "Keterlambatan", "Buku paling sering dipinjam"],
        "Keuangan dan denda": ["Denda dan pembayaran"],
        "Stok opname": ["Stok opname dan selisih"],
        "Audit aktivitas": ["Log audit"],
    }

    def __init__(self, db, settings, loans, fines, opname):
        self.db, self.settings, self.loans, self.fines, self.opname = db, settings, loans, fines, opname

    # ---------- dashboard ----------
    def dashboard(self):
        q = lambda sql, *a: self.db.execute(sql, a).fetchone()[0]
        d = {
            "titles": q("SELECT COUNT(*) FROM books WHERE is_active=1"),
            "copies": q("SELECT COUNT(*) FROM book_copies WHERE archived_at IS NULL"),
            "available": q("SELECT COUNT(*) FROM book_copies WHERE archived_at IS NULL AND circulation_status='Tersedia'"),
            "borrowed": q("SELECT COUNT(*) FROM book_copies WHERE circulation_status='Dipinjam'"),
            "members": q("SELECT COUNT(*) FROM members WHERE is_active=1"),
            "loans_today": q("SELECT COUNT(*) FROM loans WHERE loan_date=?", today()),
            "overdue": len(self.loans.overdue()),
            "fines": self.fines.summary(),
        }
        monthly = self.db.execute(
            "SELECT substr(loan_date,1,7) m, COUNT(*) n FROM loan_items li JOIN loans l ON l.id=li.loan_id "
            "GROUP BY m ORDER BY m DESC LIMIT 6").fetchall()
        d["monthly"] = [(r["m"], r["n"]) for r in reversed(monthly)]
        s = self.opname.active_session()
        d["opname"] = ({"session": s, **self.opname.progress(s["id"])} if s else None)
        return d

    # ---------- laporan ----------
    def generate(self, name, date_from=None, date_to=None):
        """Kembalikan (judul, header, baris). Filter tanggal berlaku untuk laporan sirkulasi/denda/log."""
        f, t = date_from or "0000-01-01", date_to or "9999-12-31"
        q = lambda sql, args=(): [tuple(r) for r in self.db.execute(sql, args)]
        if name == "Daftar bibliografi":
            return name, ["ISBN", "Judul", "Penulis", "Penerbit", "Tahun", "Kategori", "Rak", "Aktif"], q(
                "SELECT isbn,title,author,publisher,year,category,shelf,CASE is_active WHEN 1 THEN 'Ya' ELSE 'Arsip' END FROM books ORDER BY title")
        if name == "Daftar eksemplar":
            return name, ["Barcode", "Kode Inventaris", "Judul", "Rak", "Status", "Kondisi"], q(
                "SELECT c.barcode,c.inventory_code,b.title,c.shelf,c.circulation_status,c.condition "
                "FROM book_copies c JOIN books b ON b.id=c.book_id ORDER BY c.inventory_code")
        if name == "Ringkasan inventaris":
            return name, ["Status", "Kondisi", "Jumlah"], q(
                "SELECT circulation_status,condition,COUNT(*) FROM book_copies GROUP BY 1,2 ORDER BY 1,2")
        if name == "Daftar anggota":
            return name, ["No. Anggota", "Nama", "Jenis", "Telepon", "Email", "Terdaftar", "Aktif"], q(
                "SELECT member_no,name,member_type,phone,email,registered_at,CASE is_active WHEN 1 THEN 'Ya' ELSE 'Nonaktif' END FROM members ORDER BY name")
        if name == "Peminjaman":
            return name, ["Tgl Pinjam", "Jatuh Tempo", "Anggota", "Judul", "Barcode", "Petugas"], q(
                "SELECT l.loan_date,l.due_date,m.name,b.title,c.barcode,u.username FROM loan_items li JOIN loans l ON l.id=li.loan_id "
                "JOIN members m ON m.id=l.member_id JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id "
                "LEFT JOIN users u ON u.id=l.user_id WHERE l.loan_date BETWEEN ? AND ? ORDER BY l.loan_date", (f, t))
        if name == "Pengembalian":
            return name, ["Tgl Kembali", "Anggota", "Judul", "Barcode", "Kondisi", "Denda"], q(
                "SELECT li.returned_at,m.name,b.title,c.barcode,li.return_condition,COALESCE(f.amount,0) FROM loan_items li "
                "JOIN loans l ON l.id=li.loan_id JOIN members m ON m.id=l.member_id JOIN book_copies c ON c.id=li.copy_id "
                "JOIN books b ON b.id=c.book_id LEFT JOIN fines f ON f.loan_item_id=li.id "
                "WHERE li.returned_at BETWEEN ? AND ? ORDER BY li.returned_at", (f, t))
        if name == "Keterlambatan":
            rows = [(r["due_date"], r["member_name"], r["title"], r["barcode"], r["days_late"], r["projected_fine"])
                    for r in self.loans.overdue()]
            return name, ["Jatuh Tempo", "Anggota", "Judul", "Barcode", "Hari Terlambat", "Denda Proyeksi"], rows
        if name == "Buku paling sering dipinjam":
            return name, ["Judul", "Penulis", "Jumlah Dipinjam"], q(
                "SELECT b.title,b.author,COUNT(*) n FROM loan_items li JOIN loans l ON l.id=li.loan_id "
                "JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id "
                "WHERE l.loan_date BETWEEN ? AND ? GROUP BY b.id ORDER BY n DESC, b.title LIMIT 50", (f, t))
        if name == "Denda dan pembayaran":
            return name, ["Ditetapkan", "Anggota", "Judul", "Jenis", "Nominal", "Dibayar", "Sisa", "Status"], q(
                "SELECT substr(f.assessed_at,1,10),m.name,b.title,f.kind,f.amount,"
                "COALESCE((SELECT SUM(amount) FROM fine_payments p WHERE p.fine_id=f.id),0) paid,"
                "f.amount-COALESCE((SELECT SUM(amount) FROM fine_payments p WHERE p.fine_id=f.id),0),f.status "
                "FROM fines f JOIN loan_items li ON li.id=f.loan_item_id JOIN loans l ON l.id=li.loan_id "
                "JOIN members m ON m.id=l.member_id JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id "
                "WHERE substr(f.assessed_at,1,10) BETWEEN ? AND ? ORDER BY f.id", (f, t))
        if name == "Stok opname dan selisih":
            return name, ["Sesi", "Barcode", "Judul", "Hasil", "Kondisi fisik", "Status verifikasi"], q(
                "SELECT s.name,i.barcode_snapshot,i.book_title_snapshot,i.result,i.physical_condition,i.verification_status "
                "FROM stock_opname_items i JOIN stock_opname_sessions s ON s.id=i.session_id "
                "WHERE i.result NOT IN ('Ditemukan') ORDER BY s.year DESC, i.result, i.book_title_snapshot")
        if name == "Log audit":
            return name, ["Waktu", "Pengguna", "Entitas", "ID", "Aksi", "Nilai lama", "Nilai baru"], q(
                "SELECT a.created_at,u.username,a.entity,a.entity_id,a.action,a.old_value,a.new_value FROM audit_logs a "
                "LEFT JOIN users u ON u.id=a.user_id WHERE substr(a.created_at,1,10) BETWEEN ? AND ? ORDER BY a.id DESC", (f, t))
        raise ServiceError(f"Laporan '{name}' tidak dikenal.")

    def _meta(self, actor):
        return f"Dibuat {datetime.now():%Y-%m-%d %H:%M} oleh {actor.full_name or actor.username if actor else '-'}"

    def export_xlsx(self, path, name, actor=None, date_from=None, date_to=None):
        title, headers, rows = self.generate(name, date_from, date_to)
        wb = Workbook(); ws = wb.active; ws.title = title[:31]
        ws.append([self.settings.get("library_name", "Perpustakaan") + " — " + title])
        ws["A1"].font = Font(bold=True, size=13)
        ws.append([self._meta(actor)])
        ws.append([])
        ws.append(headers)
        for c in ws[4]:
            c.font = Font(bold=True)
        for r in rows:
            ws.append(list(r))
        for i, h in enumerate(headers, 1):
            width = max([len(str(h))] + [len(str(r[i - 1])) for r in rows[:200] if r[i - 1] is not None]) + 2
            ws.column_dimensions[ws.cell(row=4, column=i).column_letter].width = min(width, 50)
        wb.save(path)
        return len(rows)

    def export_pdf(self, path, name, actor=None, date_from=None, date_to=None):
        title, headers, rows = self.generate(name, date_from, date_to)
        st = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
        cell = st["BodyText"]; cell.fontSize = 7; cell.leading = 9
        data = [[Paragraph(f"<b>{h}</b>", cell) for h in headers]] + \
               [[Paragraph(str("" if v is None else v).replace("&", "&amp;").replace("<", "&lt;"), cell) for v in r] for r in rows]
        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                                 ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                                 ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        doc.build([Paragraph(f"{self.settings.get('library_name', 'Perpustakaan')} — {title}", st["Title"]),
                   Paragraph(self._meta(actor), st["Normal"]), Spacer(1, 8), tbl])
        return len(rows)
