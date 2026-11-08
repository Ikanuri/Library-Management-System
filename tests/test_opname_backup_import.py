import pytest
from app.services.base import ServiceError


def start(lib, year=2027):
    return lib.opname.create_session(lib.admin, year)


def test_one_active_session_per_year(lib):
    start(lib)
    with pytest.raises(ServiceError, match="aktif"):
        start(lib)


def test_snapshot_unchanged_when_master_changes(lib):
    sid = start(lib)
    lib.books.update_book(lib.admin, lib.ids["b1"], {"title": "Judul Baru"})
    lib.books.add_copy(lib.admin, lib.ids["b1"], barcode="30000001")
    titles = {i["book_title_snapshot"] for i in lib.opname.items(sid)}
    assert "Laskar Pelangi" in titles and "Judul Baru" not in titles
    assert lib.opname.progress(sid)["snapshot"] == 3


def test_scan_flow_duplicate_unknown_extra(lib):
    sid = start(lib)
    assert lib.opname.scan(lib.staff, sid, "10000001")["status"] == "ok"
    assert lib.opname.scan(lib.staff, sid, "10000001")["status"] == "duplikat"
    assert lib.opname.progress(sid)["found"] == 1                 # duplikat tidak menambah temuan
    assert lib.opname.scan(lib.staff, sid, "55555555")["status"] == "tidak_dikenal"
    lib.opname.record_extra(lib.staff, sid, "55555555")
    assert lib.opname.progress(sid)["extras"] == 1
    assert lib.db.execute("SELECT COUNT(*) FROM stock_opname_scans WHERE outcome='Duplikat'").fetchone()[0] == 1


