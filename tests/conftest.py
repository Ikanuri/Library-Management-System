import os
import sys
from pathlib import Path

os.environ["LIBRIS_PBKDF2_ITERATIONS"] = "1000"   # percepat tes; produksi 600.000
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.context import Services


@pytest.fixture
def svc(tmp_path):
    s = Services(tmp_path / "t.db", backup_dir=tmp_path / "bk")
    s.admin_id = s.auth.create_user(None, "admin", "secret1", "Admin", "admin")
    s.staff_id = s.auth.create_user(None, "petugas", "secret1", "Petugas", "staff")
    s.admin = s.auth.login("admin", "secret1")
    s.staff = s.auth.login("petugas", "secret1")
    yield s
    s.close()


@pytest.fixture
def lib(svc):
    """Perpustakaan contoh: 2 judul, 3 eksemplar, 2 anggota."""
    b1 = svc.books.add_book(svc.admin, {"title": "Laskar Pelangi", "author": "Andrea Hirata", "isbn": "9789793062792",
                                         "category": "Novel", "shelf": "A-01"})
    b2 = svc.books.add_book(svc.admin, {"title": "Bumi Manusia", "author": "Pramoedya", "category": "Novel", "shelf": "A-02"})
    c1 = svc.books.add_copy(svc.admin, b1, barcode="10000001")
    c2 = svc.books.add_copy(svc.admin, b1, barcode="10000002")
    c3 = svc.books.add_copy(svc.admin, b2, barcode="10000003")
    m1 = svc.members.add(svc.admin, {"member_no": "M001", "name": "Budi"})
    m2 = svc.members.add(svc.admin, {"member_no": "M002", "name": "Sari"})
    svc.ids = dict(b1=b1, b2=b2, c1=c1, c2=c2, c3=c3, m1=m1, m2=m2)
    return svc
