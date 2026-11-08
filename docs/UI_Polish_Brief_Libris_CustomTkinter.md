# Brief Pemolesan UI Libris (Opsi A: tetap CustomTkinter)

**Untuk:** Claude Code · **Repo:** Libris (Library Management System Offline) v0.1.0 **Letakkan berkas ini di:** `docs/UI_Polish_Brief_Libris_CustomTkinter.md` **Sumber acuan visual:** `docs/Libris_UI_UX_Prototype_v1.2.html` · **Acuan fungsional:** `docs/Proposal_Library_Management_System_Offline_v1.2.md` (§6) dan `handoff.md`

---

## 1. Tujuan

Aplikasi sudah berfungsi penuh (12 halaman, 42 tes), tetapi tampilannya terasa polos dan usang. Tugas ini hanya **memperbaiki lapisan tampilan** agar mendekati prototipe v1.2 sejauh yang dimungkinkan CustomTkinter/Tkinter, tanpa mengubah perilaku bisnis.

Yang diutamakan, berurutan:

1. Konsistensi visual (warna, jarak, huruf, tombol, kartu, tabel).
2. Dialog dan notifikasi yang terlihat modern (bukan `messagebox` bawaan Windows).
3. Alur kerja petugas berbasis scanner: fokus otomatis, umpan balik besar dan jelas.
4. Kerapian setiap halaman.

## 2. Aturan keras

- **Hanya ubah `app/ui/`** (dan berkas dokumentasi). **Dilarang** mengubah `app/services/`, `app/database/`, `app/utils/`, skema, atau tanda tangan fungsi service.
- **Jangan menambah dependensi** baru (tanpa CTkTable, tanpa Pillow-heavy asset pipeline, tanpa ttkbootstrap). `requirements.txt` dan `build_windows.bat` tidak boleh perlu diubah.
- Semua tes harus tetap lulus: `pytest -q` dan, untuk uji asap UI, `xvfb-run -a pytest -q`. Perbarui `tests/test_ui_smoke.py` hanya jika struktur halaman memang berubah.
- API komponen bersama **dipertahankan** agar halaman tidak perlu ditulis ulang: `info(msg)`, `confirm(msg) -> bool`, `guard(fn)`, `DataTable(columns, height, status_key, multi, on_double)` beserta `load/selected/selected_one`, `Toolbar.button/search/combo`, `FormDialog(master, title, fields, initial, on_save, width)`, `ScanEntry(master, on_scan, placeholder)`.
- Tanpa emoji berwarna (render tidak konsisten di Windows). Ikon hanya glyph Unicode yang ada di Segoe UI Symbol, atau teks.
- Tanpa animasi berat. Aplikasi dipakai di komputer perpustakaan yang mungkin sederhana.
- Jangan menjalankan atau mengubah proses build `.exe` (itu Fase 10 terpisah).

## 3. Temuan kondisi saat ini

| Temuan | Lokasi |
| --- | --- |
| Tema terang biru polos; prototipe bertema gelap dengan aksen cyan | `app/ui/theme.py` |
| Warna hex tersebar di luar tema (`#E3E8F0`, `#CDD5E3`, `#12315A`, `#C9D8EE`, `#E8EEF7`, dll.) | `components.py`, `app.py` |
| `messagebox` dipakai untuk semua info, konfirmasi, dan error | `components.py` (`guard`, `info`, `confirm`, `DataTable.selected_one`, `FormDialog._save`), `app.py:105` |
| `simpledialog.askinteger` dipakai langsung | `pages_admin.py:100` (tahun opname), `pages_circ.py:118` (biaya penggantian) |
| Tabel `ttk.Treeview` tema `clam` tanpa zebra, tinggi baris 26, status hanya warna teks | `components.py` (`DataTable`) |
| Sidebar hanya deretan tombol teks tanpa pengelompokan, penanda aktif, atau ikon | `app.py` (`build_main`) |
| Judul halaman diset di `Page.__init__` tanpa subjudul atau area aksi | `pages_core.py` (`Page`) |
| Daftar item peminjaman sementara berupa satu label teks | `pages_circ.py` (`LoansPage.pending`) |
| Grafik dashboard di canvas, batang polos tanpa garis bantu | `pages_core.py` (`DashboardPage._chart`) |

