# Libris — Library Management System (Offline)

Aplikasi perpustakaan desktop offline untuk Windows 10/11: Python 3.12, CustomTkinter, SQLite.
Spesifikasi lengkap: [`docs/Proposal_Library_Management_System_Offline_v1.2.md`](docs/Proposal_Library_Management_System_Offline_v1.2.md);
acuan UI: [`docs/Libris_UI_UX_Prototype_v1.2.html`](docs/Libris_UI_UX_Prototype_v1.2.html).

## Menjalankan
```bash
python -m venv .venv && .venv\Scripts\activate     # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Saat pertama dibuka, aplikasi meminta pembuatan akun Administrator. Data tersimpan di
`%LOCALAPPDATA%\Libris\` (Linux: `~/.local/share/Libris/`); ubah dengan variabel `LIBRIS_DATA_DIR`.

## Pengujian
```bash
pytest -q                      # 52 tes; uji UI dilewati bila tidak ada display
xvfb-run -a pytest -q          # Linux tanpa layar
```

## Paket .exe (di Windows)
Jalankan `build_windows.bat` (PyInstaller). Hasil: `dist\Libris\Libris.exe`.
Atau unduh dari GitHub: tab **Actions → Build Windows exe → artifact `Libris-windows`** (dibangun otomatis tiap push ke `main`, atau jalankan manual via *Run workflow*).

## Antarmuka
Tema gelap bawaan (aksen cyan, mengikuti prototipe v1.2) dengan tema terang opsional di **Pengaturan → Tampilan**.
Token warna, huruf, dan jarak ada di `app/ui/theme.py`; komponen bersama di `app/ui/components.py`
(dialog bergaya, toast, `Card`, `DataTable`, `FeedbackStrip`, `ScanEntry`). Tangkapan layar: `docs/screenshots/`
(dibuat ulang dengan `xvfb-run -a python docs/screenshots/capture.py dark|light`). Belum diuji manual di Windows:
lihat `docs/UI_Checklist_Windows.md`.

## Struktur
`app/database` skema + migrasi · `app/services` aturan bisnis · `app/ui` CustomTkinter · `tests/` pytest.