def test_borrowed_not_lost_and_dynamic_scope(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    sid = start(lib)
    assert lib.opname.progress(sid)["borrowed"] == 1 and lib.opname.progress(sid)["shelf_scope"] == 2
    lib.opname.close_first_pass(lib.admin, sid)
    assert [i for i in lib.opname.items(sid) if i["barcode_snapshot"] == "10000001"][0]["result"] == "Dipinjam"


def test_returned_during_session_must_be_scanned(lib):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    sid = start(lib)
    lib.returns.return_item(lib.admin, "10000001")
    it = [i for i in lib.opname.items(sid) if i["barcode_snapshot"] == "10000001"][0]
    assert it["result"] == "Belum diperiksa" and lib.opname.progress(sid)["shelf_scope"] == 3


def test_scanned_then_borrowed_stays_found(lib):
    sid = start(lib)
    lib.opname.scan(lib.staff, sid, "10000002")
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000002"])
    it = [i for i in lib.opname.items(sid) if i["barcode_snapshot"] == "10000002"][0]
    assert it["result"] == "Ditemukan"


def test_full_reconciliation_and_lock(lib):
    sid = start(lib)
    lib.opname.scan(lib.staff, sid, "10000001")
    lib.opname.scan(lib.staff, sid, "10000002", condition="Rusak berat")
    with pytest.raises(ServiceError):
        lib.opname.finalize(lib.admin, sid)                       # pemeriksaan pertama belum ditutup
    assert lib.opname.close_first_pass(lib.admin, sid) == 1
    with pytest.raises(ServiceError, match="belum ditemukan"):
        lib.opname.finalize(lib.admin, sid)
    nf = [i["id"] for i in lib.opname.items(sid, "Belum ditemukan")]
    lib.opname.confirm_lost(lib.admin, sid, nf)
    props = lib.opname.proposals(sid)
    assert {p["new_status"] for p in props} == {"Hilang", "Perbaikan"}
    with pytest.raises(ServiceError):
        lib.opname.finalize(lib.staff, sid)                       # hanya admin
    lib.opname.finalize(lib.admin, sid)
    assert lib.books.get_copy(lib.ids["c3"])["circulation_status"] == "Hilang"
    assert lib.books.get_copy(lib.ids["c2"])["circulation_status"] == "Perbaikan"
    adj = lib.opname.report(sid)["adjustments"]
    assert len(adj) == 2 and all(a["reason"] for a in adj)
    with pytest.raises(ServiceError, match="final"):
        lib.opname.scan(lib.staff, sid, "10000001")
    lib.opname.correct_after_final(lib.admin, sid, nf[0], "Ditemukan", "ditemukan di rak lain")
    with pytest.raises(ServiceError):
        lib.opname.correct_after_final(lib.admin, sid, nf[0], "Ditemukan", "")


def test_progress_formula(lib):
    sid = start(lib)
    lib.opname.scan(lib.staff, sid, "10000001")
    assert lib.opname.progress(sid)["percent"] == round(1 / 3 * 100, 1)


def test_backup_validate_and_restore(lib, tmp_path):
    p = lib.backups.backup(lib.admin)
    assert lib.backups.validate(p)
    lib.books.delete_book(lib.admin, lib.ids["b2"])
    bad = tmp_path / "rusak.db"; bad.write_bytes(b"bukan sqlite")
    assert not lib.backups.validate(bad)
    with pytest.raises(ServiceError):
        lib.restore(lib.admin, bad)
    assert lib.books.get_book(lib.ids["b1"])                       # DB aktif tidak berubah
    lib.restore(lib.admin, p)
    assert lib.books.get_book(lib.ids["b2"]) is not None           # data dikembalikan
    assert list(lib.backups.backup_dir().glob("*pra-restore.db"))   # salinan pengaman dibuat


def test_backup_retention(lib):
    lib.settings.set("backup_retention", 2)
    for _ in range(4):
        lib.backups.backup(lib.admin)
    assert len(list(lib.backups.backup_dir().glob("libris_*.db"))) == 2


def test_backup_warns_when_missing(lib):
    assert any("Belum pernah" in w for w in lib.backups.warnings())


def test_import_dry_run_and_atomic(lib, tmp_path):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active
    ws.append(["ISBN", "Judul*", "Penulis", "Penerbit", "Tahun", "Kategori", "Rak", "Barcode", "Inv", "Kondisi"])
    ws.append([None, "Buku Impor 1", "A", None, 2020, "Baru", "B-1", "40000001", None, "Baik"])
    ws.append([None, "Buku Impor 2", "B", None, 2021, "Baru", "B-1", "40000001", None, "Baik"])   # ganda
    f = tmp_path / "i.xlsx"; wb.save(f)
    rows = lib.imports.read_rows(f)
    rep = lib.imports.dry_run(rows)
    assert rep["errors"] == 1 and "Baru" in rep["new_categories"]
    before = lib.db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    with pytest.raises(ServiceError):
        lib.imports.commit(lib.admin, rows)
    assert lib.db.execute("SELECT COUNT(*) FROM books").fetchone()[0] == before    # tidak ada data parsial
    ws["H3"] = None; wb.save(f)
    res = lib.imports.commit(lib.admin, lib.imports.read_rows(f))
    assert res == {"books": 2, "copies": 2}
    assert all(len(c["barcode"]) == 8 for c in lib.db.execute("SELECT barcode FROM book_copies"))


def test_reports_and_labels(lib, tmp_path):
    lib.loans.checkout(lib.admin, lib.ids["m1"], ["10000001"])
    for name in sum(lib.reports.CATEGORIES.values(), []):
        lib.reports.generate(name)
    assert lib.reports.export_xlsx(tmp_path / "r.xlsx", "Daftar eksemplar", lib.admin) == 3
    lib.reports.export_pdf(tmp_path / "r.pdf", "Daftar eksemplar", lib.admin)
    assert (tmp_path / "r.pdf").read_bytes()[:4] == b"%PDF"
    lib.labels.make_pdf(tmp_path / "l.pdf", lib.labels.copies_for())
    assert (tmp_path / "l.pdf").stat().st_size > 1000
    d = lib.reports.dashboard()
    assert d["copies"] == 3 and d["borrowed"] == 1 and d["available"] == 2
