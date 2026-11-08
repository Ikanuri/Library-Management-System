"""Skema database Libris (proposal v1.2 bagian 5.3). Dikelola lewat migrations.py."""

SCHEMA_V1 = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','staff')),
    is_active INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    entity TEXT NOT NULL,
    entity_id TEXT,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT
);
CREATE INDEX idx_audit_entity ON audit_logs(entity, entity_id);

CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    year INTEGER,
    category TEXT,
    description TEXT,
    shelf TEXT,
    cover_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    archived_at TEXT, archived_by INTEGER REFERENCES users(id), archived_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT, updated_by INTEGER REFERENCES users(id)
);
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);

CREATE TABLE book_copies (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    inventory_code TEXT NOT NULL UNIQUE,
    barcode TEXT NOT NULL UNIQUE CHECK (length(barcode)=8 AND barcode NOT GLOB '*[^0-9]*'),
    acquired_at TEXT,
    acquisition_source TEXT,
    shelf TEXT,
    circulation_status TEXT NOT NULL DEFAULT 'Tersedia'
        CHECK (circulation_status IN ('Tersedia','Dipinjam','Perbaikan','Hilang','Dihapusbukukan')),
    condition TEXT NOT NULL DEFAULT 'Baik'
        CHECK (condition IN ('Baik','Rusak ringan','Rusak sedang','Rusak berat','Tidak layak pakai')),
    archived_at TEXT, archived_by INTEGER REFERENCES users(id), archived_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT, updated_by INTEGER REFERENCES users(id)
);
CREATE INDEX idx_copies_book ON book_copies(book_id);

CREATE TABLE members (
    id INTEGER PRIMARY KEY,
    member_no TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    member_type TEXT NOT NULL DEFAULT 'Umum',
    address TEXT, phone TEXT, email TEXT,
    registered_at TEXT NOT NULL DEFAULT (date('now')),
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT
);
CREATE INDEX idx_members_name ON members(name);

CREATE TABLE loans (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    user_id INTEGER REFERENCES users(id),
    loan_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE loan_items (
    id INTEGER PRIMARY KEY,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    copy_id INTEGER NOT NULL REFERENCES book_copies(id) ON DELETE RESTRICT,
    returned_at TEXT,
    return_condition TEXT,
    fine_id INTEGER
);
CREATE INDEX idx_li_copy ON loan_items(copy_id);
CREATE INDEX idx_li_loan ON loan_items(loan_id);
CREATE UNIQUE INDEX uq_li_active_copy ON loan_items(copy_id) WHERE returned_at IS NULL;

CREATE TABLE fines (
    id INTEGER PRIMARY KEY,
    loan_item_id INTEGER NOT NULL UNIQUE REFERENCES loan_items(id),
    days_late INTEGER NOT NULL DEFAULT 0,
    rate INTEGER NOT NULL DEFAULT 0,
    amount INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT 'Keterlambatan',
    status TEXT NOT NULL DEFAULT 'Belum bayar' CHECK (status IN ('Belum bayar','Sebagian','Lunas')),
    assessed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE fine_payments (
    id INTEGER PRIMARY KEY,
    fine_id INTEGER NOT NULL REFERENCES fines(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    paid_at TEXT NOT NULL DEFAULT (datetime('now')),
    received_by INTEGER REFERENCES users(id)
);

CREATE TABLE stock_opname_sessions (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'Berjalan'
        CHECK (status IN ('Berjalan','Pemeriksaan ulang','Final')),
    created_by INTEGER REFERENCES users(id),
    finalized_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    finalized_at TEXT,
    notes TEXT
);
CREATE UNIQUE INDEX uq_opname_active_year ON stock_opname_sessions(year) WHERE status <> 'Final';
CREATE TABLE stock_opname_items (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES stock_opname_sessions(id),
    copy_id INTEGER REFERENCES book_copies(id) ON DELETE RESTRICT,
    barcode_snapshot TEXT NOT NULL,
    book_title_snapshot TEXT,
    inventory_code_snapshot TEXT,
    location_snapshot TEXT,
    circulation_status_snapshot TEXT,
    result TEXT NOT NULL DEFAULT 'Belum diperiksa'
        CHECK (result IN ('Belum diperiksa','Ditemukan','Belum ditemukan','Hilang terkonfirmasi',
                          'Ditemukan ekstra','Dipinjam')),
    physical_condition TEXT,
    actual_location TEXT,
    notes TEXT,
    inspected_by INTEGER REFERENCES users(id),
    inspected_at TEXT,
    verification_status TEXT NOT NULL DEFAULT 'tidak' CHECK (verification_status IN ('ya','tidak')),
    UNIQUE (session_id, copy_id),
    UNIQUE (session_id, barcode_snapshot)
);
CREATE TABLE stock_opname_adjustments (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES stock_opname_sessions(id),
    copy_id INTEGER REFERENCES book_copies(id),
    old_status TEXT, new_status TEXT,
    reason TEXT NOT NULL,
    approved_by INTEGER REFERENCES users(id),
    adjusted_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE stock_opname_scans (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES stock_opname_sessions(id),
    barcode TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    scanned_by INTEGER REFERENCES users(id),
    outcome TEXT NOT NULL
);

CREATE TABLE backup_history (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    kind TEXT NOT NULL,
    size_bytes INTEGER
);
"""

DEFAULT_SETTINGS = {
    "loan_days": "7",
    "fine_rate": "1000",
    "fine_cap": "0",              # 0 = tanpa batas
    "grace_days": "0",
    "max_loans_per_member": "3",
    "lost_policy": "Ditentukan petugas",
    "backup_retention": "10",
    "backup_dir": "",
    "library_name": "Perpustakaan",
}
