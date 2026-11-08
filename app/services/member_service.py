"""FR-04: anggota."""
from app.database.connection import Tx
from .base import ServiceError, row_dict

FIELDS = ["member_no", "name", "member_type", "address", "phone", "email", "notes"]


class MemberService:
    def __init__(self, db, audit):
        self.db, self.audit = db, audit

    def _check(self, data, member_id=None):
        if not (data.get("member_no") or "").strip() or not (data.get("name") or "").strip():
            raise ServiceError("Nomor anggota dan nama wajib diisi.")
        if self.db.execute("SELECT 1 FROM members WHERE member_no=? AND id<>?",
                           (data["member_no"].strip(), member_id or -1)).fetchone():
            raise ServiceError("Nomor anggota sudah dipakai.")

    def add(self, actor, data):
        self._check(data)
        vals = {k: ((data.get(k) or "").strip() or None) for k in FIELDS}
        vals["member_type"] = vals["member_type"] or "Umum"
        with Tx(self.db):
            cur = self.db.execute(f"INSERT INTO members({','.join(FIELDS)}) VALUES ({','.join('?'*len(FIELDS))})",
                                  [vals[k] for k in FIELDS])
            self.audit.log(actor, "member", cur.lastrowid, "create", None, vals)
        return cur.lastrowid

    def get(self, member_id):
        return row_dict(self.db.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone())

    def find_by_no(self, member_no):
        return row_dict(self.db.execute("SELECT * FROM members WHERE member_no=?",
                                        ((member_no or "").strip(),)).fetchone())

    def update(self, actor, member_id, data):
        old = self.get(member_id)
        if not old:
            raise ServiceError("Anggota tidak ditemukan.")
        merged = {**old, **data}
        self._check(merged, member_id)
        new = {k: ((merged.get(k) or "").strip() or None) for k in FIELDS}
        new["member_type"] = new["member_type"] or "Umum"
        with Tx(self.db):
            self.db.execute(f"UPDATE members SET {','.join(k+'=?' for k in FIELDS)} WHERE id=?",
                            [new[k] for k in FIELDS] + [member_id])
            self.audit.log(actor, "member", member_id, "update", {k: old[k] for k in FIELDS}, new)

    def set_active(self, actor, member_id, active):
        if not self.get(member_id):
            raise ServiceError("Anggota tidak ditemukan.")
        self.db.execute("UPDATE members SET is_active=? WHERE id=?", (1 if active else 0, member_id))
        self.audit.log(actor, "member", member_id, "activate" if active else "deactivate")

    def list(self, search="", status="Semua"):
        sql = ("SELECT m.*, (SELECT COUNT(*) FROM loan_items li JOIN loans l ON l.id=li.loan_id "
               "WHERE l.member_id=m.id AND li.returned_at IS NULL) AS active_loans FROM members m WHERE 1=1")
        args = []
        if status == "Aktif":
            sql += " AND m.is_active=1"
        elif status == "Nonaktif":
            sql += " AND m.is_active=0"
        s = (search or "").strip()
        if s:
            sql += " AND (m.name LIKE ? OR m.member_no LIKE ? OR IFNULL(m.phone,'') LIKE ?)"
            args += [f"%{s}%"] * 3
        return [dict(r) for r in self.db.execute(sql + " ORDER BY m.name", args)]

    def history(self, member_id):
        return [dict(r) for r in self.db.execute(
            """SELECT l.id AS loan_id, l.loan_date, l.due_date, li.returned_at, b.title, c.barcode,
                      f.amount AS fine_amount, f.status AS fine_status
               FROM loans l JOIN loan_items li ON li.loan_id=l.id
               JOIN book_copies c ON c.id=li.copy_id JOIN books b ON b.id=c.book_id
               LEFT JOIN fines f ON f.loan_item_id=li.id
               WHERE l.member_id=? ORDER BY l.id DESC""", (member_id,))]
