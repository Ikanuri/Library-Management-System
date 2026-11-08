# PROPOSAL PENGEMBANGAN APLIKASI PERPUSTAKAAN OFFLINE

## Library Management System (LMS) Desktop "Libris" Berbasis Python dan SQLite

**Versi dokumen:** 1.2\
**Status:** Proposal rancangan teknis\
**Platform sasaran:** Windows 10/11\
**Model penggunaan:** Satu komputer (single-user workstation)\
**Mode operasional:** Offline\
**Teknologi utama:** Python, CustomTkinter, SQLite\
**Prototipe UI terkait:** Libris UI/UX Prototype v1.2 (selaras dengan dokumen ini)

------------------------------------------------------------------------

# Ringkasan Perubahan (v1.1 dan v1.2)

Versi ini menyelaraskan proposal dengan prototipe UI Libris v1.2 dan memperbaiki konsistensi aturan bisnis.

| Area | Perubahan |
|---|---|
| Nama | "LMS Desktop" menjadi "Libris" sebagai nama aplikasi |
| Login dan petugas | Halaman login, peran Administrator dan Petugas, halaman Petugas dan log aktivitas |
| Status dan kondisi | Enumerasi status sirkulasi dan kondisi fisik ditetapkan (3.3.1) |
| Barcode | Barcode eksemplar numerik 8 digit, dipisahkan dari kode inventaris |
| Denda | Siklus denda (berjalan, ditetapkan, lunas), tabel `fines` dan `fine_payments`, kebijakan buku hilang atau rusak berat |
| Stok opname | Hasil pemeriksaan dipisahkan dari kondisi, alur status, cakupan rak dinamis, dua jenis temuan ekstra, log pemindaian |
| Impor dan label | Impor Excel dan cetak label massal dipindah dari pengembangan lanjutan ke versi awal (FR-11) |
| Backup | Pemicu saat aplikasi dibuka dan ditutup, peringatan drive sama dan backup usang |
| Teknologi | Matplotlib dihapus; hashing dengan PBKDF2 dari `hashlib`; lokasi data `%LOCALAPPDATA%` |
| Jadwal | 9 fase menjadi 10 fase; estimasi menjadi 8--10 minggu |
| Dokumen | Rumus dan daftar yang rusak pada v1.0 diperbaiki |
| Edit dan hapus (v1.2) | Ubah bebas, arsip, pemulihan, hapus permanen, dan operasi massal untuk judul dan eksemplar (3.3.2) |

------------------------------------------------------------------------

# Ringkasan Eksekutif

Proposal ini menguraikan rencana pengembangan **Library Management
System (LMS) Desktop**, yaitu aplikasi manajemen perpustakaan yang
berjalan secara lokal pada komputer Windows tanpa memerlukan XAMPP,
Apache, PHP, MySQL Server, koneksi internet, maupun layanan server
eksternal.

Aplikasi dirancang menggunakan Python sebagai bahasa pemrograman,
CustomTkinter sebagai perangkat antarmuka grafis, dan SQLite sebagai
basis data lokal. SQLite menyimpan data dalam satu berkas database
sehingga instalasi dan pemeliharaan relatif sederhana untuk lingkungan
perpustakaan yang mengoperasikan aplikasi dari satu komputer.

Cakupan aplikasi meliputi autentikasi petugas, dashboard, pengelolaan
bibliografi dan eksemplar buku, pengelolaan anggota, transaksi
peminjaman dan pengembalian, perhitungan denda, laporan Excel dan PDF,
pencadangan serta pemulihan database, dan **stok opname tahunan berbasis
barcode**.

Fitur stok opname ditambahkan sebagai modul audit inventaris. Modul ini
memungkinkan petugas membuat periode pemeriksaan, mengambil snapshot
inventaris, memeriksa eksemplar secara fisik, mencatat kondisi,
melakukan rekonsiliasi, serta menghasilkan laporan selisih. Status
pemeriksaan dipisahkan dari status sirkulasi buku agar buku yang sedang
dipinjam tidak keliru dinyatakan hilang.

Pengembangan direncanakan melalui sepuluh fase dengan estimasi
keseluruhan sekitar **8--10 minggu**, bergantung pada ketersediaan waktu
pengembang, kecepatan pengujian, dan penyesuaian kebutuhan operasional.

------------------------------------------------------------------------

# 1. Pendahuluan

## 1.1 Latar Belakang

Pengelolaan perpustakaan melibatkan berbagai aktivitas yang saling
berkaitan, seperti pendataan koleksi, pencatatan anggota, peminjaman,
pengembalian, penghitungan denda, penyusunan laporan, dan pemeriksaan
inventaris. Apabila aktivitas tersebut dikelola secara manual atau
menggunakan berkas yang terpisah, petugas dapat mengalami kesulitan
dalam menjaga konsistensi data, menelusuri riwayat transaksi, mengetahui
ketersediaan koleksi, dan menyusun laporan secara berkala.

Digitalisasi pengelolaan perpustakaan dapat membantu menyatukan
aktivitas tersebut dalam satu sistem. Namun, tidak semua lingkungan
perpustakaan membutuhkan aplikasi berbasis web atau server. Untuk
perpustakaan yang mengoperasikan layanan melalui satu komputer, aplikasi
desktop offline dapat menjadi alternatif yang lebih sederhana.

Aplikasi desktop lokal tidak memerlukan XAMPP atau server database
terpisah. Data dapat disimpan dalam SQLite dan diakses langsung oleh
aplikasi. Dengan demikian, operasional utama tetap dapat berjalan tanpa
internet.

Selain sirkulasi buku, perpustakaan juga perlu memastikan bahwa data
inventaris sesuai dengan kondisi fisik koleksi. Oleh sebab itu, sistem
ini mencakup fitur stok opname tahunan. Pemeriksaan dilakukan pada
tingkat eksemplar, bukan hanya berdasarkan jumlah judul, sehingga setiap
buku fisik dapat diidentifikasi melalui barcode unik.

## 1.2 Identifikasi Permasalahan

Permasalahan yang hendak ditangani melalui aplikasi ini meliputi:

1.  Data buku dan anggota perlu dikelola secara terpusat.
2.  Petugas memerlukan cara cepat untuk mengetahui ketersediaan setiap
    eksemplar.
3.  Peminjaman dan pengembalian perlu dicatat secara konsisten.
4.  Keterlambatan pengembalian perlu dihitung berdasarkan aturan denda
    yang dapat dikonfigurasi.
5.  Laporan operasional perlu dapat dihasilkan tanpa rekapitulasi manual
    yang berulang.
6.  Data perlu memiliki mekanisme backup dan restore.
7.  Perpustakaan memerlukan prosedur pemeriksaan inventaris tahunan.
8.  Hasil pemeriksaan fisik perlu dibandingkan dengan catatan database
    agar buku yang sesuai, rusak, belum ditemukan, hilang, atau
    ditemukan di luar daftar dapat ditindaklanjuti.

## 1.3 Rumusan Masalah

1.  Bagaimana merancang aplikasi perpustakaan desktop yang sepenuhnya
    dapat digunakan secara offline pada Windows?
2.  Bagaimana mengelola data bibliografi, eksemplar, anggota, dan
    transaksi secara terintegrasi?
3.  Bagaimana menerapkan peminjaman dan pengembalian berbasis barcode?
4.  Bagaimana menghitung denda keterlambatan secara otomatis dan
    konsisten?
5.  Bagaimana menghasilkan laporan operasional dalam format Excel dan
    PDF?
6.  Bagaimana menjaga keamanan dan ketersediaan data melalui backup dan
    restore?
7.  Bagaimana melaksanakan stok opname tahunan dan merekonsiliasi hasil
    pemeriksaan fisik dengan data inventaris?

## 1.4 Tujuan

### Tujuan Umum

Mengembangkan aplikasi manajemen perpustakaan berbasis desktop yang
dapat beroperasi secara offline pada satu komputer Windows, dengan
pengelolaan sirkulasi dan inventaris yang terintegrasi.

### Tujuan Khusus

1.  Menyediakan sistem pengelolaan buku dan eksemplar.
2.  Menyediakan sistem pendataan anggota.
3.  Mempermudah transaksi peminjaman dan pengembalian.
4.  Mengotomatisasi perhitungan denda.
5.  Menyediakan laporan dalam format Excel dan PDF.
6.  Menyediakan mekanisme backup dan restore database.
7.  Menyediakan fitur stok opname tahunan berbasis barcode.
8.  Menjaga konsistensi, integritas, dan keterlacakan data.

## 1.5 Manfaat

**Bagi petugas perpustakaan:**

- Mengurangi pencatatan manual.
- Mempercepat pencarian buku dan anggota.
- Mempermudah transaksi sirkulasi.
- Mempermudah penyusunan laporan.
- Membantu pemeriksaan inventaris tahunan.

**Bagi pengelola perpustakaan:**

- Memperoleh ringkasan kondisi koleksi.
- Mengetahui riwayat peminjaman dan pengembalian.
- Mengetahui selisih inventaris.
- Memiliki arsip digital yang lebih terstruktur.

**Bagi pengembangan sistem:**

