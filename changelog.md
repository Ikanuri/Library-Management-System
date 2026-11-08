# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/).

## [Belum dirilis]

### Ditambahkan
- Workflow GitHub Actions `build-windows.yml`: tes + build `.exe` di runner Windows, hasil sebagai artifact.
- Aplikasi Libris 0.1.0: database SQLite + migrasi, service untuk FR-01..FR-11, UI CustomTkinter, 42 tes, README, `build_windows.bat`.
- Proposal teknis v1.2 (`docs/Proposal_Library_Management_System_Offline_v1.2.md`).
- Prototipe UI/UX Libris v1.2 (`docs/Libris_UI_UX_Prototype_v1.2.html`).
- `handoff.md`, `patchnotes.md`, `changelog.md`.

## Riwayat dokumen proposal

### [1.2]
- Edit, arsip, pemulihan, hapus permanen, dan operasi massal untuk judul dan eksemplar (§3.3.2).
- Kolom skema baru: `is_active`, `archived_*`, `updated_*`; `audit_logs` menyimpan `entity`, `action`, `old_value`, `new_value`.
- FK ke `books`/`book_copies` memakai `ON DELETE RESTRICT`.

### [1.1]
- Aplikasi dinamai "Libris"; login, peran Administrator/Petugas, halaman Petugas dan Log.
- Enumerasi status sirkulasi dan kondisi fisik (§3.3.1); barcode numerik 8 digit.
- Siklus denda dan tabel `fines`, `fine_payments`; kebijakan buku hilang/rusak berat.
- Stok opname: hasil dipisahkan dari kondisi, cakupan rak dinamis, temuan ekstra, `stock_opname_scans`.
- Impor Excel dan cetak label masuk versi awal (FR-11).
- Backup: pemicu buka/tutup aplikasi, peringatan drive sama dan backup usang.
- Matplotlib dihapus; hashing PBKDF2; data di `%LOCALAPPDATA%`.
- Jadwal 9 → 10 fase, 8–10 minggu.

### [1.0]
- Proposal awal.
