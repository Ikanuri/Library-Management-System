# Handoff — Libris (Library Management System Offline)

Tanggal: 2026-11-08 · Status proyek: **implementasi Fase 1–9 selesai di sisi kode (v0.1.0); Fase 10 (uji Windows, .exe, panduan) belum**

## Ringkasan
Libris adalah aplikasi perpustakaan desktop offline untuk Windows 10/11 (satu workstation).
Stack: Python 3.12, CustomTkinter, SQLite (`sqlite3`), OpenPyXL, ReportLab, python-barcode, PyInstaller, pytest.

## Status implementasi (v0.1.0)
Sudah ada dan diuji (52 tes pytest, termasuk uji UI via xvfb): skema 15 tabel + migrasi, login/peran/penguncian,
buku & eksemplar (edit/arsip/pulih/hapus/massal), anggota, peminjaman atomik, pengembalian sebagian, denda (siklus
berjalan→ditetapkan→dibayar), laporan Excel/PDF, backup/restore (Backup API, validasi, retensi), stok opname lengkap
(snapshot, cakupan rak dinamis, ekstra, rekonsiliasi, finalisasi, koreksi), impor Excel (dry-run, atomik), label PDF Code 128,
dashboard, UI CustomTkinter 12 halaman.

**UI (pemolesan, brief `docs/UI_Polish_Brief_Libris_CustomTkinter.md`) — selesai Fase 1–6:** token tema `app/ui/theme.py` (DARK bawaan, LIGHT),
dialog/toast/komponen di `app/ui/components.py`, sidebar berkelompok, halaman memakai `Page` (header + `self.body`), tema gelap/terang dari Pengaturan
(kunci setting `theme`). 52 tes lulus (`xvfb-run -a pytest -q`). Tangkapan layar: `docs/screenshots/{dark,light}/` (dibuat di Linux, bukan Windows).
**Belum diuji manusia:** skala DPI 125/150 %, scanner USB asli, glyph ikon pada Segoe UI Symbol, kontras pada monitor sebenarnya — lihat `docs/UI_Checklist_Windows.md`.
Pelajaran Tkinter: `CTkFrame` kosong = 200 px (pakai `holder()`); `CTkEntry` + `textvariable` menghilangkan placeholder; Treeview hanya warna per baris;
jangan menamai method `_draw` pada subclass widget CTk; `CTkTabview.configure` harus setelah tab dibuat.

**Belum / perlu dikerjakan:**
- Uji di Windows nyata + uji scanner USB HID + cetak label fisik; build `.exe` (`build_windows.bat`) belum pernah dijalankan.
- Panduan pengguna; pemetaan kolom impor di UI (service mendukung `mapping`, UI memakai urutan templat).
- Proses panjang (impor/ekspor/backup) berjalan di thread utama dengan kursor sibuk, belum di thread terpisah
  (koneksi SQLite terikat thread; perlu koneksi terpisah per thread).
- Lapisan `repositories/` tidak dibuat; SQL ada di service (penyederhanaan dari proposal §5.5).
- Backup otomatis hanya saat buka/tutup; belum ada pengingat berkala. Cetak kartu anggota, bukti pinjam: belum.
- Penyesuaian opname untuk eksemplar yang sedang dipinjam dilewati saat finalisasi (aman, tidak dilaporkan terpisah).
- UI belum diuji interaktif oleh manusia; hanya render, tes perilaku komponen, dan tangkapan layar di xvfb. Navigasi sidebar dengan keyboard belum ada.

## Isi repo
| Berkas | Keterangan |
|---|---|
| `docs/Proposal_Library_Management_System_Offline_v1.2.md` | Sumber kebenaran: kebutuhan FR-01..FR-11, skema DB, arsitektur, jadwal, pengujian |
| `docs/Libris_UI_UX_Prototype_v1.2.html` | Prototipe UI (acuan visual/alur, bukan kode produksi) |
| `main.py`, `config.py`, `app/`, `tests/` | Aplikasi dan pengujian (lihat README) |
| `handoff.md`, `patchnotes.md`, `changelog.md` | Dokumen serah terima dan riwayat |

## Keputusan kunci (jangan dilanggar; lihat Lampiran C proposal)
- Offline-first; tanpa XAMPP/Apache/PHP/MySQL. DB di `%LOCALAPPDATA%\Libris\`, bukan di folder instalasi.
- Judul (`books`) dipisahkan dari eksemplar (`book_copies`). Barcode eksemplar numerik 8 digit (Code 128), terpisah dari kode inventaris (`INV-2026-00182`).
- Status sirkulasi (Tersedia, Dipinjam, Perbaikan, Hilang, Dihapusbukukan) terpisah dari kondisi fisik (Baik … Tidak layak pakai).
- Password: PBKDF2-HMAC-SHA256, minimal 600.000 iterasi, salt per pengguna.
- Denda: disimpan final saat pengembalian (`fines`), pembayaran di `fine_payments`; denda berjalan hanya proyeksi. Uang = bilangan bulat rupiah.
- Stok opname: snapshot, cakupan rak dinamis, buku dipinjam tidak pernah otomatis hilang, penyesuaian butuh persetujuan + audit.
- Data berriwayat diarsipkan, bukan dihapus; hapus permanen hanya Administrator dan hanya tanpa riwayat. Semua edit/arsip/hapus/pulih masuk `audit_logs` (nilai lama/baru).
- Transaksi sirkulasi atomik; `PRAGMA foreign_keys=ON` di setiap koneksi; skema via migration.
- Grafik dashboard memakai canvas CustomTkinter (tanpa Matplotlib). Proses panjang di thread terpisah.

## Struktur kode
`app/database` (connection dengan `Tx` bersarang via SAVEPOINT, schema, migrations) · `app/services` (satu service per modul, dirakit di `app/context.py`) ·
`app/ui` (theme, components, pages_core/circ/admin, app) · `app/utils` (security, barcode, validators).
Aturan bisnis hanya di `services/`. Tambah perubahan skema dengan menambah fungsi di `MIGRATIONS`.

## Langkah berikutnya
1. Jalankan di Windows, uji scanner & label, bangun `.exe`, uji di Windows bersih (Fase 10).
2. Thread terpisah untuk proses panjang; pemetaan kolom impor; pengingat backup berkala.
3. Panduan pengguna & selaraskan dokumen proposal.

## Hal terbuka (proposal §13)
Jumlah akun petugas, format nomor anggota, durasi pinjam & tarif denda sebenarnya, batas pinjam, bulan opname, standar kerusakan, frekuensi/lokasi backup, kop/logo laporan.

## Catatan
- Proposal §2.2a masih menyebut "Prototipe v1.1" dan §2.1 memakai nama kerja lama "LMS Desktop"; selaraskan ke v1.2/"Libris" saat revisi dokumen.
- Nomor daftar di §12 tidak berurutan (1, 3, 4, 5, 6, 7, 9, 10).
- PBKDF2 memakai 600.000 iterasi; tes menurunkannya lewat `LIBRIS_PBKDF2_ITERATIONS` (jangan set di produksi).
