from datetime import datetime, timedelta

from app.database.connection import Tx
from app.utils.security import hash_password, verify_password
from .base import Actor, ServiceError, now

MAX_ATTEMPTS = 5
LOCK_MINUTES = 5


class AuthService:
    def __init__(self, db, audit):
        self.db, self.audit = db, audit

    def user_count(self):
        return self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_user(self, actor, username, password, full_name, role="staff"):
        if actor is not None:
            actor.require_admin()
        username = (username or "").strip()
        if not username or not full_name.strip():
            raise ServiceError("Username dan nama wajib diisi.")
        if len(password) < 6:
            raise ServiceError("Password minimal 6 karakter.")
        if role not in ("admin", "staff"):
            raise ServiceError("Peran tidak valid.")
        if self.db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            raise ServiceError("Username sudah dipakai.")
        with Tx(self.db):
            cur = self.db.execute(
                "INSERT INTO users(username,password_hash,full_name,role) VALUES (?,?,?,?)",
                (username, hash_password(password), full_name.strip(), role))
            self.audit.log(actor, "user", cur.lastrowid, "create", None,
                           {"username": username, "role": role})
        return cur.lastrowid

    def login(self, username, password) -> Actor:
        row = self.db.execute("SELECT * FROM users WHERE username=?", ((username or "").strip(),)).fetchone()
        if row is None:
            raise ServiceError("Username atau password salah.")
        if row["locked_until"] and datetime.fromisoformat(row["locked_until"]) > datetime.now():
            raise ServiceError("Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.")
        if not row["is_active"]:
            raise ServiceError("Akun nonaktif.")
        if not verify_password(password, row["password_hash"]):
            attempts = row["failed_attempts"] + 1
            locked = None
            if attempts >= MAX_ATTEMPTS:
                locked = (datetime.now() + timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds")
                attempts = 0
            self.db.execute("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
                            (attempts, locked, row["id"]))
            raise ServiceError("Username atau password salah.")
        self.db.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?", (row["id"],))
        actor = Actor(row["id"], row["role"], row["username"], row["full_name"])
        self.audit.log(actor, "user", row["id"], "login")
        return actor

    def logout(self, actor):
        self.audit.log(actor, "user", actor.id, "logout")

    def list_users(self):
        return [dict(r) for r in self.db.execute(
            "SELECT id,username,full_name,role,is_active,created_at FROM users ORDER BY username")]

    def set_active(self, actor, user_id, active):
        actor.require_admin()
        if user_id == actor.id and not active:
            raise ServiceError("Tidak dapat menonaktifkan akun sendiri.")
        self.db.execute("UPDATE users SET is_active=?, updated_at=? WHERE id=?", (1 if active else 0, now(), user_id))
        self.audit.log(actor, "user", user_id, "activate" if active else "deactivate")

    def change_password(self, actor, user_id, new_password):
        if actor.id != user_id:
            actor.require_admin()
        if len(new_password) < 6:
            raise ServiceError("Password minimal 6 karakter.")
        self.db.execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
                        (hash_password(new_password), now(), user_id))
        self.audit.log(actor, "user", user_id, "change_password")