Kabar baik: pemakaian `info`, `confirm`, dan `guard` sudah terpusat, sehingga mengganti dialog cukup di `components.py` ditambah dua titik `simpledialog` dan satu titik di `app.py`.

## 4. Token desain

Sumber: `:root` pada prototipe v1.2. Buat di `theme.py` sebagai **dua palet** (`DARK`, `LIGHT`) dengan nama token yang sama. **DARK menjadi bawaan.** `LIGHT` diisi dengan warna terang yang sekarang ada di `theme.py` agar tidak ada regresi. Pemilih tema (Pengaturan) bersifat opsional, hanya jika waktu cukup (Fase 6).

| Token | DARK | Fungsi |
| --- | --- | --- |
| `BG` | `#0b1020` | Latar jendela |
| `PANEL` | `#111a2d` | Kartu, area konten |
| `PANEL2` | `#172238` | Header tabel, hover |
| `PANEL3` | `#1d2a43` | Item aktif, baris terpilih |
| `LINE` | `#263550` | Garis tepi 1 px |
| `TEXT` | `#edf3ff` | Teks utama |
| `SOFT` | `#c5d0e2` | Teks sekunder terang |
| `MUTED` | `#91a0ba` | Keterangan, placeholder |
| `ACCENT` | `#54d6e8` | Aksen utama (penanda aktif, progres, tombol utama) |
| `BLUE` | `#6b8cff` | Informasi, status Dipinjam |
| `PURPLE` | `#a78bfa` | Ekstra, administrator |
| `OK` | `#43c99a` | Berhasil, Tersedia, Lunas |
| `WARN` | `#f3bd62` | Peringatan, Perbaikan |
| `DANGER` | `#fb7185` | Error, Hilang, terlambat |

Warna badge (teks / latar / garis), dipakai untuk label status di kartu dan strip umpan balik:

| Jenis | Teks | Latar | Garis |
| --- | --- | --- | --- |
| green | `#78e0b3` | `#153a31` | `#245b49` |
| blue | `#8bb6ff` | `#1b2f50` | `#2c4773` |
| amber | `#f5cb7b` | `#42351d` | `#6c5428` |
| red | `#ff9cac` | `#442330` | `#713548` |
| purple | `#c3aaff` | `#30264c` | `#514076` |
| gray | `#b0bfd3` | `#273448` | `#3a4b63` |

Pemetaan `STATUS_COLORS` yang ada dipertahankan namanya, tetapi nilainya merujuk token di atas (Tersedia/Ditemukan/Lunas = `OK`; Dipinjam/Berjalan/Ditemukan ekstra = `BLUE` atau `PURPLE` sesuai prototipe; Perbaikan/Sebagian/Belum ditemukan/Pemeriksaan ulang = `WARN`; Hilang/Belum bayar/Hilang terkonfirmasi = `DANGER`; Dihapusbukukan/Belum diperiksa = `MUTED`; Final = `OK`).

**Skala jarak:** 4, 8, 12, 16, 24 px. Padding halaman 24; jarak antarkartu 16; padding dalam kartu 16 sampai 18. **Skala huruf (Segoe UI):** judul halaman 22 bold; judul seksi 15 bold; isi 13; keterangan 12; header tabel 11 bold huruf kapital; isi tabel 10 pt (ttk). Angka statistik 26 bold. **Radius:** kartu 14, tombol 9, input 9. **Tinggi kontrol:** tombol dan input 34 (kolom scan 42).

## 5. Fase kerja

