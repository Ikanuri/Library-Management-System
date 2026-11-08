from datetime import date, timedelta
import pytest
from app.services.base import ServiceError
from app.services.fine_service import compute_fine


def iso(d):
    return d.isoformat()


def test_compute_fine_examples():
    assert compute_fine("2026-01-08", "2026-01-11", 1000) == (3, 3000)   # contoh proposal
    assert compute_fine("2026-01-08", "2026-01-08", 1000) == (0, 0)
    assert compute_fine("2026-01-08", "2026-01-05", 1000) == (0, 0)
    assert compute_fine("2026-01-08", "2026-01-11", 1000, grace=2) == (3, 1000)
    assert compute_fine("2026-01-08", "2026-02-08", 1000, cap=5000) == (31, 5000)


def test_checkout_and_double_borrow(lib):
    lid = lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001", "10000003"])
    loan = lib.loans.get(lid)
    assert len(loan["items"]) == 2
    assert lib.books.get_copy(lib.ids["c1"])["circulation_status"] == "Dipinjam"
    with pytest.raises(ServiceError, match="Dipinjam"):
        lib.loans.checkout(lib.admin, lib.ids["m2"], ["10000001"])


def test_checkout_atomic_rollback(lib):
    with pytest.raises(ServiceError):
        lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001", "99999999"])
    assert lib.books.get_copy(lib.ids["c1"])["circulation_status"] == "Tersedia"
    assert lib.db.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 0


def test_loan_limit(lib):
    lib.settings.set("max_loans_per_member", 1)
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    with pytest.raises(ServiceError, match="batas"):
        lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000002"])


def test_on_time_return_zero_fine(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    r = lib.returns.return_item(lib.admin, "10000001")
    assert r["fine"] is None and lib.books.get_copy(lib.ids["c1"])["circulation_status"] == "Tersedia"


def test_late_return_3000_and_rate_change_not_retroactive(lib):
    start = date.today() - timedelta(days=10)       # jatuh tempo = +7 -> 3 hari terlambat
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"], loan_date=iso(start))
    r = lib.returns.return_item(lib.admin, "10000001")
    assert r["fine"]["amount"] == 3000 and r["fine"]["days_late"] == 3
    lib.settings.set("fine_rate", 5000)
    assert lib.db.execute("SELECT amount FROM fines").fetchone()[0] == 3000


def test_double_return_rejected(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    lib.returns.return_item(lib.admin, "10000001")
    with pytest.raises(ServiceError):
        lib.returns.return_item(lib.admin, "10000001")


def test_partial_return(lib):
    lid = lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001", "10000002"])
    lib.returns.return_item(lib.admin, "10000001")
    assert [i["returned_at"] is None for i in lib.loans.get(lid)["items"]].count(True) == 1


def test_projected_fine_not_payable_and_payment_cycle(lib):
    start = date.today() - timedelta(days=9)        # 2 hari terlambat, belum kembali
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"], loan_date=iso(start))
    od = lib.loans.overdue()
    assert od[0]["days_late"] == 2 and od[0]["projected_fine"] == 2000
    assert lib.fines.list() == []                   # belum ada denda yang ditetapkan -> tidak bisa dibayar
    lib.returns.return_item(lib.admin, "10000001")
    fid = lib.fines.list()[0]["id"]
    assert lib.fines.pay(lib.staff, fid, 500) == "Sebagian"
    with pytest.raises(ServiceError, match="melebihi"):
        lib.fines.pay(lib.staff, fid, 5000)
    assert lib.fines.pay(lib.staff, fid, 1500) == "Lunas"
    assert lib.fines.summary()["outstanding"] == 0


def test_heavy_damage_requires_confirmation(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    with pytest.raises(ServiceError, match="mengonfirmasi"):
        lib.returns.return_item(lib.admin, "10000001", condition="Rusak berat")
    r = lib.returns.return_item(lib.admin, "10000001", condition="Rusak berat",
                                confirmed_status="Perbaikan", replacement_fee=50000)
    assert r["new_status"] == "Perbaikan" and r["fine"]["amount"] == 50000
    with pytest.raises(ServiceError):
        lib.loans.checkout(lib.admin, lib.ids["m2"], ["10000001"])   # status Perbaikan tak bisa dipinjam
