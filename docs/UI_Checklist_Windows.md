# Daftar Periksa UI di Windows (manual)

> **Status: BELUM DIUJI.** Semua butir di bawah belum pernah dijalankan oleh manusia di Windows.
> Tangkapan layar di `docs/screenshots/` dibuat di Linux (xvfb, font cadangan Inter/DejaVu), bukan Windows;
> bentuk huruf, ikon, dan ukuran akan berbeda di Segoe UI. Centang hanya setelah diperiksa sendiri.

Uji dengan build dari GitHub Actions (artifact `Libris-windows`) atau `python main.py`.

## Skala layar dan jendela
- [ ] 100 %: tidak ada teks terpotong pada sidebar, header halaman, dan tombol toolbar.
- [ ] 125 %: tinggi baris tabel proporsional (tabel memakai faktor `theme.dpi_factor`); huruf tabel terbaca.
- [ ] 150 %: sidebar, dialog, dan kartu statistik tidak saling menimpa; tidak perlu scroll horizontal pada tabel.
- [ ] Ukuran jendela minimum 1100×680: semua halaman masih dapat dipakai; Pengaturan dapat di-scroll.
- [ ] Jendela dimaksimalkan: grafik dashboard menggambar ulang mengikuti lebar kartu.

## Scanner USB (HID)
- [ ] Halaman Peminjaman: kolom anggota/eksemplar otomatis terfokus saat halaman dibuka dan setelah tiap pemindaian.
- [ ] Pengembalian: setelah pemindaian, fokus kembali ke kolom scan; strip umpan balik hijau/merah/kuning sesuai hasil.
- [ ] Stok Opname: pemindaian beruntun cepat tidak melewatkan atau menggandakan kode; duplikat menampilkan strip kuning.
- [ ] Scanner yang mengirim Enter di akhir kode bekerja tanpa ketukan tambahan.
- [ ] Dialog yang muncul di tengah pemindaian tidak "menelan" karakter scanner.

## Keyboard saja
- [ ] Tab/Shift+Tab bergerak logis pada form dan dialog; Enter menyimpan, Esc menutup `FormDialog`.
- [ ] Dialog info/konfirmasi: Enter = tombol utama, Esc = batal; fokus awal pada tombol utama.
- [ ] Layar login: Enter dari kolom mana pun mengirim.
- [ ] Menu sidebar dapat dipakai dengan mouse; **catatan:** navigasi sidebar dengan keyboard belum diimplementasikan.

## Tampilan
- [ ] Ikon sidebar (◫ ▤ ♙ ↗ ↙ ◈ ▦ ↑ ▥ ↓ ☰ ⚙) tampil sebagai glyph, bukan kotak kosong, pada Segoe UI Symbol.
- [ ] Judul buku/anggota yang sangat panjang terpotong rapi dan tidak merusak tata letak.
- [ ] Kontras: teks MUTED/SOFT terbaca pada tema gelap dan terang (periksa pada monitor kantor yang redup).
- [ ] Tema Terang: sidebar, tabel, dialog, dan banner terbaca; ganti tema dari Pengaturan tidak membuat aplikasi macet.
- [ ] Status berwarna: baris Dipinjam/Perbaikan/Hilang/Belum ditemukan berwarna; Tersedia/Aktif berteks biasa (disengaja).
- [ ] Toast di pojok kanan bawah tidak menutupi tombol penting dan hilang sendiri.
- [ ] Dialog muncul di atas jendela utama pada layar kedua (multi-monitor) dan `grab_set` berhasil.

## Fungsi yang tidak boleh berubah
- [ ] Peminjaman → Pengembalian → Denda → Pembayaran berjalan seperti sebelum pemolesan.
- [ ] Opname: pemindaian, rekonsiliasi, finalisasi.
- [ ] Backup/Restore; impor Excel; label PDF.
