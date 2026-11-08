"""Perakitan semua service di atas satu koneksi database."""
from pathlib import Path

from app.database.connection import connect
from app.database.migrations import migrate
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService
from app.services.book_service import BookService
from app.services.fine_service import FineService
from app.services.import_service import ImportService
from app.services.label_service import LabelService
from app.services.loan_service import LoanService
from app.services.member_service import MemberService
from app.services.report_service import ReportService
from app.services.return_service import ReturnService
from app.services.settings_service import SettingsService
from app.services.stock_opname_service import StockOpnameService


class Services:
    def __init__(self, db_path, backup_dir=None):
        self.db_path = Path(db_path) if str(db_path) != ":memory:" else db_path
        self.backup_dir = backup_dir or (Path(db_path).parent / "backups" if str(db_path) != ":memory:" else "backups")
        self.db = connect(db_path)
        migrate(self.db)
        self._build()

    def _build(self):
        db = self.db
        self.audit = AuditService(db)
        self.settings = SettingsService(db, self.audit)
        self.auth = AuthService(db, self.audit)
        self.books = BookService(db, self.audit)
        self.members = MemberService(db, self.audit)
        self.fines = FineService(db, self.audit, self.settings)
        self.loans = LoanService(db, self.audit, self.settings)
        self.returns = ReturnService(db, self.audit, self.settings, self.fines)
        self.opname = StockOpnameService(db, self.audit)
        self.reports = ReportService(db, self.settings, self.loans, self.fines, self.opname)
        self.imports = ImportService(db, self.audit, self.books)
        self.labels = LabelService(db)
        self.backups = BackupService(db, self.db_path, self.backup_dir, self.settings, self.audit)

    def restore(self, actor, path):
        self.db = self.backups.restore(actor, path)
        self._build()

    def close(self):
        self.db.close()
