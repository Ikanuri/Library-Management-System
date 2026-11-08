import sqlite3
from pathlib import Path


def connect(path) -> sqlite3.Connection:
    """Buka koneksi SQLite dengan foreign key aktif di setiap koneksi."""
    conn = sqlite3.connect(str(path) if not isinstance(path, Path) else path,
                           isolation_level=None)  # transaksi dikelola manual
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if str(path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


class Tx:
    """Transaksi atomik: commit bila sukses, rollback bila gagal. Mendukung nesting (SAVEPOINT)."""

    def __init__(self, conn):
        self.conn = conn
        self.nested = False
        self.name = ""

    def __enter__(self):
        if self.conn.in_transaction:
            self.nested = True
            self.name = f"sp_{id(self)}"
            self.conn.execute(f"SAVEPOINT {self.name}")
        else:
            self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, et, ev, tb):
        if self.nested:
            if et is None:
                self.conn.execute(f"RELEASE {self.name}")
            else:
                self.conn.execute(f"ROLLBACK TO {self.name}")
                self.conn.execute(f"RELEASE {self.name}")
        elif et is None:
            self.conn.execute("COMMIT")
        else:
            self.conn.execute("ROLLBACK")
        return False
