"""FR-10: stok opname tahunan (proposal 3.10)."""
from app.database.connection import Tx
from app.utils.barcode import normalize
from .base import ServiceError, now, today
from .book_service import CONDITIONS

DAMAGE_PROPOSAL = {"Rusak berat": "Perbaikan", "Tidak layak pakai": "Dihapusbukukan"}


class StockOpnameService:
    def __init__(self, db, audit):
        self.db, self.audit = db, audit

    # ---------- sesi ----------
    def create_session(self, actor, year, name=None, notes=None):
        year = int(year)
        if self.db.execute("SELECT 1 FROM stock_opname_sessions WHERE year=? AND status<>'Final'", (year,)).fetchone():
            raise ServiceError(f"Sudah ada sesi opname aktif untuk tahun {year}.")
        name = (name or f"Stok Opname Tahun {year}").strip()
        with Tx(self.db):
            cur = self.db.execute(
                "INSERT INTO stock_opname_sessions(year,name,start_date,created_by,notes) VALUES (?,?,?,?,?)",
                (year, name, today(), actor.id, notes))
            sid = cur.lastrowid
            self.db.execute(
                """INSERT INTO stock_opname_items(session_id,copy_id,barcode_snapshot,book_title_snapshot,
                       inventory_code_snapshot,location_snapshot,circulation_status_snapshot,result)
                   SELECT ?, c.id, c.barcode, b.title, c.inventory_code, c.shelf, c.circulation_status,
                          CASE WHEN c.circulation_status='Dipinjam' THEN 'Dipinjam' ELSE 'Belum diperiksa' END
                   FROM book_copies c JOIN books b ON b.id=c.book_id WHERE c.archived_at IS NULL""", (sid,))
            n = self.db.execute("SELECT COUNT(*) FROM stock_opname_items WHERE session_id=?", (sid,)).fetchone()[0]
            self.audit.log(actor, "opname", sid, "create", None, {"year": year, "snapshot": n})
        return sid

    def get_session(self, sid):
        r = self.db.execute("SELECT * FROM stock_opname_sessions WHERE id=?", (sid,)).fetchone()
        return dict(r) if r else None

    def active_session(self):
        r = self.db.execute("SELECT * FROM stock_opname_sessions WHERE status<>'Final' ORDER BY id DESC").fetchone()
        return dict(r) if r else None

    def sessions(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM stock_opname_sessions ORDER BY year DESC, id DESC")]

    def _open_session(self, sid):
        s = self.get_session(sid)
        if not s:
            raise ServiceError("Sesi opname tidak ditemukan.")
        if s["status"] == "Final":
            raise ServiceError("Sesi sudah final dan terkunci.")
        return s

    # ---------- pemindaian ----------
    def scan(self, actor, sid, code, condition="Baik", actual_location=None, notes=None):
        """Hasil: dict(status=ok|duplikat|dipinjam|ekstra_dikenal|tidak_dikenal, message=...)."""
        self._open_session(sid)
        if condition not in CONDITIONS:
            raise ServiceError("Kondisi tidak valid.")
        code = normalize(code)
        if not code:
            raise ServiceError("Kode kosong.")
        item = self.db.execute(
            "SELECT * FROM stock_opname_items WHERE session_id=? AND (barcode_snapshot=? OR UPPER(inventory_code_snapshot)=?)",
            (sid, code, code)).fetchone()

        def log(outcome):
            self.db.execute("INSERT INTO stock_opname_scans(session_id,barcode,scanned_by,outcome) VALUES (?,?,?,?)",
                            (sid, code, actor.id, outcome))

        with Tx(self.db):
            if item is None:
                known = self.db.execute("SELECT c.id,b.title FROM book_copies c JOIN books b ON b.id=c.book_id "
                                        "WHERE c.barcode=? OR UPPER(c.inventory_code)=?", (code, code)).fetchone()
                if known:
                    log("Tidak ada di snapshot")
                    return {"status": "ekstra_dikenal", "message": f"{code} ({known['title']}) tidak ada dalam snapshot."}
                log("Tidak dikenal")
                return {"status": "tidak_dikenal", "message": f"Barcode {code} tidak dikenal."}
            if item["result"] in ("Ditemukan", "Ditemukan ekstra"):
                log("Duplikat")
                return {"status": "duplikat", "message": f"{item['barcode_snapshot']} sudah dipindai sebelumnya."}
            if item["result"] == "Dipinjam":
                log("Dipinjam")
                return {"status": "dipinjam",
                        "message": f"{item['book_title_snapshot']} tercatat sedang dipinjam; diverifikasi lewat sirkulasi."}
            self.db.execute(
                "UPDATE stock_opname_items SET result='Ditemukan', physical_condition=?, actual_location=?, notes=?,"
                "inspected_by=?, inspected_at=? WHERE id=?",
                (condition, actual_location, notes, actor.id, now(), item["id"]))
            log("Ditemukan")
        return {"status": "ok", "message": f"{item['book_title_snapshot']} ({item['barcode_snapshot']}) ditemukan.",
                "item_id": item["id"]}

    def record_extra(self, actor, sid, code, condition="Baik", notes=None):
        """Catat temuan ekstra: barcode dikenal tapi di luar snapshot, atau tidak dikenal."""
        self._open_session(sid)
        code = normalize(code)
        if self.db.execute("SELECT 1 FROM stock_opname_items WHERE session_id=? AND barcode_snapshot=?",
                           (sid, code)).fetchone():
            raise ServiceError("Barcode ini sudah tercatat pada sesi.")
        known = self.db.execute("SELECT c.id,b.title,c.inventory_code,c.shelf FROM book_copies c "
                                "JOIN books b ON b.id=c.book_id WHERE c.barcode=?", (code,)).fetchone()
        with Tx(self.db):
            self.db.execute(
                "INSERT INTO stock_opname_items(session_id,copy_id,barcode_snapshot,book_title_snapshot,"
                "inventory_code_snapshot,location_snapshot,result,physical_condition,notes,inspected_by,inspected_at)"
                " VALUES (?,?,?,?,?,?,'Ditemukan ekstra',?,?,?,?)",
                (sid, known["id"] if known else None, code, known["title"] if known else "(tidak dikenal)",
                 known["inventory_code"] if known else None, known["shelf"] if known else None,
                 condition, notes, actor.id, now()))
            self.db.execute("INSERT INTO stock_opname_scans(session_id,barcode,scanned_by,outcome) VALUES (?,?,?,?)",
                            (sid, code, actor.id, "Ekstra dicatat"))
            self.audit.log(actor, "opname", sid, "extra", None, {"barcode": code, "known": bool(known)})

    # ---------- tahap penutupan ----------
    def close_first_pass(self, actor, sid):
        s = self._open_session(sid)
        if s["status"] != "Berjalan":
            raise ServiceError("Pemeriksaan pertama sudah ditutup.")
        with Tx(self.db):
            n = self.db.execute("UPDATE stock_opname_items SET result='Belum ditemukan' "
                                "WHERE session_id=? AND result='Belum diperiksa'", (sid,)).rowcount
            self.db.execute("UPDATE stock_opname_sessions SET status='Pemeriksaan ulang' WHERE id=?", (sid,))
            self.audit.log(actor, "opname", sid, "close_first_pass", None, {"belum_ditemukan": n})
        return n

    def confirm_lost(self, actor, sid, item_ids):
        s = self._open_session(sid)
        if s["status"] != "Pemeriksaan ulang":
            raise ServiceError("Tutup pemeriksaan pertama terlebih dahulu.")
        n = 0
        with Tx(self.db):
            for iid in item_ids:
                n += self.db.execute(
                    "UPDATE stock_opname_items SET result='Hilang terkonfirmasi', verification_status='ya',"
                    "inspected_by=?, inspected_at=? WHERE id=? AND session_id=? AND result='Belum ditemukan'",
                    (actor.id, now(), iid, sid)).rowcount
            self.audit.log(actor, "opname", sid, "confirm_lost", None, {"items": list(item_ids), "count": n})
        return n

    def proposals(self, sid):
        """Usulan penyesuaian status; baru berlaku setelah persetujuan (finalize)."""
        out = []
        for r in self.db.execute(
                "SELECT i.*, c.circulation_status AS cur_status FROM stock_opname_items i "
                "JOIN book_copies c ON c.id=i.copy_id WHERE i.session_id=?", (sid,)):
            if r["result"] == "Hilang terkonfirmasi" and r["cur_status"] != "Hilang":
                out.append({"copy_id": r["copy_id"], "barcode": r["barcode_snapshot"], "title": r["book_title_snapshot"],
                            "old_status": r["cur_status"], "new_status": "Hilang",
                            "reason": "Hilang terkonfirmasi pada stok opname"})
            elif r["result"] == "Ditemukan" and r["physical_condition"] in DAMAGE_PROPOSAL \
                    and r["cur_status"] not in ("Perbaikan", "Dihapusbukukan", "Hilang"):
                out.append({"copy_id": r["copy_id"], "barcode": r["barcode_snapshot"], "title": r["book_title_snapshot"],
                            "old_status": r["cur_status"], "new_status": DAMAGE_PROPOSAL[r["physical_condition"]],
                            "reason": f"Kondisi fisik {r['physical_condition']} pada stok opname"})
        return out

    def finalize(self, actor, sid, notes=None):
        actor.require_admin()
        s = self._open_session(sid)
        if s["status"] != "Pemeriksaan ulang":
            raise ServiceError("Tutup pemeriksaan pertama dan selesaikan pemeriksaan ulang sebelum finalisasi.")
        pending = self.db.execute("SELECT COUNT(*) FROM stock_opname_items WHERE session_id=? AND result IN "
                                  "('Belum diperiksa','Belum ditemukan')", (sid,)).fetchone()[0]
        if pending:
            raise ServiceError(f"Masih ada {pending} eksemplar belum ditemukan; temukan atau konfirmasi hilang.")
        props = self.proposals(sid)
        with Tx(self.db):
            for p in props:
                borrowed = self.db.execute("SELECT 1 FROM loan_items WHERE copy_id=? AND returned_at IS NULL",
                                           (p["copy_id"],)).fetchone()
                if borrowed:
                    continue
                if p["new_status"] in ("Hilang", "Dihapusbukukan"):
                    self.db.execute(
                        "UPDATE book_copies SET circulation_status=?, archived_at=?, archived_by=?, archived_reason=?,"
                        "updated_at=?, updated_by=? WHERE id=?",
                        (p["new_status"], now(), actor.id, "Hilang" if p["new_status"] == "Hilang" else "Rusak tidak layak",
                         now(), actor.id, p["copy_id"]))
                else:
                    self.db.execute("UPDATE book_copies SET circulation_status=?, updated_at=?, updated_by=? WHERE id=?",
                                    (p["new_status"], now(), actor.id, p["copy_id"]))
                self.db.execute(
                    "INSERT INTO stock_opname_adjustments(session_id,copy_id,old_status,new_status,reason,approved_by) "
                    "VALUES (?,?,?,?,?,?)", (sid, p["copy_id"], p["old_status"], p["new_status"], p["reason"], actor.id))
            self.db.execute("UPDATE stock_opname_items SET verification_status='ya' WHERE session_id=? AND result='Dipinjam'", (sid,))
            self.db.execute("UPDATE stock_opname_sessions SET status='Final', end_date=?, finalized_by=?, finalized_at=?,"
                            "notes=COALESCE(?,notes) WHERE id=?", (today(), actor.id, now(), notes, sid))
            self.audit.log(actor, "opname", sid, "finalize", None, {"adjustments": len(props)})

    def correct_after_final(self, actor, sid, item_id, new_result, reason):
        """Prosedur koreksi tercatat setelah sesi final (hanya Administrator)."""
        actor.require_admin()
        s = self.get_session(sid)
        if not s or s["status"] != "Final":
            raise ServiceError("Koreksi hanya untuk sesi yang sudah final.")
        if not (reason or "").strip():
            raise ServiceError("Alasan koreksi wajib diisi.")
        item = self.db.execute("SELECT * FROM stock_opname_items WHERE id=? AND session_id=?", (item_id, sid)).fetchone()
        if not item:
            raise ServiceError("Item tidak ditemukan.")
        with Tx(self.db):
            self.db.execute("UPDATE stock_opname_items SET result=? WHERE id=?", (new_result, item_id))
            self.audit.log(actor, "opname_item", item_id, "correct_after_final",
                           {"result": item["result"]}, {"result": new_result, "reason": reason})

    # ---------- tampilan & laporan ----------
    def items(self, sid, result=None, search=""):
        sql = ("SELECT i.*, c.archived_at IS NOT NULL AS archived_now FROM stock_opname_items i "
               "LEFT JOIN book_copies c ON c.id=i.copy_id WHERE i.session_id=?")
        args = [sid]
        if result:
            sql += " AND i.result=?"; args.append(result)
        if search:
            sql += " AND (i.barcode_snapshot LIKE ? OR i.book_title_snapshot LIKE ?)"; args += [f"%{search}%"] * 2
        return [dict(r) for r in self.db.execute(sql + " ORDER BY i.book_title_snapshot, i.barcode_snapshot", args)]

    def recent_scans(self, sid, limit=20):
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM stock_opname_scans WHERE session_id=? ORDER BY id DESC LIMIT ?", (sid, limit))]

    def progress(self, sid):
        counts = {r["result"]: r["n"] for r in self.db.execute(
            "SELECT result, COUNT(*) n FROM stock_opname_items WHERE session_id=? GROUP BY result", (sid,))}
        snapshot = self.db.execute("SELECT COUNT(*) FROM stock_opname_items WHERE session_id=? "
                                   "AND result<>'Ditemukan ekstra'", (sid,)).fetchone()[0]
        extras = counts.get("Ditemukan ekstra", 0)
        borrowed = counts.get("Dipinjam", 0)
        found = counts.get("Ditemukan", 0)
        shelf_scope = snapshot - borrowed
        checked = found  # eksemplar ditemukan lalu dipinjam tetap berstatus Ditemukan
        percent = round(found / shelf_scope * 100, 1) if shelf_scope > 0 else 0.0
        damaged = self.db.execute(
            "SELECT COUNT(*) FROM stock_opname_items WHERE session_id=? AND result='Ditemukan' "
            "AND physical_condition<>'Baik'", (sid,)).fetchone()[0]
        return {"snapshot": snapshot, "borrowed": borrowed, "shelf_scope": shelf_scope, "found": found,
                "unchecked": counts.get("Belum diperiksa", 0), "not_found": counts.get("Belum ditemukan", 0),
                "lost": counts.get("Hilang terkonfirmasi", 0), "extras": extras, "damaged": damaged,
                "percent": percent, "checked": checked}

    def report(self, sid):
        s = self.get_session(sid)
        if not s:
            raise ServiceError("Sesi tidak ditemukan.")
        p = self.progress(sid)
        by_cond = {r["physical_condition"]: r["n"] for r in self.db.execute(
            "SELECT physical_condition, COUNT(*) n FROM stock_opname_items WHERE session_id=? AND result='Ditemukan' "
            "AND physical_condition<>'Baik' GROUP BY physical_condition", (sid,))}
        adj = [dict(r) for r in self.db.execute(
            "SELECT a.*, c.barcode FROM stock_opname_adjustments a LEFT JOIN book_copies c ON c.id=a.copy_id "
            "WHERE a.session_id=?", (sid,))]
        return {"session": s, "progress": p, "damage_by_condition": by_cond, "adjustments": adj}
