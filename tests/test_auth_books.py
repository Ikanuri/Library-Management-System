import pytest
from app.services.base import ServiceError
from app.utils.security import hash_password, verify_password


def test_login_ok_and_wrong_password(svc):
    assert svc.auth.login("admin", "secret1").role == "admin"
    with pytest.raises(ServiceError):
        svc.auth.login("admin", "salah")


def test_password_is_hashed(svc):
    h = svc.db.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()[0]
    assert h.startswith("pbkdf2_sha256$") and "secret1" not in h
    assert verify_password("x", hash_password("x")) and not verify_password("y", hash_password("x"))


def test_lockout_and_inactive(svc):
    for _ in range(5):
        with pytest.raises(ServiceError):
            svc.auth.login("petugas", "salah")
    with pytest.raises(ServiceError, match="percobaan"):
        svc.auth.login("petugas", "secret1")
    svc.db.execute("UPDATE users SET locked_until=NULL WHERE username='petugas'")
    svc.auth.set_active(svc.admin, svc.staff_id, False)
    with pytest.raises(ServiceError, match="nonaktif"):
        svc.auth.login("petugas", "secret1")


def test_staff_cannot_create_user(svc):
    with pytest.raises(ServiceError):
        svc.auth.create_user(svc.staff, "x", "secret1", "X")


def test_duplicate_barcode_rejected(lib):
    with pytest.raises(ServiceError, match="sudah dipakai"):
        lib.books.add_copy(lib.admin, lib.ids["b1"], barcode="10000001")


def test_barcode_must_be_8_digits(lib):
    for bad in ("1234", "ABCDEFGH", "123456789"):
        with pytest.raises(ServiceError):
            lib.books.add_copy(lib.admin, lib.ids["b1"], barcode=bad)


def test_auto_barcode_and_inventory_code(lib):
    cid = lib.books.add_copy(lib.admin, lib.ids["b2"])
    c = lib.books.get_copy(cid)
    assert len(c["barcode"]) == 8 and c["barcode"].isdigit() and c["inventory_code"].startswith("INV-")


def test_isbn_unique_and_valid(lib):
    with pytest.raises(ServiceError, match="ISBN sudah"):
        lib.books.add_book(lib.admin, {"title": "Lain", "isbn": "978-979-3062-79-2"})
    with pytest.raises(ServiceError, match="tidak valid"):
        lib.books.add_book(lib.admin, {"title": "Lain", "isbn": "123"})


def test_edit_book_logged_old_new(lib):
    lib.books.update_book(lib.admin, lib.ids["b1"], {"title": "Laskar Pelangi (Ed. 2)"})
    log = lib.audit.list(entity="book", action="update")[0]
    assert "Laskar Pelangi (Ed. 2)" in log["new_value"] and '"Laskar Pelangi"' in log["old_value"]


def test_edit_copy_barcode_warns_and_validates(lib):
    w = lib.books.update_copy(lib.admin, lib.ids["c1"], {"barcode": "20000001"})
    assert any("cetak ulang" in x for x in w)
    with pytest.raises(ServiceError):
        lib.books.update_copy(lib.admin, lib.ids["c1"], {"barcode": "10000002"})


def test_delete_without_history_admin_only(lib):
    with pytest.raises(ServiceError):
        lib.books.delete_book(lib.staff, lib.ids["b2"])
    lib.books.delete_book(lib.admin, lib.ids["b2"])
    assert lib.books.get_book(lib.ids["b2"]) is None


def test_delete_with_history_refused_archive_ok_restore(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000003"])
    lib.returns.return_item(lib.admin, "10000003")
    with pytest.raises(ServiceError, match="riwayat"):
        lib.books.delete_book(lib.admin, lib.ids["b2"])
    lib.books.archive_book(lib.staff, lib.ids["b2"])
    assert lib.books.list_books(view="Aktif") and all(b["id"] != lib.ids["b2"] for b in lib.books.list_books(view="Aktif"))
    with pytest.raises(ServiceError):
        lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000003"])
    lib.books.restore_book(lib.staff, lib.ids["b2"])
    assert lib.books.get_copy(lib.ids["c3"])["circulation_status"] == "Tersedia"


def test_borrowed_cannot_be_archived_or_deleted(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    for fn in (lambda: lib.books.archive_copy(lib.admin, lib.ids["c1"]),
               lambda: lib.books.delete_copy(lib.admin, lib.ids["c1"]),
               lambda: lib.books.archive_book(lib.admin, lib.ids["b1"]),
               lambda: lib.books.delete_book(lib.admin, lib.ids["b1"])):
        with pytest.raises(ServiceError, match="dipinjam"):
            fn()


def test_bulk_remove_skips_borrowed(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    r = lib.books.bulk_remove_copies(lib.admin, [lib.ids["c1"], lib.ids["c2"]])
    assert r["ok"] == 1 and len(r["skipped"]) == 1 and "dipinjam" in r["skipped"][0][1]


def test_bulk_update_shelf(lib):
    r = lib.books.bulk_update_copies(lib.admin, [lib.ids["c1"], lib.ids["c2"]], {"shelf": "Z-9"})
    assert r["ok"] == 2 and lib.books.get_copy(lib.ids["c2"])["shelf"] == "Z-9"


def test_search_by_barcode_and_title(lib):
    assert lib.books.list_books(search="10000003")[0]["title"] == "Bumi Manusia"
    assert lib.books.list_books(search="laskar")[0]["copies_total"] == 2


def test_member_unique_and_inactive(lib):
    with pytest.raises(ServiceError):
        lib.members.add(lib.admin, {"member_no": "M001", "name": "Dobel"})
    lib.members.set_active(lib.admin, lib.ids["m1"], False)
    with pytest.raises(ServiceError, match="nonaktif"):
        lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
