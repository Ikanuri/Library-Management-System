import re


def clean_isbn(isbn: str | None) -> str | None:
    if not isbn:
        return None
    s = re.sub(r"[\s-]", "", isbn).upper()
    return s or None


def isbn_valid(isbn: str | None) -> bool:
    s = clean_isbn(isbn)
    if s is None:
        return True  # opsional
    if re.fullmatch(r"\d{13}", s):
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s[:12]))
        return (10 - total % 10) % 10 == int(s[12])
    if re.fullmatch(r"\d{9}[\dX]", s):
        total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s))
        return total % 11 == 0
    return False
