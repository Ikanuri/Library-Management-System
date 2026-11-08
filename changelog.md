# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/).

## [Belum dirilis]

### Diubah (pemolesan UI, hanya `app/ui/`)
- **Tema:** token DARK (bawaan, dari `:root` prototipe v1.2) dan LIGHT di `theme.py`; `apply(mode)`, `badge_style`, `status_kind`. Tidak ada warna literal di luar `theme.py` (dijaga oleh tes).
- **Dialog:** `info/confirm/warn/error` kini dialog `CTkToplevel` bergaya (Enter = utama, Esc = batal, terpusat, `grab_set` tertunda); `toast()` untuk sukses non-kritis; `ask_int()` menggantikan `simpledialog`; `FormDialog` menampilkan error inline merah. `messagebox`/`simpledialog` tidak lagi dipakai.
- **Shell:** sidebar berkelompok (Workspace, Sirkulasi, Pengelolaan, Sistem) dengan ikon, garis kiri aksen untuk item aktif, blok profil; topbar dengan breadcrumb dan penanda "MODE OFFLINE"; header halaman standar (judul, subjudul, area aksi); layar login baru.
- **Komponen:** `DataTable` (zebra, header huruf kapital, status `● Teks`, keadaan kosong, urut klik header, kolom menyesuaikan lebar, tinggi baris mengikuti DPI), `Card`, `StatCard` beraksen, `Toolbar` dengan varian primary/secondary/danger/ghost, `FeedbackStrip`, `ScanEntry` besar dengan `on_error` inline.
- **Halaman:** Dashboard (banner peringatan, kartu opname dengan progress bar, grafik dengan garis bantu dan gambar ulang saat resize); Peminjaman (kartu anggota, daftar sementara berupa tabel dengan hapus item); Pengembalian/Opname (strip umpan balik, fokus otomatis); Pengaturan per kartu; Detail Buku dengan kartu info.
- **Opsional dikerjakan:** pilihan tema Gelap/Terang di Pengaturan, tersimpan lewat `settings_service` (kunci `theme`) tanpa mengubah service.

### Keputusan karena batas Tkinter
- Treeview hanya mendukung warna per **baris**. Status tampil sebagai `● Teks`; hanya status yang perlu perhatian (biru/kuning/merah/ungu) mewarnai baris, sedangkan hijau (Tersedia, Aktif, Lunas) dan abu tetap berteks biasa agar tabel tidak hijau seluruhnya.
- `CTkEntry` tidak menampilkan placeholder bila memakai `textvariable`; kolom pencarian dan filter tanggal memakai entry langsung (`.get()`).
- `CTkFrame` kosong bawaannya setinggi 200 px; pembungkus kosong memakai `holder()`.
- Scrollbar tabel memakai `CTkScrollbar` agar mengikuti tema.
- Glyph ikon sidebar: `↑`/`↓` dipakai untuk Impor/Backup (bukan `⇪`/`⤓` dari prototipe) agar aman di Segoe UI Symbol.
- Operasi panjang tetap di thread utama (di luar lingkup).

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
