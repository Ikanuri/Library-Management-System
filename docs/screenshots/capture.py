"""Ambil tangkapan layar semua halaman Libris di xvfb.

    xvfb-run -a -s "-screen 0 1400x900x24" python docs/screenshots/capture.py [dark|light]

Butuh ImageMagick (`import`). Data contoh dibuat di database sementara.
"""
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ["LIBRIS_PBKDF2_ITERATIONS"] = "1000"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.context import Services          # noqa: E402
from app.ui.app import LibrisApp          # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "dark"
out = Path(__file__).resolve().parent / mode
out.mkdir(exist_ok=True)
tmp = tempfile.mkdtemp()
s = Services(tmp + "/x.db", tmp + "/bk")
s.auth.create_user(None, "admin", "secret1", "Administrator", "admin")
a = s.auth.login("admin", "secret1")
s.settings.set("theme", mode, a)
data = [("Laskar Pelangi", "Andrea Hirata", "Novel", "A-01", 3), ("Bumi Manusia", "Pramoedya A. Toer", "Novel", "A-02", 2),
        ("Filosofi Teras", "Henry Manampiring", "Nonfiksi", "B-01", 2), ("Atomic Habits", "James Clear", "Nonfiksi", "B-02", 2),
        ("Negeri 5 Menara", "A. Fuadi", "Novel", "A-03", 1)]
n = 0
for t, au, cat, shelf, k in data:
    b = s.books.add_book(a, {"title": t, "author": au, "category": cat, "shelf": shelf})
    for _ in range(k):
        n += 1
        s.books.add_copy(a, b, barcode=f"1000{n:04d}")
m1 = s.members.add(a, {"member_no": "M001", "name": "Budi Santoso", "phone": "0812"})
m2 = s.members.add(a, {"member_no": "M002", "name": "Sari Wulandari"})
s.members.add(a, {"member_no": "M003", "name": "Dewi Lestari"})
for i, d in enumerate((40, 10, 9)):
    s.loans.checkout(a, m1 if i != 2 else m2, [f"1000{i+1:04d}"], loan_date=(date.today() - timedelta(days=d)).isoformat())
s.returns.return_item(a, "10000001", returned_at=(date.today() - timedelta(days=2)).isoformat())
s.loans.checkout(a, m2, ["10000005"], loan_date=(date.today() - timedelta(days=30)).isoformat())
sid = s.opname.create_session(a, date.today().year)
for c in ("10000004", "10000006", "10000007", "10000008"):
    s.opname.scan(a, sid, c)
s.opname.scan(a, sid, "10000004")
s.backups.backup(a)

app = LibrisApp(s)
app.geometry("1280x780+0+0")
app.update()


def snap(name):
    app.update(); app.update_idletasks()
    subprocess.run(["import", "-window", "root", "-crop", "1280x780+0+0", str(out / f"{name}.png")], check=True)


snap("00-login") if False else None
app.actor = a
app.build_main()
pages = ["dashboard", "books", "members", "loans", "returns", "fines", "opname", "import", "reports", "backup", "users", "settings"]
steps = [(f"{i + 1:02d}-{k}", k, {}) for i, k in enumerate(pages)] + [("13-detail", "detail", {"book_id": 1})]


def run(i=0):
    if i == len(steps):
        app.show_login(); app.after(300, lambda: (snap("00-login"), app.destroy())); return
    name, key, kw = steps[i]
    app.show(key, **kw)
    if key == "loans":      # contoh alur scan: pilih anggota dan pindai satu eksemplar
        app.pages["loans"].pick_member("M003"); app.pages["loans"].add_code("10000009") if False else None
        app.pages["loans"].add_code("10000008")
    if key == "returns":
        app.pages["returns"].scan_code("10000002")
    if key == "opname":
        app.pages["opname"].do_scan("10000009")
    if key == "reports":
        app.pages["reports"].preview()
    app.after(350, lambda: (snap(name), run(i + 1)))


app.after(300, run)
app.mainloop()
print("selesai:", out)
