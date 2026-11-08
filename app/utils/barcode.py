"""Utilitas barcode: normalisasi input scanner, pembuatan kode, gambar Code 128."""
import io
import re
import secrets


def normalize(code: str) -> str:
    return (code or "").strip().upper()


def is_valid_barcode(code: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", code or ""))


def generate_barcode(exists) -> str:
    """Buat barcode numerik 8 digit unik. `exists(code)->bool` memeriksa duplikasi."""
    for _ in range(1000):
        code = f"{secrets.randbelow(10**8):08d}"
        if not exists(code):
            return code
    raise RuntimeError("Gagal membuat barcode unik")


def code128_png(code: str) -> bytes:
    import barcode
    from barcode.writer import ImageWriter
    buf = io.BytesIO()
    barcode.get("code128", code, writer=ImageWriter()).write(
        buf, {"write_text": False, "module_height": 12.0, "quiet_zone": 2.0})
    return buf.getvalue()
