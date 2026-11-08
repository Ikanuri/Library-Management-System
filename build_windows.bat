@echo off
REM Bangun Libris.exe dengan PyInstaller (jalankan di Windows dari folder proyek).
python -m pip install -r requirements.txt || exit /b 1
python -m PyInstaller --noconfirm --windowed --name Libris --collect-all customtkinter --collect-all barcode main.py
echo Selesai: dist\Libris\Libris.exe