Kerjakan **berurutan**. Setiap fase: ubah, jalankan tes, ambil tangkapan layar, commit dengan pesan jelas (`ui: fase N - ...`).

### Fase 1: Fondasi tema (`theme.py`)

- Refactor `theme.py` menjadi token (bagian 4), dua palet, fungsi `apply(mode)`, skala huruf dan jarak sebagai konstanta, serta helper `font(...)` yang sudah ada.
- Tambah `badge_style(kind)` yang mengembalikan (teks, latar, garis) dan `status_kind(status) -> kind`.
- Ganti **semua** hex dan warna literal di `components.py`, `app.py`, dan `pages_*.py` dengan token.
- `ctk.set_appearance_mode("dark")` bila palet DARK aktif.
- **Selesai bila:** `grep -nE '#[0-9a-fA-F]{6}' app/ui` hanya menemukan `theme.py`; aplikasi tampil gelap dan tetap berfungsi.

### Fase 2: Dialog dan notifikasi (`components.py`)

- Ganti isi `info(msg)` dan `confirm(msg)` dengan dialog `CTkToplevel` bergaya: judul, ikon glyph, pesan (multi baris dan `wraplength`), tombol. Pertahankan tanda tangan dan nilai kembali (`confirm` mengembalikan `bool`).
- Perilaku dialog: terpusat di atas jendela induk, `transient` + `grab_set` (tunda \~120 ms seperti `FormDialog`), **Esc = batal**, **Enter = tombol utama**, fokus awal pada tombol utama, dapat diuji di xvfb.
- Tambah `toast(master, pesan, jenis="ok|warn|error", durasi=2500)`: kartu kecil di pojok kanan bawah yang hilang sendiri. Pakai untuk pesan sukses non-kritis (mis. "Pengaturan disimpan", "Templat tersimpan", "Label tersimpan", "Log diekspor"). Konfirmasi, peringatan, dan error tetap modal.
- `guard()` memakai dialog baru untuk `ServiceError` (peringatan) dan kesalahan tak terduga (error).
- Ganti `messagebox` di `DataTable.selected_one`, `FormDialog._save`, dan `app.py:105`.
- `FormDialog._save`: tampilkan `ServiceError` **sebagai teks merah di dalam dialog** (label di atas tombol), bukan popup.
- Ganti `simpledialog.askinteger` di `pages_admin.py:100` dan `pages_circ.py:118` dengan dialog angka bergaya (boleh memakai `FormDialog` satu field). Perilaku dan validasi tetap sama.
- `filedialog` tetap bawaan (native memang tepat).
- **Selesai bila:** `messagebox` dan `simpledialog` tidak diimpor di luar `components.py`; semua alur yang memakai `info/confirm` tetap berjalan.

### Fase 3: Shell, sidebar, header halaman (`app.py`, `Page`)

- Sidebar: blok merek (nama "Libris" + subjudul kecil), menu **dikelompokkan** mengikuti sidebar pada prototipe v1.2, setiap item dengan glyph ikon, penanda aktif berupa garis kiri 3 px `ACCENT` + latar `PANEL3`, hover `PANEL2`. Blok profil di bawah (nama, peran) dan tombol Keluar. Item admin-only tetap disembunyikan untuk Petugas.
- `Page`: header terstandar dengan judul, **subjudul opsional**, dan **area aksi kanan** (mis. tombol utama halaman). Tambah method `header_actions()` atau parameter sederhana; halaman yang ada dimigrasi satu per satu.
- Padding halaman 24, latar `BG`, konten di dalam `Card` bila berupa kelompok kontrol.
- Layar login: kartu di tengah dengan merek, teks pengantar, kolom (tinggi 38), pesan error **inline** merah, dan Enter untuk masuk (sudah ada, pertahankan). Mode "pengaturan awal" tetap.
- **Selesai bila:** semua halaman memakai header yang sama; sidebar menampilkan kelompok, ikon, dan penanda aktif.