- Menyediakan fondasi modular yang dapat dikembangkan.
- Memisahkan aturan bisnis, antarmuka, dan akses database.
- Memungkinkan penambahan fitur pada versi berikutnya tanpa harus membangun ulang seluruh aplikasi.

------------------------------------------------------------------------

# 2. Gambaran Umum Sistem

## 2.1 Nama dan Identitas Sistem

Nama kerja sistem: **Library Management System (LMS) Desktop**.

Sistem merupakan aplikasi desktop untuk pengelolaan operasional
perpustakaan yang digunakan pada satu komputer Windows.

## 2.2 Karakteristik Sistem

  Aspek                Spesifikasi
  -------------------- -----------------------------------------------
  Bentuk aplikasi      Desktop
  Sistem operasi       Windows 10/11
  Penggunaan           Satu komputer
  Koneksi              Offline
  Bahasa pemrograman   Python 3.12 atau versi stabil yang kompatibel
  GUI                  CustomTkinter
  Database             SQLite
  Akses database       Modul `sqlite3` bawaan Python
  Barcode              Code 128
  Pemindai             USB barcode scanner mode HID
  Ekspor Excel         OpenPyXL
  Ekspor PDF           ReportLab
  Grafik               Canvas CustomTkinter
  Packaging            PyInstaller
  IDE                  Visual Studio Code

Versi dependensi final harus dikunci dan diuji sebelum aplikasi dikemas
menjadi executable. Versi Python yang dipilih harus kompatibel dengan
seluruh pustaka yang digunakan.

## 2.2a Hubungan dengan Prototipe UI

Prototipe Libris v1.1 (HTML) adalah acuan visual dan alur, bukan kode produksi. Padanan halaman dan kebutuhan:

| Halaman prototipe | Kebutuhan |
|---|---|
| Login, Petugas dan Log | FR-01 |
| Dashboard | FR-02 |
| Katalog Buku, Detail Buku | FR-03 |
| Anggota | FR-04 |
| Peminjaman, Pengembalian | FR-05, FR-06 |
| Denda dan Pembayaran | FR-07 |
| Laporan | FR-08 |
| Backup dan Restore | FR-09 |
| Stok Opname | FR-10 |
| Impor dan Label | FR-11 |

Catatan implementasi CustomTkinter: status ditampilkan sebagai teks berwarna atau warna baris (`ttk.Treeview` tidak mendukung badge per sel); grafik batang digambar pada canvas; warna dan ukuran huruf dikelola di `ui/theme.py`; proses panjang (impor, ekspor, backup) dijalankan di thread terpisah agar jendela tidak membeku.

## 2.3 Prinsip Perancangan

1.  **Offline-first:** fungsi inti tidak bergantung pada internet.
2.  **Local data ownership:** database berada pada penyimpanan lokal
    komputer.
3.  **Modular:** setiap modul memiliki tanggung jawab yang jelas.
4.  **Data integrity:** transaksi dan relasi data dijaga melalui
    constraint serta transaksi database.
5.  **Traceability:** perubahan penting dan penyesuaian inventaris dapat
    ditelusuri.
6.  **Maintainability:** kode dipisahkan ke dalam lapisan dan modul.
7.  **Recoverability:** tersedia mekanisme backup dan restore yang dapat
    diuji.

## 2.4 Batasan Sistem

Versi awal sistem memiliki batasan berikut:

-   Hanya ditujukan untuk satu komputer Windows.
-   Tidak menyediakan sinkronisasi antarkomputer.
-   Tidak menyediakan akses jarak jauh atau aplikasi mobile.
-   Tidak memerlukan server web.
-   Tidak menyediakan katalog publik berbasis internet.
-   Tidak mencakup integrasi pembayaran elektronik.
-   Tidak mengasumsikan ketersediaan perangkat RFID.
-   Fitur barcode menggunakan scanner USB yang berperilaku seperti
    keyboard.
-   Penggunaan satu akun atau beberapa akun petugas dapat disesuaikan,
    tetapi sistem tetap dioperasikan dari satu workstation.

Jika pada masa mendatang perpustakaan membutuhkan banyak komputer yang
mengakses data secara bersamaan, arsitektur perlu dievaluasi kembali.
SQLite lokal tidak boleh sekadar diletakkan pada folder jaringan dan
dipakai sebagai pengganti server database multi-user.

------------------------------------------------------------------------

# 3. Ruang Lingkup dan Modul Aplikasi

## 3.1 Autentikasi dan Pengguna

**Kode kebutuhan: FR-01**

Fungsi:

- Login dan logout.
- Pengelolaan akun petugas.
- Penyimpanan password dalam bentuk hash.
- Pembatasan akses berdasarkan peran jika diperlukan.
- Pencatatan aktivitas penting.

Data pengguna:

- ID pengguna.
- Username.
- Password hash.
- Nama petugas.
- Peran.
- Status akun.
- Waktu pembuatan dan pembaruan.

Password tidak boleh disimpan sebagai teks biasa. Gunakan PBKDF2-HMAC-SHA256 (`hashlib.pbkdf2_hmac`) dengan salt acak per pengguna dan jumlah iterasi sesuai rekomendasi terbaru (minimal 600.000), atau `hashlib.scrypt`. Keduanya tersedia di pustaka standar sehingga tidak menambah dependensi.

Peran: **Administrator** (kelola petugas, pengaturan, restore, finalisasi dan penyesuaian opname) dan **Petugas** (sirkulasi, data koleksi dan anggota, pemindaian opname). Login gagal berulang dibatasi sementara. Akun nonaktif tidak dapat masuk. Log aktivitas (login, perubahan data, restore, penyesuaian) ditampilkan pada halaman Petugas dan Log, dan dapat diekspor.

## 3.2 Dashboard

**Kode kebutuhan: FR-02**

Dashboard menampilkan ringkasan operasional, antara lain:

- Total judul buku.
- Total eksemplar.
- Eksemplar tersedia.
- Eksemplar sedang dipinjam.
- Total anggota aktif.
- Transaksi peminjaman hari ini.
- Buku terlambat.
- Statistik peminjaman bulanan.
- Ringkasan denda.
- Ringkasan progres stok opname ketika periode pemeriksaan sedang berlangsung.

Dashboard merupakan tampilan ringkasan. Data rinci tetap tersedia pada
modul masing-masing.

## 3.3 Manajemen Buku dan Eksemplar

**Kode kebutuhan: FR-03**

Sistem membedakan **judul/bibliografi** dengan **eksemplar fisik**.

Satu judul dapat memiliki beberapa eksemplar. Setiap eksemplar mempunyai
barcode unik.

### Data bibliografi

-   ID buku.
-   ISBN.
-   Judul.
-   Penulis.
-   Penerbit.
-   Tahun terbit.
-   Kategori.
-   Deskripsi.
-   Lokasi atau klasifikasi rak.
-   Path gambar sampul (opsional).

### Data eksemplar

-   ID eksemplar.
-   ID bibliografi.
-   Kode inventaris.
-   Barcode.
-   Tanggal perolehan (opsional).
-   Sumber perolehan (opsional).
-   Lokasi rak.
-   Status sirkulasi.
-   Kondisi terakhir yang diketahui.

Fungsi:

- Tambah, ubah, lihat, arsipkan, pulihkan, dan hapus permanen data buku (aturan 3.3.2).
- Tambah, ubah, arsipkan, pulihkan, dan hapus eksemplar, termasuk operasi massal (aturan 3.3.2).
- Membuat atau mencetak barcode.
- Pencarian berdasarkan judul, penulis, ISBN, kode inventaris, atau barcode.
- Filter berdasarkan kategori dan lokasi rak.
- Menampilkan riwayat sirkulasi eksemplar.

Penghapusan permanen dibatasi jika data sudah memiliki riwayat
transaksi. Sistem lebih mengutamakan penonaktifan daripada menghapus
rekam historis.

### 3.3.1 Status, Kondisi, dan Barcode

Dua atribut eksemplar disimpan terpisah:

| Atribut | Nilai |
|---|---|
| Status sirkulasi | Tersedia, Dipinjam, Perbaikan, Hilang, Dihapusbukukan |
| Kondisi fisik | Baik, Rusak ringan, Rusak sedang, Rusak berat, Tidak layak pakai |

Aturan: kondisi Rusak berat atau Tidak layak pakai saat pengembalian mengusulkan status Perbaikan atau Hilang/Dihapusbukukan dan memerlukan konfirmasi petugas. Eksemplar berstatus selain Tersedia tidak dapat dipinjamkan.

Barcode eksemplar adalah **kode numerik 8 digit** yang unik (Code 128). Kode inventaris yang mudah dibaca manusia (misalnya `INV-2026-00182`) disimpan terpisah dan dicetak pada label. Kode numerik dipilih karena scanner HID mengetik melalui layout keyboard dan hasilnya dapat berubah akibat Caps Lock atau tanda baca. Service tetap menormalkan input (trim, huruf besar).

Antarmuka: halaman Detail Buku menampilkan daftar eksemplar (barcode, kode inventaris, rak, status, kondisi), penambahan eksemplar, dan cetak label.

### 3.3.2 Edit, Arsip, Hapus, dan Pemulihan

Perubahan data dapat dilakukan bebas dan seluruhnya tercatat. Penghapusan permanen hanya diizinkan bila tidak merusak riwayat transaksi.

