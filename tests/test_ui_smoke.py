"""Uji asap UI: butuh display (jalankan dengan xvfb-run). Dilewati bila tidak ada display."""
import os
import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture
def ui(svc):
    try:
        from app.ui.app import LibrisApp
        app = LibrisApp(svc)
    except Exception as e:
        pytest.skip(f"Tidak ada display: {e}")
    yield app
    app.destroy()
    from app.ui import theme
    theme.apply("dark")      # tema bersifat global; kembalikan agar tes lain deterministik


def test_all_pages_render(ui, lib):
    ui.actor = lib.admin
    ui.build_main()
    for key in ui.pages:
        if key == "detail":
            ui.show("detail", book_id=lib.ids["b1"])
        else:
            ui.show(key)
        ui.update()
    assert len(ui.pages) == 13


def test_staff_sees_no_admin_pages(ui, lib):
    ui.actor = lib.staff
    ui.build_main()
    assert "users" not in ui.pages and "settings" not in ui.pages


def test_confirm_enter_and_escape(ui):
    from app.ui import components as c
    ui.update()
    ui.after(250, lambda: c.Dialog.current.invoke())            # Enter = tombol utama (Ya)
    assert c.confirm("Lanjutkan?") is True
    ui.after(250, lambda: c.Dialog.current.event_generate("<Escape>"))   # Esc = batal
    assert c.confirm("Lanjutkan?") is False
    ui.after(250, lambda: c.Dialog.current.invoke())
    assert c.info("Halo") is None


def test_ask_int_validates_inline(ui):
    from app.ui import components as c
    ui.update()
    def type_bad_then_good():
        dlg = [w for w in ui.winfo_children() if isinstance(w, c.FormDialog)][0]
        dlg.vars["n"].set("abc"); dlg._save()
        assert "bilangan bulat" in dlg.err.cget("text")
        dlg.vars["n"].set("2027"); dlg._save()
    ui.after(250, type_bad_then_good)
    assert c.ask_int("Tahun", "Tahun", 2026, 1900) == 2027


def test_toast_and_feedback_strip(ui):
    from app.ui import components as c
    t = c.toast(ui, "Tersimpan", duration=3000)
    ui.update(); assert t.winfo_exists()
    t.destroy()
    s = c.FeedbackStrip(ui); s.ok("Judul", "detail"); assert s.kind == "green"
    s.fail("Gagal"); assert s.kind == "red"


def test_no_literal_colors_or_messagebox_outside_theme():
    import re, pathlib
    for f in pathlib.Path("app/ui").glob("*.py"):
        src = f.read_text(encoding="utf-8")   # Windows memakai cp1252 secara bawaan
        if f.name != "theme.py":
            assert not re.search(r"#[0-9a-fA-F]{6}", src), f"warna literal di {f.name}"
        if f.name != "components.py":
            assert "messagebox" not in src and "simpledialog" not in src, f.name


def test_datatable_status_prefix_empty_state_and_sort(ui):
    from app.ui.components import DataTable
    t = DataTable(ui, [("name", "Nama", 100), ("n", "Jumlah", 60), ("st", "Status", 80)], status_key="st")
    t.pack(); ui.update()
    t.load([]); ui.update()
    assert t.empty.winfo_ismapped()                       # keadaan kosong tampil
    t.load([{"id": 1, "name": "b", "n": 10, "st": "Hilang"}, {"id": 2, "name": "a", "n": 2, "st": "Tersedia"}])
    ui.update()
    assert not t.empty.winfo_ismapped()
    assert t.tree.item("1", "values")[2] == "● Hilang"      # status = penanda berwarna
    assert "Hilang" in t.tree.item("1", "tags") and "Tersedia" not in t.tree.item("2", "tags")
    t.sort_by("n"); assert t._order == ["2", "1"]            # urut numerik, bukan teks
    t.sort_by("n"); assert t._order == ["1", "2"]            # klik lagi = terbalik


def test_loans_scan_flow_inline_feedback(ui, lib):
    ui.actor = lib.admin; ui.build_main(); ui.show("loans"); ui.update()
    p = ui.pages["loans"]
    p.pick_member("M001")
    assert "Budi" in p.member_lbl.cget("text")
    p.add_code("10000001")
    assert p.strip.kind == "green" and len(p.pending_rows) == 1
    p.scan.on_scan("99999999")                                # kode tak dikenal -> strip merah, tanpa dialog
    assert p.strip.kind == "red"
    p.add_code("10000002"); p.pending.tree.selection_set("10000001"); p.remove_item()
    assert [r["barcode"] for r in p.pending_rows] == ["10000002"]
    p.confirm_loan()
    assert lib.loans.active_count(lib.ids["m1"]) == 1 and p.pending_rows == []


def test_returns_error_is_inline(ui, lib):
    ui.actor = lib.admin; ui.build_main(); ui.show("returns"); ui.update()
    p = ui.pages["returns"]
    p.scan.on_scan("10000001")                                # tidak sedang dipinjam
    assert p.strip.kind == "red"


def test_theme_switch_persists_and_rebuilds(ui, lib):
    from app.ui import theme
    ui.actor = lib.admin; ui.build_main(); ui.show("settings"); ui.update()
    page = ui.pages["settings"]
    page.theme_var.set("Terang"); page.save(); ui.update()
    assert lib.settings.get("theme") == "light" and theme.MODE == "light" and theme.BG == theme.LIGHT["BG"]
    assert ui.current_key == "settings" and "dashboard" in ui.pages
    ui.pages["settings"].theme_var.set("Gelap"); ui.pages["settings"].save(); ui.update()
    assert theme.MODE == "dark" and theme.BG == theme.DARK["BG"]


def test_sidebar_groups_hidden_for_staff(ui, lib):
    ui.actor = lib.staff; ui.build_main(); ui.update()
    assert "users" not in ui.nav_buttons and "settings" not in ui.nav_buttons
    assert {"dashboard", "loans", "opname", "backup"} <= set(ui.nav_buttons)


def test_theme_tokens_complete_and_badges():
    from app.ui import theme
    need = {"BG", "PANEL", "PANEL2", "PANEL3", "LINE", "TEXT", "SOFT", "MUTED", "ACCENT", "BLUE", "PURPLE", "OK", "WARN", "DANGER"}
    assert need <= set(theme.DARK) and need <= set(theme.LIGHT)
    assert theme.DARK["BG"] == "#0b1020" and theme.DARK["ACCENT"] == "#54d6e8"
    assert theme.BADGES_DARK["green"] == ("#78e0b3", "#153a31", "#245b49")
    assert theme.status_kind("Hilang") == "red" and theme.status_kind("Tersedia") == "green" and theme.status_kind("?") == "gray"
    assert len(theme.badge_style("blue")) == 3
