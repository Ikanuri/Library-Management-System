from .base import js


class AuditService:
    def __init__(self, db):
        self.db = db

    def log(self, actor, entity, entity_id, action, old=None, new=None):
        uid = actor.id if actor else None
        self.db.execute(
            "INSERT INTO audit_logs(user_id,entity,entity_id,action,old_value,new_value) VALUES (?,?,?,?,?,?)",
            (uid, entity, None if entity_id is None else str(entity_id), action,
             js(old) if old is not None else None, js(new) if new is not None else None))

    def list(self, limit=500, entity=None, action=None):
        sql = ("SELECT a.*, u.username FROM audit_logs a LEFT JOIN users u ON u.id=a.user_id WHERE 1=1")
        args = []
        if entity:
            sql += " AND a.entity=?"; args.append(entity)
        if action:
            sql += " AND a.action=?"; args.append(action)
        sql += " ORDER BY a.id DESC LIMIT ?"; args.append(limit)
        return [dict(r) for r in self.db.execute(sql, args)]