| Operasi | Judul (bibliografi) | Eksemplar |
|---|---|---|
| Edit | Semua field: ISBN, judul, penulis, penerbit, tahun, kategori, rak, deskripsi, sampul | Barcode, kode inventaris, rak, kondisi, status Tersedia atau Perbaikan |
| Validasi | Judul wajib; ISBN unik bila diisi | Barcode 8 digit angka dan unik; kode inventaris unik; perubahan barcode memberi peringatan cetak ulang label |
| Arsip | Untuk judul berriwayat; judul hilang dari pencarian sirkulasi dan semua eksemplar aktifnya ikut diarsipkan | Untuk eksemplar berriwayat; status menjadi Hilang atau Dihapusbukukan dengan alasan |
| Hapus permanen | Hanya bila seluruh eksemplarnya tanpa riwayat; eksemplar ikut terhapus dalam satu transaksi | Hanya bila tanpa riwayat |
| Pemulihan | Arsip kembali menjadi aktif | Kembali ke status Tersedia |
| Massal | Tidak tersedia pada versi awal | Ubah terpilih (rak, kondisi, status) dan hapus atau arsip terpilih, dengan ringkasan hasil |

Aturan:

1. **Riwayat** berarti ada baris pada `loan_items`, `fines`, atau `stock_opname_items` yang merujuk data tersebut.
2. Judul atau eksemplar yang sedang dipinjam tidak dapat diarsipkan atau dihapus; sistem menampilkan alasannya. Status Dipinjam hanya diubah oleh sirkulasi.
3. Hapus permanen memerlukan konfirmasi, hanya dapat dilakukan Administrator, dan tidak dapat dibatalkan. Arsip dan pemulihan dapat dilakukan Petugas maupun Administrator.
4. Perubahan data master tidak mengubah snapshot opname. Eksemplar yang diarsipkan selama sesi opname aktif tetap berada dalam snapshot dan ditandai pada rekonsiliasi.
5. Setiap edit, arsip, hapus, dan pemulihan dicatat di `audit_logs` (pengguna, waktu, nilai lama, nilai baru).
6. Operasi massal memproses tiap item menurut aturan di atas; item yang dilewati dilaporkan beserta alasannya.

Antarmuka: halaman Katalog memiliki tombol Edit dan Hapus pada setiap baris, filter tampilan (Aktif, Diarsipkan, Semua), dan form Tambah buku. Halaman Detail Buku memiliki kotak centang, tombol Ubah terpilih dan Hapus/arsip terpilih, form Tambah eksemplar, serta filter koleksi aktif dan keluar koleksi.

## 3.4 Manajemen Anggota

**Kode kebutuhan: FR-04**

Data anggota:

- ID anggota.
- Nomor induk/nomor anggota.
- Nama.
- Jenis anggota.
- Alamat.
- Nomor telepon.
- Email (opsional).
- Tanggal pendaftaran.
- Status keanggotaan.
- Catatan (opsional).

Fungsi:

- Tambah, ubah, lihat, dan nonaktifkan anggota.
- Pencarian anggota.
- Pencetakan kartu anggota dengan barcode (opsional).
- Melihat riwayat peminjaman.
- Memeriksa status keanggotaan.

Anggota nonaktif tidak dapat membuat transaksi peminjaman baru. Riwayat
transaksinya tetap disimpan.

## 3.5 Peminjaman

**Kode kebutuhan: FR-05**

Alur:

1. Petugas membuka menu peminjaman.
2. Petugas memindai barcode anggota atau mencari anggota.
3. Sistem memvalidasi status anggota.
4. Petugas memindai satu atau beberapa barcode eksemplar.
5. Sistem memeriksa status setiap eksemplar.
6. Sistem menentukan tanggal pinjam dan jatuh tempo berdasarkan pengaturan.
7. Petugas mengonfirmasi transaksi.
8. Sistem menyimpan transaksi dan memperbarui status sirkulasi eksemplar.
9. Sistem dapat menghasilkan bukti peminjaman.

Aturan:

- Anggota harus aktif.
- Eksemplar harus tersedia.
- Eksemplar yang sudah dipinjam atau tidak layak dipinjam tidak boleh dipinjamkan.
- Batas jumlah buku per anggota dapat diatur.
- Durasi peminjaman dapat diatur.
- Pencatatan transaksi harus bersifat atomik: seluruh perubahan berhasil atau seluruhnya dibatalkan jika terjadi kesalahan.

## 3.6 Pengembalian

**Kode kebutuhan: FR-06**

Alur:

1. Petugas membuka menu pengembalian.
2. Petugas memindai barcode eksemplar.
3. Sistem mencari transaksi aktif yang terkait.
4. Sistem menampilkan anggota, judul, tanggal pinjam, dan jatuh tempo.
5. Petugas mencatat tanggal pengembalian dan kondisi buku.
6. Sistem menghitung keterlambatan serta denda.
7. Sistem menyimpan pengembalian dan memperbarui status sirkulasi.
8. Sistem menampilkan ringkasan pengembalian.

Pengembalian dapat dilakukan sebagian. Artinya, satu transaksi yang
berisi beberapa buku tidak harus ditutup sekaligus ketika hanya sebagian
eksemplar yang dikembalikan.

Pengembalian kedua atas eksemplar yang sudah dikembalikan harus ditolak
atau ditangani melalui prosedur koreksi yang tercatat.

Aturan kondisi saat kembali: kondisi dicatat pada `loan_items`. Kondisi Rusak berat atau Tidak layak pakai mengikuti aturan 3.3.1 dan kebijakan penggantian pada 3.7.

## 3.7 Perhitungan Denda

**Kode kebutuhan: FR-07**

Rumus dasar:

```text
Denda = max(0, hari_terlambat - masa_tenggang) x tarif_per_hari
hari_terlambat = tanggal_kembali - tanggal_jatuh_tempo
```

Keterangan:

- Denda dihitung per eksemplar yang terlambat dan dibatasi batas maksimum bila diaktifkan.
- Masa tenggang bernilai 0 secara bawaan.
- Tanggal jatuh tempo dan tanggal kembali disimpan sebagai tanggal (ISO 8601).

Contoh parameter awal untuk pengujian:

- Durasi pinjam: 7 hari.
- Tarif denda: Rp1.000 per hari.
- Pengembalian terlambat: 3 hari.
- Denda: Rp3.000.

Nilai di atas adalah contoh konfigurasi, bukan ketentuan yang tidak
dapat diubah.

Pengaturan denda:

- Tarif per hari.
- Masa pinjam.
- Batas maksimum denda (opsional).
- Masa tenggang (opsional).
- Kebijakan hari kalender atau hari operasional, jika dibutuhkan.

Sistem harus menyimpan nilai denda yang dikenakan pada transaksi agar
perubahan tarif di masa depan tidak mengubah perhitungan historis secara
retroaktif.

Pembayaran denda perlu dibedakan dari pengenaan denda. Jika pembayaran
dicatat, data minimal meliputi nominal, tanggal, status pembayaran, dan
petugas penerima.

### Siklus denda

1. **Berjalan:** pinjaman terlambat yang belum dikembalikan menampilkan denda proyeksi. Denda ini belum dapat dibayar karena masih bertambah setiap hari.
2. **Ditetapkan:** saat pengembalian, sistem menyimpan nilai denda final (tarif dan hari saat itu) pada tabel `fines`.
3. **Dibayar:** pembayaran dicatat pada `fine_payments` (nominal, tanggal, petugas); status menjadi Sebagian atau Lunas.

Pengaturan tambahan: batas maksimum denda, perhitungan hari kalender atau hari operasional, dan **kebijakan buku hilang atau rusak berat** (ganti buku, bayar harga buku, atau ditentukan petugas). Kebijakan ini juga dipakai ketika opname menetapkan eksemplar Hilang terkonfirmasi yang masih terkait pinjaman. Seluruh nilai uang disimpan sebagai bilangan bulat rupiah.

## 3.8 Laporan

**Kode kebutuhan: FR-08**

Laporan yang disediakan:

1.  Daftar bibliografi.
2.  Daftar seluruh eksemplar.
3.  Daftar anggota.
4.  Laporan peminjaman berdasarkan periode.
5.  Laporan pengembalian berdasarkan periode.
6.  Laporan keterlambatan.
7.  Laporan denda yang dikenakan dan pembayaran denda.
8.  Statistik buku paling sering dipinjam.
9.  Ringkasan inventaris.
10. Laporan stok opname dan selisih inventaris.
11. Log audit aktivitas.

Pada antarmuka, laporan dikelompokkan menjadi enam kategori: Koleksi dan katalog (1, 2, 9), Keanggotaan (3), Sirkulasi (4, 5, 6, 8), Keuangan dan denda (7), Stok opname (10), Audit aktivitas (11).


Fitur laporan:

- Filter tanggal/periode.
- Filter kategori atau status.
- Pratinjau data.
- Ekspor Excel (.xlsx).
- Ekspor PDF.
- Informasi waktu pembuatan laporan.
- Identitas petugas pembuat laporan.

Laporan harus dihasilkan dari query yang konsisten dengan data
transaksi. Angka pada laporan harus dapat ditelusuri ke data sumbernya.

## 3.9 Backup dan Restore

