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
