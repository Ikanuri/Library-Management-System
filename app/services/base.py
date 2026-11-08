import json
from datetime import date, datetime


class ServiceError(Exception):
    """Kesalahan aturan bisnis yang aman ditampilkan kepada petugas."""


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today() -> str:
    return date.today().isoformat()


def parse_date(s) -> date:
    if isinstance(s, date):
        return s
    return date.fromisoformat(str(s)[:10])


def js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def row_dict(row):
    return dict(row) if row is not None else None


class Actor:
    """Pengguna yang sedang bertindak (id + peran)."""

    def __init__(self, id: int, role: str, username: str = "", full_name: str = ""):
        self.id, self.role, self.username, self.full_name = id, role, username, full_name

    @property
    def is_admin(self):
        return self.role == "admin"

    def require_admin(self):
        if not self.is_admin:
            raise ServiceError("Hanya Administrator yang dapat melakukan tindakan ini.")
