# Handoff — Libris (Library Management System Offline)

Tanggal: 2026-11-08 · Status proyek: **tahap perancangan, belum ada kode aplikasi**

## Ringkasan
Libris adalah aplikasi perpustakaan desktop offline untuk Windows 10/11 (satu workstation).
Stack: Python 3.12, CustomTkinter, SQLite (`sqlite3`), OpenPyXL, ReportLab, python-barcode, PyInstaller, pytest.

## Isi repo saat ini
| Berkas | Keterangan |
|---|---|
| `docs/Proposal_Library_Management_System_Offline_v1.2.md` | Sumber kebenaran: kebutuhan FR-01..FR-11, skema DB, arsitektur, jadwal, pengujian |
| `docs/Libris_UI_UX_Prototype_v1.2.html` | Prototipe UI (acuan visual/alur, bukan kode produksi) |
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

## Struktur kode yang direncanakan
Lihat proposal §5.5: `main.py`, `config.py`, `app/{database,models,repositories,services,ui,utils}`, `tests/`.
Aturan bisnis hanya di `services/`, bukan di callback GUI.

## Langkah berikutnya (urut fase proposal §8)
1. **Fase 1** — fondasi: repo Python, venv, `requirements.txt`, koneksi SQLite, skema 14 tabel, migration, tes constraint.
2. **Fase 2** — jendela utama, sidebar, login/peran, halaman Petugas & Log, tema (`ui/theme.py`), dashboard.
3. **Fase 3** — CRUD buku/eksemplar/anggota, arsip/pulih/hapus (§3.3.2), barcode.
4. Fase 4–10: impor & label, sirkulasi, denda, laporan, backup, stok opname, testing & packaging.

Estimasi total 8–10 minggu (40–52 hari kerja).

## Hal terbuka (proposal §13)
Jumlah akun petugas, format nomor anggota, durasi pinjam & tarif denda sebenarnya, batas pinjam, bulan opname, standar kerusakan, frekuensi/lokasi backup, kop/logo laporan.

## Catatan
- Proposal §2.2a masih menyebut "Prototipe v1.1" dan §2.1 memakai nama kerja lama "LMS Desktop"; selaraskan ke v1.2/"Libris" saat revisi dokumen.
- Nomor daftar di §12 tidak berurutan (1, 3, 4, 5, 6, 7, 9, 10).
- Belum ada pengujian karena belum ada kode.
