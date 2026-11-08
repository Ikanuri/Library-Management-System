"""FR-09: backup dan restore memakai SQLite Backup API."""
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.database.connection import connect
from .base import ServiceError


class BackupService:
    def __init__(self, db, db_path, default_dir, settings, audit):
        self.db, self.db_path, self.default_dir = db, Path(db_path), Path(default_dir)
        self.settings, self.audit = settings, audit

    def backup_dir(self):
        d = Path(self.settings.get("backup_dir") or self.default_dir)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def backup(self, actor=None, kind="manual", dest_dir=None):
        dest_dir = Path(dest_dir) if dest_dir else self.backup_dir()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"libris_{datetime.now():%Y%m%d_%H%M%S_%f}_{kind}.db"
        out = sqlite3.connect(str(dest))
        try:
            self.db.backup(out)
        finally:
            out.close()
        if not self.validate(dest):
            dest.unlink(missing_ok=True)
            raise ServiceError("Backup gagal diverifikasi.")
        self.db.execute("INSERT INTO backup_history(path,kind,size_bytes) VALUES (?,?,?)",
                        (str(dest), kind, dest.stat().st_size))
        self.audit.log(actor, "backup", dest.name, "backup", None, {"kind": kind})
        self._prune(dest_dir)
        return dest

    def _prune(self, d):
        keep = max(1, self.settings.get_int("backup_retention", 10))
        files = sorted(d.glob("libris_*.db"))
        for f in files[:-keep]:
            f.unlink(missing_ok=True)

    @staticmethod
    def validate(path) -> bool:
        """File harus berupa database SQLite yang lulus integrity_check dan berskema Libris."""
        try:
            c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    return False
                tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                return {"books", "book_copies", "members", "users"} <= tables
            finally:
                c.close()
        except sqlite3.Error:
            return False

    def restore(self, actor, backup_path):
        """Kembalikan database dari backup. Mengembalikan koneksi baru; database aktif diamankan lebih dulu."""
        actor.require_admin()
        backup_path = Path(backup_path)
        if not backup_path.is_file() or not self.validate(backup_path):
            raise ServiceError("File bukan backup Libris yang valid; database aktif tidak diubah.")
        safety = self.backup(actor, kind="pra-restore")
        tmp = self.db_path.with_suffix(".restore.tmp")
        shutil.copyfile(backup_path, tmp)
        self.db.close()
        for ext in ("-wal", "-shm"):
            Path(str(self.db_path) + ext).unlink(missing_ok=True)
        os.replace(tmp, self.db_path)
        new = connect(self.db_path)
        if new.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ServiceError(f"Integritas gagal setelah restore; salinan pengaman: {safety}")
        return new

    def history(self, limit=50):
        return [dict(r) for r in self.db.execute("SELECT * FROM backup_history ORDER BY id DESC LIMIT ?", (limit,))]

    def last_backup_age_days(self):
        r = self.db.execute("SELECT MAX(created_at) FROM backup_history WHERE kind<>'pra-restore'").fetchone()[0]
        if not r:
            return None
        return (datetime.now() - datetime.fromisoformat(r)).days

    def warnings(self):
        out = []
        age = self.last_backup_age_days()
        if age is None:
            out.append("Belum pernah ada backup.")
        elif age > 7:
            out.append(f"Backup terakhir {age} hari lalu (lebih dari 7 hari).")
        if self.same_drive(self.backup_dir(), self.db_path):
            out.append("Folder backup berada pada drive yang sama dengan database; salin juga ke media eksternal.")
        return out

    @staticmethod
    def same_drive(a, b):
        try:
            return os.stat(a).st_dev == os.stat(Path(b).parent).st_dev
        except OSError:
            return True