### Fase 4: Komponen data (`DataTable`, `Card`, `StatCard`, `Toolbar`)

- **`DataTable`:** gaya `ttk` selaras palet, tinggi baris 34 (kalikan dengan faktor skala DPI, lihat bagian 6), baris selang-seling (tag `odd/even`), header datar `PANEL2` berhuruf kapital kecil, tanpa garis tepi, warna baris terpilih `PANEL3`, indikator fokus halus. Status ditampilkan sebagai `● Teks` berwarna lewat tag (Treeview tidak mendukung badge per sel; jangan memaksakan). Tambah **keadaan kosong** ("Belum ada data") sebagai label di atas tabel saat `load([])`. Opsional: klik header untuk mengurutkan di sisi klien.
- **`Card`:** latar `PANEL`, garis 1 px `LINE`, radius 14.
- **`StatCard`:** label kecil huruf kapital `MUTED` di atas, angka besar di bawah, dengan parameter warna aksen (garis kecil atau teks angka berwarna). Dashboard memberi warna aksen berbeda per metrik.
- **`Toolbar.button`:** empat varian terstandar: `primary`, `secondary`, `danger`, `ghost`; tinggi 34. Pertahankan parameter `danger` dan `secondary` yang ada; tambah `variant=` bila perlu.
- **Selesai bila:** tidak ada warna atau gaya tombol/kartu yang didefinisikan ulang di halaman; semua tabel tampil seragam.

### Fase 5: Halaman dan alur

- **Dashboard:** kartu statistik 4×2 dengan aksen warna; peringatan backup sebagai banner `Card` berwarna `WARN` dengan ikon (bukan label teks polos); progres opname sebagai `Card` dengan `CTkProgressBar`; grafik canvas dipoles: garis bantu horizontal tipis `LINE`, batang `ACCENT`, label nilai di atas batang, sumbu dan label bulan `MUTED`, ukuran mengikuti lebar kartu dan digambar ulang saat `<Configure>` (dengan debounce).
- **Peminjaman dan Pengembalian (alur scanner):**
  - `ScanEntry` lebih besar (tinggi 42, huruf 15), fokus otomatis saat halaman tampil (`refresh`) dan setelah setiap aksi.
  - **Strip umpan balik** besar di bawah kolom scan: hijau saat berhasil (judul, penulis, barcode), merah saat gagal (pesan `ServiceError`), bertahan sampai pemindaian berikutnya.
  - Daftar eksemplar sementara pada `LoansPage` diganti tabel kecil (`DataTable`) dengan aksi **hapus item** sebelum konfirmasi. Logika tetap memakai `self.codes`; hanya presentasi dan penghapusan item dari daftar halaman yang bertambah.
  - Ringkasan anggota (nama, nomor, jumlah pinjaman aktif) tampil sebagai kartu kecil, bukan satu label panjang.
- **Stok Opname:** strip umpan balik yang sama untuk hasil pemindaian; deret penghitung (Belum diperiksa, Ditemukan, Dipinjam, Belum ditemukan, Hilang terkonfirmasi, Ekstra) sebagai `StatCard` kecil; `CTkProgressBar` untuk cakupan rak.
- **Detail Buku:** kartu informasi judul di atas, tabel eksemplar dengan warna status, aksi massal di toolbar.
- **Denda, Laporan, Backup, Impor & Label, Petugas, Pengaturan:** bagi isi menjadi `Card` bertajuk (judul seksi + isi), jarak konsisten, tombol sesuai varian. Pengaturan dikelompokkan per kartu (kebijakan peminjaman, denda, backup, laporan).
- **Selesai bila:** setiap halaman memakai header, kartu, tabel, dan tombol standar; alur scan memberi umpan balik yang jelas tanpa dialog.

### Fase 6: Mutu, dokumentasi, dan penutup