**Kode kebutuhan: FR-09**

Fungsi:

- Backup manual.
- Backup otomatis sesuai kebijakan aplikasi.
- Pemilihan lokasi penyimpanan.
- Riwayat backup.
- Restore dari file backup.
- Validasi database sebelum pemulihan.
- Konfirmasi sebelum menimpa database aktif.

Backup otomatis dapat dijalankan pada saat aplikasi ditutup secara
normal dan/atau melalui pengingat berkala. Namun, backup saat penutupan
bukan satu-satunya perlindungan karena komputer dapat mati mendadak.

Gunakan SQLite Backup API (`Connection.backup()`) atau mekanisme aman
lain yang sesuai. Jangan menyalin file database aktif secara sembarangan
ketika transaksi sedang berlangsung.

Sebelum restore:

1. Pastikan file backup dipilih dengan benar.
2. Validasi bahwa file merupakan database SQLite yang dapat dibaca.
3. Buat backup dari database aktif sebagai langkah pengamanan.
4. Tutup koneksi yang relevan.
5. Lakukan pemulihan.
6. Buka kembali database dan jalankan pemeriksaan integritas.

Backup harus disimpan pada media atau lokasi lain yang dapat bertahan
jika komputer utama rusak. Salinan pada drive yang sama tidak cukup
untuk menghadapi kerusakan perangkat.

Pemicu backup: saat aplikasi dibuka, saat ditutup secara normal, dan pengingat berkala. Aplikasi tidak menjalankan backup terjadwal jika tidak sedang dibuka. Dashboard memberi peringatan jika backup terakhir lebih dari 7 hari, atau jika folder backup berada pada drive fisik yang sama dengan database. Simpan sejumlah salinan terakhir (retensi dapat diatur) dan salin ke media eksternal. Database berada di `%LOCALAPPDATA%\Libris\` untuk satu akun Windows; bila beberapa akun Windows memakai komputer yang sama, gunakan `C:\ProgramData\Libris\` dengan izin tulis eksplisit.

## 3.10 Stok Opname Tahunan

**Kode kebutuhan: FR-10**

### 3.10.1 Tujuan

Melakukan pemeriksaan fisik koleksi perpustakaan secara berkala, dengan
target satu kali dalam satu tahun, untuk mengetahui kesesuaian antara
catatan inventaris dan keadaan fisik setiap eksemplar.

### 3.10.2 Konsep

Stok opname dilaksanakan pada tingkat eksemplar. Setiap eksemplar yang
terdaftar mempunyai identitas unik berupa barcode.

Sistem membuat periode pemeriksaan, misalnya **Stok Opname Tahun 2027**.
Ketika periode dimulai, sistem membuat snapshot daftar eksemplar yang
menjadi cakupan pemeriksaan. Snapshot diperlukan agar daftar pemeriksaan
tidak berubah hanya karena data bibliografi atau status eksemplar
diperbarui setelah kegiatan dimulai.

### 3.10.3 Tahapan kegiatan

1.  Petugas membuat sesi stok opname.
2.  Sistem menetapkan tahun, tanggal mulai, petugas penanggung jawab,
    dan catatan.
3.  Sistem mengambil snapshot inventaris.
4.  Petugas memeriksa buku secara fisik.
5.  Petugas memindai barcode atau memasukkan kode secara manual.
6.  Sistem mencocokkan kode dengan daftar snapshot.
7.  Petugas mencatat kondisi dan lokasi aktual.
8.  Sistem menampilkan progres dan hasil sementara.
9.  Petugas melakukan pemeriksaan ulang atas item yang belum ditemukan
    atau bermasalah.
10. Petugas melakukan rekonsiliasi.
11. Petugas menyelesaikan dan mengunci sesi.
12. Sistem menghasilkan laporan final.

### 3.10.4 Hasil Pemeriksaan dan Kondisi Fisik

Hasil pemeriksaan dan kondisi fisik adalah dua atribut berbeda. "Rusak" bukan hasil; laporan menurunkannya dari kondisi selain Baik.

| Hasil pemeriksaan | Makna |
|---|---|
| Belum diperiksa | Belum dipindai pada pemeriksaan pertama |
| Ditemukan | Dipindai dan cocok dengan snapshot |
| Belum ditemukan | Tidak dipindai setelah pemeriksaan pertama selesai |
| Hilang terkonfirmasi | Tidak ditemukan setelah pemeriksaan ulang, disetujui petugas |
| Ditemukan ekstra | Dipindai tetapi tidak ada dalam cakupan snapshot |
| Dipinjam | Sedang dipinjam; diverifikasi melalui catatan sirkulasi |

Kondisi memakai enumerasi pada 3.3.1. Alur status: Belum diperiksa menjadi Ditemukan saat dipindai; setelah pemeriksaan pertama ditutup, sisanya menjadi Belum ditemukan; pemeriksaan ulang menghasilkan Ditemukan atau Hilang terkonfirmasi.

### 3.10.5 Sirkulasi Selama Sesi (Cakupan Rak Dinamis)

Peminjaman dan pengembalian tetap berjalan selama sesi. Aturannya:

- Eksemplar yang sedang dipinjam keluar dari cakupan rak dan berstatus Dipinjam; tidak pernah otomatis Hilang.
- Eksemplar yang dikembalikan selama sesi otomatis masuk kembali ke cakupan rak sebagai Belum diperiksa dan wajib dipindai.
- Eksemplar yang dipindai lalu dipinjam setelahnya tetap berhasil Ditemukan.
- Eksemplar yang masih dipinjam saat finalisasi dicatat Dipinjam, terverifikasi melalui sirkulasi.

### 3.10.6 Rekonsiliasi dan Temuan Ekstra

Sistem membandingkan snapshot dengan hasil pemeriksaan, per judul dan per eksemplar, lalu menampilkan usulan penyesuaian. Status eksemplar baru berubah setelah persetujuan petugas.

Temuan ekstra ada dua jenis: (a) barcode dikenal tetapi tidak ada dalam snapshot, misalnya eksemplar yang ditambahkan setelah sesi dimulai; (b) barcode tidak dikenal. Keduanya dicatat melalui tindakan "Catat sebagai ekstra" dan ditinjau sebelum masuk inventaris.

### 3.10.7 Aturan bisnis stok opname

1.  Satu sesi mempunyai identitas dan periode yang jelas.
2.  Sistem mencegah sesi tahunan ganda yang tidak disengaja.
3.  Satu eksemplar hanya memiliki satu hasil pemeriksaan final per sesi.
4.  Pemindaian barcode yang sama berulang harus ditangani sebagai
    pemindaian duplikat, bukan menambah jumlah temuan.
5.  Barcode yang tidak dikenal dicatat sebagai temuan ekstra atau item
    yang perlu ditinjau, bukan langsung dimasukkan ke inventaris.
6.  Item yang belum ditemukan tidak langsung dinyatakan hilang.
7.  Buku yang sedang dipinjam tidak otomatis dinyatakan hilang.
8.  Perubahan status setelah rekonsiliasi harus mempunyai alasan dan
    identitas petugas.
9.  Sesi yang telah difinalisasi dikunci dari perubahan biasa.
10. Koreksi setelah finalisasi harus melalui prosedur koreksi yang
    tercatat.
11. Hanya satu sesi aktif per tahun.
12. Setiap pemindaian dicatat pada `stock_opname_scans` (barcode, waktu, petugas, hasil) sebagai bukti, termasuk pemindaian duplikat yang ditolak.
13. Kombinasi (sesi, eksemplar) dan (sesi, barcode) bersifat unik pada `stock_opname_items`.

### 3.10.8 Laporan stok opname

Laporan sekurang-kurangnya memuat:

- Nama dan tahun kegiatan.
- Tanggal mulai dan selesai.
- Petugas penanggung jawab.
- Total eksemplar dalam snapshot.
- Total eksemplar diperiksa.
- Total belum diperiksa.
- Total sesuai.
- Total rusak berdasarkan kategori.
- Total sedang dipinjam.
- Total belum ditemukan.
- Total hilang terkonfirmasi.
- Total temuan ekstra.
- Daftar penyesuaian inventaris.
- Catatan dan persetujuan petugas.

### 3.10.9 Indikator Progres

Cakupan rak = jumlah eksemplar snapshot dikurangi eksemplar yang sedang dipinjam dan belum dikembalikan.

```text
P = (jumlah_diperiksa / cakupan_rak) x 100%
```

Contoh: snapshot 3.850, dipinjam 184, cakupan rak 3.666, diperiksa 2.511, maka P = 68,5%. Eksemplar Dipinjam ditampilkan terpisah sebagai "verifikasi sirkulasi" dan tidak dihitung pada P.

## 3.11 Impor Data dan Label Barcode

**Kode kebutuhan: FR-11**

Impor dan label termasuk versi awal karena koleksi yang sudah ada harus dimasukkan dan setiap eksemplar harus berlabel sebelum sirkulasi dan opname berbasis barcode dapat berjalan.

Impor Excel (.xlsx):

- Unduh templat; pilih berkas; petakan kolom.
- Validasi uji coba (dry-run): barcode ganda, ISBN tidak valid, kolom wajib kosong, kategori atau rak baru. Hasil ditampilkan per baris.
- Tidak ada data tersimpan sebelum konfirmasi; impor dilakukan dalam satu transaksi, gagal berarti seluruhnya dibatalkan.
- Barcode numerik 8 digit dibuat otomatis untuk eksemplar tanpa barcode.

Cetak label: lembar PDF (ReportLab) berisi Code 128, kode inventaris, judul singkat, dan rak; ukuran label dapat diatur. Cetak uji satu halaman dan uji pemindaian dengan scanner asli sebelum mencetak massal. Penempelan label fisik adalah pekerjaan terpisah dan perlu dijadwalkan sebelum sesi opname pertama.
------------------------------------------------------------------------

# 4. Kebutuhan Nonfungsional

## 4.1 Kinerja

-   Aplikasi dapat dibuka dan digunakan pada komputer Windows dengan
    spesifikasi memadai.
-   Pencarian data umum harus responsif untuk ukuran koleksi
    perpustakaan kecil hingga menengah.
-   Operasi database menggunakan indeks pada kolom pencarian dan relasi
    yang relevan.
-   Proses ekspor laporan tidak boleh membuat data transaksi menjadi
    tidak konsisten.

Target waktu respons final perlu diuji menggunakan volume data yang
realistis.

## 4.2 Keamanan

-   Password disimpan sebagai hash.
-   Validasi input dilakukan pada antarmuka dan service layer.
-   Query SQL menggunakan parameter binding, bukan menyusun query dari
    input pengguna secara langsung.
-   Database dan backup dibatasi aksesnya melalui izin folder Windows.
-   Aktivitas penting dicatat dalam audit log.
-   Restore memerlukan konfirmasi.
-   Data sensitif tidak ditampilkan pada log teknis secara berlebihan.

## 4.3 Integritas Data

-   Menggunakan foreign key.
-   Menggunakan unique constraint untuk barcode dan nomor anggota.
-   Menggunakan transaksi database untuk operasi yang melibatkan
    beberapa tabel.
-   Mengaktifkan foreign key pada setiap koneksi SQLite.
-   Menggunakan rollback jika operasi gagal.
-   Menyediakan pemeriksaan integritas database.

## 4.4 Kemudahan Penggunaan

-   Navigasi konsisten.
-   Formulir memiliki validasi dan pesan kesalahan yang jelas.
-   Kolom barcode mudah difokuskan untuk pemindaian berulang.
-   Status buku menggunakan label yang mudah dipahami.
-   Tersedia konfirmasi untuk tindakan penting.
-   Tersedia pencarian dan filter pada tabel data.

## 4.5 Keandalan dan Pemulihan

-   Backup dapat diverifikasi.
-   Restore diuji secara berkala.
-   Kegagalan proses tidak boleh meninggalkan transaksi setengah jadi.
-   Aplikasi menampilkan pesan yang jelas jika database tidak dapat
    dibuka.
-   Database tidak disimpan di dalam direktori instalasi yang mungkin
    tidak memiliki izin tulis.

------------------------------------------------------------------------

# 5. Arsitektur Teknis

## 5.1 Pola Arsitektur

Sistem menggunakan **Layered Architecture** yang terdiri atas empat
lapisan.

### A. Presentation Layer

Bertanggung jawab atas tampilan dan interaksi pengguna.

Teknologi:

- CustomTkinter.
- Tkinter/ttk untuk komponen tabel bila diperlukan.
- Canvas CustomTkinter untuk grafik batang dashboard.

Komponen:

- Login.
- Dashboard.
- Manajemen buku.
- Manajemen anggota.
- Peminjaman.
- Pengembalian.
- Denda.
- Laporan.
- Stok opname.
- Impor dan label.
- Petugas dan log aktivitas.
- Pengaturan.

### B. Application / Service Layer

Bertanggung jawab atas aturan bisnis.

Contoh:

- `BookService` - `MemberService` - `LoanService` - `ReturnService` - `FineService` - `ReportService` - `BackupService` - `StockOpnameService`

Aturan bisnis tidak boleh diletakkan seluruhnya di dalam callback tombol
GUI. Antarmuka memanggil service, kemudian service menjalankan validasi
dan proses bisnis.

### C. Data Access Layer

Bertanggung jawab atas komunikasi dengan SQLite.

Komponen:

- Repository buku.
- Repository eksemplar.
- Repository anggota.
- Repository transaksi.
- Repository stok opname.
- Repository laporan.

Repository mengelola query dan pemetaan hasil database ke objek atau
struktur data aplikasi.

### D. Database Layer

Menggunakan satu database SQLite lokal, dengan skema yang dikelola
melalui migration.

Database menyimpan data operasional, transaksi, konfigurasi, audit log,
dan hasil stok opname.

## 5.2 Diagram Arsitektur

``` mermaid
flowchart TD
    A[Petugas Perpustakaan] --> B[Presentation Layer<br/>CustomTkinter]
    B --> C[Application / Service Layer]
    C --> D[Data Access Layer / Repository]
    D --> E[(SQLite Database)]
    C --> F[Report Generator<br/>Excel / PDF]
    C --> G[Barcode Utilities]
    C --> H[Backup / Restore Service]
    H --> I[(Folder Backup)]
    G --> J[USB Barcode Scanner]
