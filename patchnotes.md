# Patch Notes

## 2026-11-08 — Pemolesan tampilan
### Baru
- Tema gelap bawaan dengan aksen cyan sesuai prototipe, plus tema terang (Pengaturan → Tampilan).
- Dialog dan notifikasi modern: konfirmasi Enter/Esc, pesan sukses sebagai toast di pojok, kesalahan form tampil di dalam dialog.
- Sidebar berkelompok dengan ikon dan penanda halaman aktif; layar login baru.
- Peminjaman, Pengembalian, dan Stok Opname: kolom scan besar yang selalu terfokus dan strip hasil hijau/merah/kuning besar; daftar pinjam sementara bisa dihapus per item.
- Tabel lebih rapi: baris selang-seling, status berpenanda warna, urut dengan klik judul kolom, pesan "Belum ada data".
### Diperbaiki
- Teks kolom pencarian (placeholder) kini tampil; label sumbu grafik dashboard tidak ganda.
### Masalah diketahui
- Tampilan belum diuji manual di Windows (skala 125/150 %, scanner, Segoe UI). Lihat `docs/UI_Checklist_Windows.md`.
- Navigasi sidebar dengan keyboard belum ada.

## 2026-11-08 — Libris 0.1.0 (rilis awal, belum diuji di Windows)
### Baru
- Login Administrator/Petugas (password PBKDF2, penguncian setelah 5 kali gagal) dan log aktivitas.
- Koleksi buku & eksemplar: barcode 8 digit, edit, arsip, pulihkan, hapus permanen (aturan riwayat), operasi massal.
- Anggota, peminjaman multi-buku atomik, pengembalian sebagian, denda dengan siklus berjalan/ditetapkan/dibayar.
- Laporan Excel & PDF (11 laporan), dashboard dengan grafik canvas.
- Backup/restore aman, impor Excel dengan validasi uji coba, label barcode PDF.
- Stok opname tahunan: snapshot, cakupan rak dinamis, temuan ekstra, rekonsiliasi, finalisasi terkunci.
### Masalah diketahui
- Belum diuji di Windows/scanner nyata; `.exe` belum dibangun; lihat `handoff.md` untuk daftar lengkap.

## 2026-11-08 — Inisialisasi repositori
- Menambahkan dokumen perancangan Libris v1.2 (proposal + prototipe UI) ke `docs/`.
- Menambahkan `handoff.md` (serah terima), `changelog.md` (riwayat teknis), dan berkas ini (ringkasan bagi pengguna).
- Belum ada kode aplikasi; tidak ada perubahan perilaku.

## Template catatan berikutnya
```
## <tanggal> — <judul rilis/versi>
### Baru
### Diperbaiki
### Diubah
### Masalah diketahui
```
