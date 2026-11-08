"""Migrasi skema berurutan memakai PRAGMA user_version."""
from .schema import SCHEMA_V1, DEFAULT_SETTINGS


def _v1(conn):
    for stmt in _split(SCHEMA_V1):
        conn.execute(stmt)
    for k, v in DEFAULT_SETTINGS.items():
        conn.execute("INSERT INTO settings(key,value) VALUES (?,?)", (k, v))


def _split(script):
    # skema tidak memiliki trigger sehingga pemisahan berdasarkan ';' aman
    return [s.strip() for s in script.split(";") if s.strip()]


MIGRATIONS = [_v1]   # tambahkan fungsi baru di akhir untuk perubahan skema berikutnya


def current_version(conn) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn) -> int:
    ver = current_version(conn)
    for i, fn in enumerate(MIGRATIONS[ver:], start=ver + 1):
        conn.execute("BEGIN IMMEDIATE")
        try:
            fn(conn)
            conn.execute(f"PRAGMA user_version = {i}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return current_version(conn)
