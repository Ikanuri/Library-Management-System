from .base import ServiceError


class SettingsService:
    def __init__(self, db, audit=None):
        self.db, self.audit = db, audit

    def get(self, key, default=None):
        r = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def get_int(self, key, default=0):
        try:
            return int(self.get(key, default))
        except (TypeError, ValueError):
            return default

    def all(self):
        return {r["key"]: r["value"] for r in self.db.execute("SELECT key,value FROM settings")}

    def set(self, key, value, actor=None):
        value = str(value)
        if key in ("loan_days", "fine_rate", "fine_cap", "grace_days", "max_loans_per_member",
                   "backup_retention"):
            if not value.isdigit():
                raise ServiceError(f"Pengaturan '{key}' harus berupa bilangan bulat tidak negatif.")
            if key in ("loan_days", "max_loans_per_member") and int(value) < 1:
                raise ServiceError(f"Pengaturan '{key}' minimal 1.")
        old = self.get(key)
        self.db.execute("INSERT INTO settings(key,value) VALUES (?,?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        if self.audit and old != value:
            self.audit.log(actor, "settings", key, "update", {"value": old}, {"value": value})