```

## 5.3 Rancangan Database

Database awal terdiri atas tabel berikut.

  Tabel                        Fungsi
  ---------------------------- -----------------------------------
  `books`                      Data bibliografi/judul
  `book_copies`                Data setiap eksemplar dan barcode
  `members`                    Data anggota
  `loans`                      Header transaksi peminjaman
  `loan_items`                 Detail eksemplar dalam transaksi
  `users`                      Akun petugas
  `settings`                   Pengaturan sistem
  `audit_logs`                 Riwayat aktivitas penting
  `stock_opname_sessions`      Sesi stok opname
  `stock_opname_items`         Snapshot dan hasil pemeriksaan
  `stock_opname_adjustments`   Riwayat penyesuaian inventaris
  `fines`                      Denda yang ditetapkan per eksemplar
  `fine_payments`              Pembayaran denda
  `stock_opname_scans`         Log setiap pemindaian opname

Tabel tambahan untuk kategori atau lokasi rak dapat ditambahkan saat implementasi tanpa mengubah konsep arsitektur.

### Penambahan Skema v1.1

- `loan_items`: `returned_at`, `return_condition`, `fine_id`.
- `book_copies`: `circulation_status`, `condition`, `inventory_code` (unik), `barcode` (unik, 8 digit).
- `fines`: `id`, `loan_item_id`, `days_late`, `rate`, `amount`, `status`, `assessed_at`.
- `fine_payments`: `id`, `fine_id`, `amount`, `paid_at`, `received_by`.
- `stock_opname_scans`: `id`, `session_id`, `barcode`, `scanned_at`, `scanned_by`, `outcome`.
- `stock_opname_items`: `result` dan `physical_condition` terpisah; `verification_status` bernilai ya atau tidak; unik pada (`session_id`, `copy_id`) dan (`session_id`, `barcode_snapshot`).

### Penambahan Skema v1.2

- `books`: `is_active`, `archived_at`, `archived_by`, `archived_reason`, `updated_at`, `updated_by`.
- `book_copies`: `archived_at`, `archived_by`, `archived_reason` (Hilang, Rusak tidak layak, Dihibahkan, Lainnya), `updated_at`, `updated_by`.
- `audit_logs`: `entity`, `entity_id`, `action`, `old_value`, `new_value` (JSON).
- Foreign key ke `books` dan `book_copies` memakai `ON DELETE RESTRICT`; hapus permanen dilakukan dalam satu transaksi setelah pemeriksaan riwayat.

### Relasi inti

-   Satu bibliografi mempunyai banyak eksemplar.
-   Satu anggota dapat mempunyai banyak transaksi.
-   Satu transaksi mempunyai satu atau lebih detail peminjaman.
-   Satu detail peminjaman merujuk pada satu eksemplar.
-   Satu sesi stok opname mempunyai banyak item pemeriksaan.
-   Satu eksemplar dapat muncul pada banyak sesi stok opname dari tahun
    ke tahun.
-   Satu sesi stok opname dapat menghasilkan beberapa penyesuaian
    inventaris.
-   Aktivitas penting dikaitkan dengan akun petugas.

### Rancangan field tambahan stok opname

**`stock_opname_sessions`**

- `id`
- `year`
- `name`
- `start_date`
- `end_date`
- `status`
- `created_by`
- `finalized_by`
- `created_at`
- `finalized_at`
- `notes`

**`stock_opname_items`**

- `id`
- `session_id`
- `copy_id` (dapat nullable untuk temuan ekstra)
- `barcode_snapshot`
- `book_title_snapshot`
- `inventory_code_snapshot`
- `location_snapshot`
- `circulation_status_snapshot`
- `result`
- `physical_condition`
- `actual_location`
- `notes`
- `inspected_by`
- `inspected_at`
- `verification_status`

**`stock_opname_adjustments`**

- `id`
- `session_id`
- `copy_id`
- `old_status`
- `new_status`
- `reason`
- `approved_by`
- `adjusted_at`

Snapshot menyimpan informasi yang relevan pada saat kegiatan dimulai.
Hal ini penting untuk menjaga nilai historis laporan meskipun data
master berubah di kemudian hari.

## 5.4 Diagram Relasi Konseptual

``` mermaid
erDiagram
    BOOKS ||--o{ BOOK_COPIES : has
    MEMBERS ||--o{ LOANS : makes
    USERS ||--o{ LOANS : processes
    LOANS ||--|{ LOAN_ITEMS : contains
    BOOK_COPIES ||--o{ LOAN_ITEMS : borrowed
    STOCK_OPNAME_SESSIONS ||--o{ STOCK_OPNAME_ITEMS : contains
    BOOK_COPIES ||--o{ STOCK_OPNAME_ITEMS : inspected
    STOCK_OPNAME_SESSIONS ||--o{ STOCK_OPNAME_ADJUSTMENTS : generates
    BOOK_COPIES ||--o{ STOCK_OPNAME_ADJUSTMENTS : concerns
    USERS ||--o{ AUDIT_LOGS : performs
    LOAN_ITEMS ||--o| FINES : incurs
    FINES ||--o{ FINE_PAYMENTS : paid_by
    STOCK_OPNAME_SESSIONS ||--o{ STOCK_OPNAME_SCANS : records
```

## 5.5 Struktur Direktori Proyek

``` text
library_management/
│
├── main.py
├── config.py
├── requirements.txt
│
├── app/
│   ├── database/
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── migrations.py
│   │
│   ├── models/
│   │   ├── book.py
│   │   ├── book_copy.py
│   │   ├── member.py
│   │   ├── loan.py
│   │   ├── user.py
│   │   └── stock_opname.py
│   │
│   ├── repositories/
│   │   ├── book_repository.py
│   │   ├── member_repository.py
│   │   ├── book_copy_repository.py
│   │   ├── user_repository.py
│   │   ├── fine_repository.py
│   │   ├── loan_repository.py
│   │   └── stock_opname_repository.py
│   │
│   ├── services/
│   │   ├── book_service.py
│   │   ├── loan_service.py
│   │   ├── return_service.py
│   │   ├── fine_service.py
│   │   ├── report_service.py
│   │   ├── backup_service.py
│   │   ├── auth_service.py
│   │   ├── audit_service.py
│   │   ├── settings_service.py
│   │   ├── import_service.py
│   │   ├── label_service.py
│   │   └── stock_opname_service.py
│   │
│   ├── ui/
│   │   ├── theme.py
│   │   ├── components/        (tabel, badge, modal, input scan)
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   ├── books.py
│   │   ├── members.py
│   │   ├── loans.py
│   │   ├── returns.py
│   │   ├── reports.py
│   │   ├── book_detail.py
│   │   ├── stock_opname.py
│   │   ├── import_labels.py
│   │   ├── users.py
│   │   └── settings.py
│   │
│   └── utils/
│       ├── barcode.py
│       ├── validators.py
│       └── helpers.py
│
├── assets/
│   ├── icons/
│   └── images/
│
├── tests/
│   ├── test_books.py
│   ├── test_loans.py
│   ├── test_returns.py
│   ├── test_fines.py
│   ├── test_auth.py
│   ├── test_members.py
│   ├── test_backup.py
│   ├── test_import.py
│   └── test_stock_opname.py
│
└── backups/
```

Folder `backups/` di dalam source tree dapat digunakan saat
pengembangan. Pada aplikasi produksi, lokasi database dan backup harus
berada pada direktori data pengguna atau lokasi yang ditentukan melalui
pengaturan.

------------------------------------------------------------------------

# 6. Desain Antarmuka Pengguna

## 6.1 Prinsip Desain

-   Tampilan desktop modern dan sederhana.
-   Sidebar untuk navigasi utama.
-   Dashboard menggunakan kartu statistik.
-   Tabel data mempunyai pencarian dan filter.
-   Formulir dibuat konsisten.
-   Warna status digunakan secara konsisten.
-   Ukuran komponen sesuai penggunaan dengan mouse dan keyboard.
-   Pemindaian barcode dapat dilakukan tanpa banyak perpindahan fokus.

## 6.2 Struktur Navigasi

1.  Dashboard
2.  Koleksi Buku (termasuk Detail Buku)
3.  Anggota
4.  Peminjaman
5.  Pengembalian
6.  Denda
7.  Stok Opname
8.  Impor dan Label
9.  Laporan
10. Backup dan Restore
11. Petugas dan Log (Administrator)
12. Pengaturan

## 6.3 Halaman Stok Opname

Halaman terdiri atas tiga tab, sesuai prototipe.

**Pemeriksaan scan:** kolom barcode (Enter mengirim), kondisi fisik, tombol catat, pesan hasil (berhasil, duplikat, tidak dikenal dengan tombol "Catat sebagai ekstra"), dan tabel pemeriksaan terbaru. Ringkasan di atas halaman menampilkan Belum diperiksa, Ditemukan (dengan jumlah kondisi rusak), Dipinjam (verifikasi sirkulasi), Hilang terkonfirmasi, dan Temuan ekstra, serta bar progres cakupan rak.

**Rekonsiliasi:** ringkasan snapshot, diperiksa, belum diperiksa, dipinjam, dan tahap penutupan (selesaikan pemeriksaan, verifikasi lanjutan, tinjau usulan penyesuaian, setujui dan finalisasi).

**Riwayat sesi:** daftar sesi per tahun dengan status dan akses ke laporan final.

Tambahan pada aplikasi final: lokasi aktual dan catatan pada form pemeriksaan, progres per rak, dan ekspor daftar belum diperiksa.
------------------------------------------------------------------------

# 7. Perangkat Keras dan Perangkat Lunak

## 7.1 Perangkat Keras Minimum

  Komponen        Rekomendasi
  --------------- ----------------------------------
  Komputer        PC/laptop Windows
  RAM             8 GB disarankan
  Penyimpanan     SSD disarankan
  Scanner         USB barcode scanner HID
  Printer         Printer A4 untuk laporan
  Printer label   Opsional
  Media backup    Flash drive atau media eksternal

Spesifikasi aktual perlu disesuaikan dengan jumlah koleksi, ukuran
gambar sampul, dan kebutuhan operasional.

## 7.2 Perangkat Lunak Pengembangan

-   Python.
-   Visual Studio Code.
-   Git.
-   Virtual environment (`venv`).
-   CustomTkinter.
-   SQLite.
-   OpenPyXL.
-   ReportLab.
-   python-barcode.
-   PyInstaller.
-   Pustaka pengujian seperti pytest.

## 7.3 Perangkat Lunak Pengguna

Pengguna akhir cukup menjalankan aplikasi hasil packaging. Python tidak
harus dipasang secara terpisah apabila executable dibangun dengan benar
dan seluruh dependensi telah disertakan.

------------------------------------------------------------------------

# 8. Roadmap dan Jadwal Implementasi

Estimasi pengembangan: **8--10 minggu**.

| Fase | Aktivitas | Estimasi |
|---|---|---|
| 1 | Fondasi proyek dan database | 3--4 hari |
| 2 | Antarmuka, navigasi, dan login | 5--6 hari |
| 3 | Manajemen buku, eksemplar, anggota, barcode | 6--8 hari |
| 4 | Impor Excel dan cetak label | 3--4 hari |
| 5 | Peminjaman dan pengembalian | 5--6 hari |
| 6 | Denda | 3--4 hari |
| 7 | Laporan Excel dan PDF | 4--5 hari |
| 8 | Backup dan restore | 2--3 hari |
| 9 | Stok opname tahunan | 5--7 hari |
| 10 | Testing, perbaikan, dan deployment | 4--5 hari |

Total 40--52 hari kerja.

Estimasi hari kerja tersebut merupakan perkiraan aktivitas. Waktu
kalender dapat lebih panjang apabila pengembangan dilakukan paruh waktu
atau terdapat perubahan kebutuhan.

## 8.1 Fase 1 --- Fondasi Proyek

Aktivitas:

- Membuat repository proyek.
- Menyiapkan Python dan virtual environment.
- Menyiapkan struktur folder.
- Membuat koneksi SQLite.
- Membuat schema awal.
- Mengaktifkan foreign key.
- Membuat migration dasar.

Kriteria selesai:

- Aplikasi dapat membuka database.
- Schema dapat dibuat dari kondisi kosong.
- Constraint dasar berjalan.
- Database dapat diuji melalui skrip.

## 8.2 Fase 2 --- Antarmuka

Aktivitas:

- Membuat jendela utama.
- Membuat sidebar.
- Membuat halaman login dan peran pengguna.
- Membuat halaman Petugas dan log aktivitas.
- Membuat tema dan komponen bersama.
- Membuat dashboard.
- Membuat komponen tabel dan formulir.

Kriteria selesai:

- Navigasi berfungsi.
- Tampilan konsisten.
- Data dummy dapat ditampilkan.

## 8.3 Fase 3 --- Manajemen Data dan Barcode

Aktivitas:

- CRUD bibliografi.
- CRUD eksemplar.
- Arsip, pemulihan, dan hapus permanen sesuai aturan 3.3.2.
- Ubah dan hapus atau arsip massal eksemplar.
- CRUD anggota.
- Pencarian dan filter.
- Pembuatan barcode.
- Uji scanner USB.

Kriteria selesai:

- Barcode unik.
- Data dapat dicari.
- Pemindaian mengisi kolom dengan benar.
- Relasi bibliografi dan eksemplar berjalan.
- Hapus permanen ditolak bila ada riwayat atau pinjaman aktif.
- Arsip dapat dipulihkan.
- Setiap perubahan tercatat di log.

## 8.4 Fase 4 --- Impor Data dan Label Barcode

Aktivitas:

- Templat dan pemetaan kolom Excel.
- Validasi uji coba dan impor atomik.
- Pembuatan barcode otomatis.
- Cetak label PDF dan uji pindai.

Kriteria selesai:

- Impor gagal tidak meninggalkan data parsial.
- Barcode hasil impor unik.
- Label tercetak dapat dibaca scanner yang digunakan.

## 8.5 Fase 5 --- Transaksi Sirkulasi

Aktivitas:

- Form peminjaman.
- Validasi anggota.
- Validasi ketersediaan.
- Pemindaian barcode.
- Pengembalian sebagian dan penuh.
- Riwayat transaksi.

Kriteria selesai:

- Tidak ada peminjaman ganda atas eksemplar yang sama.
- Transaksi gagal tidak meninggalkan perubahan parsial.
- Pengembalian memperbarui status dengan benar.

## 8.6 Fase 6 --- Denda

Aktivitas:

- Pengaturan durasi.
- Pengaturan tarif.
- Perhitungan keterlambatan.
- Siklus denda (berjalan, ditetapkan, lunas) dan kebijakan buku hilang atau rusak berat.
- Pencatatan pembayaran bila diaktifkan.
- Riwayat denda.

Kriteria selesai:

- Pengembalian tepat waktu menghasilkan denda nol.
- Keterlambatan menghasilkan perhitungan sesuai kebijakan.
- Perubahan tarif tidak mengubah denda historis.

## 8.7 Fase 7 --- Laporan

Aktivitas:

- Query laporan.
- Filter periode.
- Ekspor Excel.
- Ekspor PDF.
- Statistik dashboard.

Kriteria selesai:

- Hasil ekspor sesuai data sumber.
- Format laporan dapat dibaca.
- Filter tanggal bekerja benar.

## 8.8 Fase 8 --- Backup dan Restore

Aktivitas:

- Backup manual.
- Backup terjadwal atau pengingat.
- Validasi backup.
- Restore.
- Pengujian pemulihan.

Kriteria selesai:

- Backup dapat dibuka.
- Restore mengembalikan data yang benar.
- Database aktif dicadangkan sebelum restore.
- Kegagalan restore tidak menghilangkan database aktif.

## 8.9 Fase 9 --- Stok Opname

Aktivitas:

- Pembuatan sesi.
- Snapshot inventaris.
- Pemeriksaan barcode.
- Pencatatan kondisi.
- Penanganan buku yang sedang dipinjam (cakupan rak dinamis).
- Temuan ekstra dan log pemindaian.
- Rekonsiliasi.
- Penyesuaian dengan persetujuan.
- Laporan stok opname.

Kriteria selesai:

- Snapshot tidak berubah ketika data master berubah.
- Pemindaian duplikat ditangani.
- Buku yang sedang dipinjam tidak otomatis dianggap hilang.
- Item yang belum ditemukan dapat diverifikasi ulang.
- Penyesuaian inventaris tercatat.
- Sesi final tidak dapat diubah melalui operasi biasa.

## 8.10 Fase 10 --- Testing dan Deployment

Aktivitas:

- Pengujian unit.
- Pengujian integrasi.
- Pengujian alur operasional.
- Pengujian backup/restore.
- Packaging dengan PyInstaller.
- Uji pada Windows yang bersih.
- Penyusunan panduan pengguna.

Kriteria selesai:

- Aplikasi dapat dijalankan dari executable.
- Database berada pada lokasi data pengguna.
- Tidak memerlukan internet untuk fungsi inti.
- Backup dan restore berfungsi.
- Tidak ada bug kritis yang diketahui pada skenario penerimaan.

------------------------------------------------------------------------

# 9. Strategi Pengujian dan Kriteria Penerimaan

## 9.1 Pengujian Fungsional

  ------------------------------------------------------------------------
                           No. Skenario              Hasil yang diharapkan
  ---------------------------- --------------------- ---------------------
                             1 Login dengan akun     Berhasil
                               valid                 

                             2 Login dengan password Ditolak
                               salah                 

                             3 Menambah buku         Data tersimpan

                             4 Menambah eksemplar    Ditolak
                               dengan barcode        
                               duplikat              

                             5 Menambah anggota      Data tersimpan

                             6 Anggota nonaktif      Ditolak
                               meminjam              

                             7 Meminjam eksemplar    Berhasil
                               tersedia              

                             8 Meminjam eksemplar    Ditolak
                               yang sudah dipinjam   

                             9 Mengembalikan tepat   Denda nol
                               waktu                 

                            10 Mengembalikan         Denda Rp3.000
                               terlambat 3 hari      
                               dengan tarif          
                               Rp1.000/hari          

                            11 Mengembalikan         Ditolak atau
                               eksemplar dua kali    memerlukan koreksi
                                                     tercatat

                            12 Ekspor laporan        File valid

                            13 Backup database       File backup valid

                            14 Restore database      Data kembali utuh

                            15 Memindai barcode saat Item cocok dengan
                               stok opname           snapshot

                            16 Memindai barcode dua  Duplikasi ditangani
                               kali pada sesi yang   
                               sama                  

                            17 Memeriksa buku yang   Tidak otomatis
                               sedang dipinjam       dianggap hilang

                            18 Memfinalisasi sesi    Sesi terkunci
                               stok opname           

                            19 Menyesuaikan status   Alasan dan petugas
                               inventaris            tercatat
  ------------------------------------------------------------------------

### Skenario Tambahan v1.1

- Login petugas menyembunyikan menu Petugas dan Log.
- Impor Excel dengan barcode ganda ditolak pada validasi uji coba.
- Denda pada pinjaman terlambat yang belum kembali tampil sebagai proyeksi dan tidak dapat dibayar.
- Eksemplar dikembalikan selama opname masuk kembali ke cakupan rak.
- Pemindaian barcode tidak dikenal dapat dicatat sebagai ekstra.
- Backup lebih dari 7 hari atau pada drive yang sama menampilkan peringatan.
- Edit judul dengan ISBN yang sudah dipakai ditolak.
- Edit barcode eksemplar dengan nilai duplikat atau bukan 8 digit ditolak.
- Hapus judul atau eksemplar yang sedang dipinjam ditolak dengan alasan.
- Item berriwayat hanya dapat diarsipkan; item tanpa riwayat dapat dihapus permanen oleh Administrator saja.
- Pemulihan arsip mengembalikan item ke status aktif.
- Hapus massal melewati item dipinjam dan melaporkan jumlahnya.
- Setiap edit, arsip, hapus, dan pemulihan muncul di log aktivitas.

## 9.2 Pengujian Integritas

Pengujian harus mencakup:

- Foreign key.
- Unique barcode.
- Unique nomor anggota.
- Transaksi atomik.
- Rollback.
- Konsistensi status eksemplar.
- Kesesuaian jumlah laporan dengan data sumber.
- Konsistensi snapshot stok opname.

## 9.3 Pengujian Pemulihan

Simulasikan:

- Aplikasi ditutup secara normal.
- Aplikasi dihentikan mendadak.
- Komputer mati saat tidak ada transaksi.
- Komputer mati saat transaksi berlangsung.
- File backup rusak.
- Restore dari backup yang valid.

Tujuannya memastikan database tetap dapat digunakan atau dapat
dipulihkan melalui prosedur yang telah disediakan.

## 9.4 Kriteria Penerimaan Akhir

Aplikasi dapat dinyatakan siap digunakan apabila:

1. Seluruh modul dalam ruang lingkup telah berfungsi.
2. Transaksi peminjaman dan pengembalian menjaga integritas data.
3. Barcode dapat dibaca oleh scanner yang digunakan.
4. Denda dihitung sesuai pengaturan.
5. Laporan Excel dan PDF dapat dihasilkan.
6. Backup dan restore berhasil diuji.
7. Stok opname dapat dilaksanakan sampai finalisasi.
8. Riwayat dan penyesuaian inventaris dapat ditelusuri.
9. Aplikasi berjalan offline pada Windows.
10. Pengguna memperoleh panduan operasional.

------------------------------------------------------------------------

# 10. Risiko Proyek dan Mitigasi

  -----------------------------------------------------------------------
  Risiko                  Dampak                  Mitigasi
  ----------------------- ----------------------- -----------------------
  Database rusak          Kehilangan data         Backup berkala dan uji
                                                  restore

  Barcode tidak terbaca   Pemeriksaan/transaksi   Uji scanner dan
                          terhambat               sediakan input manual

  Transaksi tidak         Stok keliru             Transaksi atomik dan
  konsisten                                       constraint

  Salah menghitung denda  Ketidaksesuaian         Uji batas tanggal dan
                          administrasi            konfigurasi

  Buku pinjaman dianggap  Laporan opname salah    Pisahkan status
  hilang                                          sirkulasi dan hasil
                                                  opname

  Pemindaian ganda        Jumlah temuan keliru    Unique constraint dan
                                                  validasi sesi

  Perubahan database      Aplikasi gagal setelah  Migration dan backup
  merusak data lama       pembaruan               sebelum upgrade

  Aplikasi tidak berjalan Deployment gagal        Uji executable pada
  di komputer lain                                Windows bersih

  Komputer rusak          Data lokal hilang       Salinan backup pada
                                                  media eksternal
  -----------------------------------------------------------------------

------------------------------------------------------------------------

Risiko tambahan v1.1: barcode salah baca akibat layout keyboard (mitigasi: barcode numerik dan uji scanner); pelabelan fisik terlambat (mitigasi: jadwalkan sebelum opname pertama); backup pada drive yang sama (mitigasi: peringatan dan media eksternal); sirkulasi berjalan saat opname (mitigasi: cakupan rak dinamis).

# 11. Hasil dan Luaran Proyek

Luaran yang diharapkan:

## 11.1 Produk Perangkat Lunak

-   Aplikasi LMS Desktop untuk Windows.
-   Database SQLite.
-   Modul manajemen buku dan eksemplar.
-   Modul anggota.
-   Modul peminjaman dan pengembalian.
-   Modul denda.
-   Modul laporan.
-   Modul backup dan restore.
-   Modul stok opname tahunan.
-   Modul impor Excel dan cetak label.
-   Modul petugas dan log aktivitas.

## 11.2 Dokumen Teknis

-   Dokumen SRS.
-   Dokumen desain database.
-   Dokumentasi arsitektur.
-   Dokumentasi instalasi.
-   Dokumentasi backup dan restore.
-   Dokumentasi pengujian.
-   Panduan pengguna.

## 11.3 Berkas Distribusi

-   Executable aplikasi (`.exe`).
-   Folder aset yang diperlukan.
-   Panduan penggunaan.
-   Template atau contoh label barcode.
-   Database awal yang telah diinisialisasi.
-   Paket dependensi yang diperlukan jika distribusi tidak menggunakan
    executable tunggal.

------------------------------------------------------------------------

# 12. Pemeliharaan dan Pengembangan Lanjutan

Setelah versi pertama digunakan, beberapa pengembangan dapat
dipertimbangkan tanpa menjadi bagian wajib dari versi awal:

1.  Kartu anggota dengan barcode.
3.  Pengelolaan kategori dan klasifikasi yang lebih lengkap.
4.  Riwayat kondisi fisik buku.
5.  Pengelolaan pengadaan dan penghapusan koleksi.
6.  Dashboard tren koleksi.
7.  Pencarian katalog yang lebih canggih.
9.  Multi-user dan sinkronisasi jaringan melalui arsitektur baru.
10. Integrasi perangkat RFID jika kebutuhan dan anggaran memungkinkan.

Pengembangan lanjutan harus mempertahankan data historis dan menggunakan
mekanisme migration.

------------------------------------------------------------------------

# 13. Asumsi dan Hal yang Perlu Ditetapkan

Proposal ini menggunakan beberapa asumsi awal yang perlu dikonfirmasi
sebelum implementasi:

  -----------------------------------------------------------------------
  Aspek                   Asumsi awal             Keputusan yang perlu
                                                  dikonfirmasi
  ----------------------- ----------------------- -----------------------
  Pengguna                Satu komputer Windows   Apakah satu atau
                                                  beberapa akun petugas?

  Anggota                 Memiliki nomor anggota  Format nomor anggota
                          unik                    

  Durasi pinjam           Contoh 7 hari           Durasi sebenarnya

  Denda                   Contoh Rp1.000/hari     Tarif sebenarnya

  Batas pinjam            Dapat dikonfigurasi     Maksimal eksemplar per
                                                  anggota

  Barcode                 Code 128                Apakah barcode dibuat
                                                  dari nol atau memakai
                                                  kode inventaris yang
                                                  sudah ada?

  Stok opname             Tahunan                 Bulan/periode
                                                  pelaksanaan

  Kondisi buku            Baik hingga tidak layak Standar klasifikasi
                          pakai                   kerusakan

  Backup                  Lokal dan media         Frekuensi dan lokasi
                          eksternal               penyimpanan

  Laporan                 Excel dan PDF           Format kop, logo, dan
                                                  tanda tangan
  -----------------------------------------------------------------------

Parameter tersebut sebaiknya diselesaikan pada fase analisis kebutuhan
sebelum implementasi modul terkait.

------------------------------------------------------------------------

## 13.1 Keputusan Ditetapkan pada v1.1

| Aspek | Keputusan |
|---|---|
| Barcode | Numerik 8 digit, Code 128, dibuat dari nol atau diimpor |
| Hashing password | PBKDF2-HMAC-SHA256 (`hashlib`) |
| Lokasi data | `%LOCALAPPDATA%\Libris\` untuk satu akun Windows |
| Opname dan sirkulasi | Sirkulasi tetap berjalan; cakupan rak dinamis |
| Grafik | Canvas CustomTkinter, tanpa Matplotlib |

# 14. Penutup

Pengembangan Library Management System Desktop diharapkan dapat
menyediakan sarana pengelolaan perpustakaan yang terintegrasi, sederhana
dalam operasional, dan dapat berjalan tanpa ketergantungan pada server
maupun koneksi internet.

Penggunaan Python, CustomTkinter, dan SQLite dipilih untuk membangun
aplikasi desktop yang ringan dan mudah dipelihara pada lingkungan satu
komputer Windows. Pemisahan arsitektur ke dalam lapisan antarmuka,
service, repository, dan database dimaksudkan agar aplikasi dapat
dikembangkan secara bertahap tanpa mencampuradukkan aturan bisnis dengan
tampilan.

Cakupan sistem tidak hanya berorientasi pada pencatatan peminjaman dan
pengembalian. Pengelolaan eksemplar berbasis barcode, pelaporan,
pencadangan data, dan stok opname tahunan menjadikan aplikasi ini
sebagai sistem yang juga mendukung pengendalian inventaris.

Dengan pelaksanaan pengembangan secara bertahap, pengujian yang memadai,
serta prosedur backup dan pemulihan yang teruji, aplikasi ini diharapkan
dapat menjadi perangkat operasional perpustakaan yang andal dan
berkelanjutan.

------------------------------------------------------------------------

# Lampiran A. Daftar Kebutuhan Fungsional

  Kode    Kebutuhan
  ------- -------------------------------------
  FR-01   Autentikasi pengguna
  FR-02   Dashboard
  FR-03   Manajemen bibliografi dan eksemplar
  FR-04   Manajemen anggota
  FR-05   Peminjaman
  FR-06   Pengembalian
  FR-07   Perhitungan dan pencatatan denda
  FR-08   Laporan Excel dan PDF
  FR-09   Backup dan restore
  FR-10   Stok opname tahunan
  FR-11   Impor data dan cetak label barcode

# Lampiran B. Daftar Teknologi

  Teknologi        Peran
  ---------------- ------------------------------------
  Python           Bahasa pemrograman
  CustomTkinter    GUI desktop
  Tkinter/ttk      Komponen tabel dan widget tambahan
  SQLite           Database lokal
  sqlite3          Akses database
  Canvas CTk       Grafik dashboard
  OpenPyXL         Ekspor Excel
  ReportLab        Ekspor PDF
  python-barcode   Pembuatan barcode
  PyInstaller      Packaging executable
  pytest           Pengujian
  Git              Version control
  VS Code          IDE

# Lampiran C. Prinsip Implementasi yang Tidak Boleh Dilanggar

1.  Tidak menggunakan XAMPP.
2.  Tidak membutuhkan Apache, PHP, atau MySQL Server.
3.  Fungsi inti harus berjalan tanpa internet.
4.  Database produksi tidak ditempatkan di direktori instalasi aplikasi.
5.  Data bibliografi harus dibedakan dari data eksemplar.
6.  Barcode harus unik untuk setiap eksemplar.
7.  Status sirkulasi harus dibedakan dari kondisi fisik buku.
8.  Peminjaman dan pengembalian harus menggunakan transaksi database.
9.  Data historis tidak dihapus sembarangan.
10. Snapshot stok opname harus dipertahankan sebagai bukti kondisi
    inventaris pada periode pemeriksaan.
11. Buku yang sedang dipinjam tidak otomatis dinyatakan hilang.
12. Penyesuaian hasil stok opname harus melalui persetujuan dan audit
    trail.
13. Backup dan restore wajib diuji, bukan hanya disediakan sebagai
    tombol.
14. Setiap perubahan skema database harus dikelola melalui migration.
15. Semua modul harus memiliki pengujian sesuai aturan bisnisnya.
16. Barcode eksemplar numerik 8 digit dan dipisahkan dari kode inventaris.
17. Denda yang masih berjalan tidak dapat dibayar sebelum ditetapkan saat pengembalian.
18. Sirkulasi selama opname mengikuti aturan cakupan rak dinamis.
19. Data berriwayat diarsipkan, bukan dihapus permanen; hapus permanen hanya untuk data tanpa riwayat.
20. Setiap edit, arsip, hapus, dan pemulihan tercatat dengan nilai lama dan baru.

------------------------------------------------------------------------

**Akhir dokumen proposal**\
**Library Management System (LMS) Desktop --- Versi 1.2**
