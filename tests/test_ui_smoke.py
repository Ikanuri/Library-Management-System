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
    t = c.toast(ui, "Tersimpan", duration=50)
    ui.update(); assert t.winfo_exists()
    s = c.FeedbackStrip(ui); s.ok("Judul", "detail"); assert s.kind == "green"
    s.fail("Gagal"); assert s.kind == "red"


def test_no_literal_colors_or_messagebox_outside_theme():
    import re, pathlib
    for f in pathlib.Path("app/ui").glob("*.py"):
        src = f.read_text()
        if f.name != "theme.py":
            assert not re.search(r"#[0-9a-fA-F]{6}", src), f"warna literal di {f.name}"
        if f.name != "components.py":
            assert "messagebox" not in src and "simpledialog" not in src, f.name