- Perbarui dan jalankan seluruh tes (`pytest -q`, `xvfb-run -a pytest -q`).
- Ambil tangkapan layar semua halaman di xvfb (misalnya lewat `import -window root` atau `scrot`) dan simpan di `docs/screenshots/` untuk ditinjau manusia.
- Daftar periksa manual untuk Windows (tulis di `docs/UI_Checklist_Windows.md`, jangan klaim sudah diuji): skala layar 100/125/150 %, fokus kolom scan dengan scanner USB, navigasi hanya dengan keyboard (Tab, Enter, Esc), ukuran jendela minimum (1100×680), judul panjang terpotong dengan baik, kontras teks.
- Perbarui `README.md` (bagian UI), `changelog.md`, `patchnotes.md`, dan `handoff.md` (status UI, hal yang belum diuji manusia).
- Opsional bila waktu cukup: pemilih tema gelap/terang di Pengaturan dan penyimpanan pilihan lewat `settings_service` yang sudah ada **tanpa mengubah service**; bila membutuhkan perubahan service, lewati dan catat di `handoff.md`.

## 6. Catatan teknis Tkinter/CustomTkinter

- `ttk.Style` dikonfigurasi **sekali** (di `theme.apply`), bukan di setiap `DataTable`. Warna baris terpilih lewat `style.map("Libris.Treeview", background=[("selected", PANEL3)], foreground=[("selected", TEXT)])`.
- `Treeview` tidak mengikuti skala DPI CustomTkinter. Kalikan `rowheight` dan ukuran huruf dengan faktor skala jendela (verifikasi API yang tersedia pada versi CustomTkinter terpasang, atau hitung dari `tk scaling`).
- Dialog `CTkToplevel` di Windows kadang gagal `grab_set` bila dipanggil langsung; pola `after(120, grab_set)` pada `FormDialog` sudah benar, pakai ulang.
- Canvas tidak memakai warna tema otomatis; baca token saat menggambar dan gambar ulang saat tema berganti.
- Hindari `place`/`grid` yang membuat tata letak bergantung pada ukuran piksel tetap; jendela dapat diubah ukurannya (minimum 1100×680).
- Operasi panjang (impor, ekspor, backup) masih di thread utama dengan kursor sibuk (`busy()` di `pages_admin.py`). Itu di luar lingkup tugas ini; jangan diubah.

## 7. Definisi selesai

- [ ] Tidak ada hex warna di luar `theme.py`.
- [ ] `messagebox` dan `simpledialog` tidak dipakai di luar `components.py`.
- [ ] Semua halaman memakai header, `Card`, `DataTable`, dan varian tombol standar.
- [ ] Alur Peminjaman, Pengembalian, dan Opname memiliki fokus otomatis dan strip umpan balik.
- [ ] `pytest -q` dan `xvfb-run -a pytest -q` lulus (42 tes atau lebih).
- [ ] `app/services/`, `app/database/`, `requirements.txt`, `build_windows.bat` tidak berubah.
- [ ] Tangkapan layar semua halaman tersimpan di `docs/screenshots/`.
- [ ] `README.md`, `changelog.md`, `patchnotes.md`, `handoff.md` diperbarui; hal yang belum diuji manusia dinyatakan jujur.

## 8. Cara bekerja

1. Baca `handoff.md`, bagian 6 proposal, dan buka prototipe HTML v1.2 sebagai acuan visual.
2. Kerjakan Fase 1 sampai 6 **berurutan tanpa menunggu konfirmasi**. Berhenti hanya bila ada tes yang gagal dan tidak dapat diperbaiki dalam lingkup ini.
3. Bila batas Tkinter menghalangi tampilan persis seperti prototipe, pilih solusi sederhana yang konsisten dan catat keputusannya di `changelog.md`; jangan menambah dependensi demi meniru prototipe.
4. Di akhir setiap fase, tulis ringkasan satu paragraf: apa yang diubah, hasil tes, dan hal yang perlu ditinjau manusia.