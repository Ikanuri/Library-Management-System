"""Komponen bersama: tabel, dialog form, kartu statistik, kolom scan."""
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from app.services.base import ServiceError
from . import theme


def guard(fn):
    """Dekorator callback UI: tampilkan ServiceError sebagai pesan, bukan crash."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except ServiceError as e:
            messagebox.showwarning("Libris", str(e))
        except Exception as e:  # kesalahan tak terduga
            messagebox.showerror("Libris", f"Terjadi kesalahan: {e}")
    return wrapper


def info(msg):
    messagebox.showinfo("Libris", msg)


def confirm(msg):
    return messagebox.askyesno("Libris", msg)


class Card(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=theme.PANEL, corner_radius=10, **kw)


class StatCard(Card):
    def __init__(self, master, label, value="0", color=theme.ACCENT):
        super().__init__(master)
        self.value = ctk.CTkLabel(self, text=str(value), font=theme.font(24, True), text_color=color)
        self.value.pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(self, text=label, font=theme.font(12), text_color=theme.MUTED).pack(anchor="w", padx=14, pady=(0, 10))

    def set(self, v):
        self.value.configure(text=str(v))


class DataTable(ctk.CTkFrame):
    """Tabel Treeview dengan warna status per baris. columns=[(key,judul,lebar)]."""

    def __init__(self, master, columns, height=14, status_key=None, multi=False, on_double=None):
        super().__init__(master, fg_color="transparent")
        self.columns, self.status_key, self.rows = columns, status_key, {}
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Libris.Treeview", rowheight=26, font=("Segoe UI", 10), background="white",
                        fieldbackground="white", borderwidth=0)
        style.configure("Libris.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=theme.PANEL2)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings", height=height,
                                 style="Libris.Treeview", selectmode="extended" if multi else "browse")
        for key, title, width in columns:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for st, col in theme.STATUS_COLORS.items():
            self.tree.tag_configure(st, foreground=col)
        self.tree.tag_configure("late", foreground=theme.DANGER)
        if on_double:
            self.tree.bind("<Double-1>", lambda e: on_double())

    def load(self, rows, tag=None):
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for i, r in enumerate(rows):
            iid = str(r.get("id", i)) if isinstance(r, dict) else str(i)
            if iid in self.rows:
                iid = f"{iid}_{i}"
            self.rows[iid] = r
            vals = [("" if r.get(k) is None else r.get(k)) for k, _, _ in self.columns]
            tags = []
            if self.status_key and r.get(self.status_key) in theme.STATUS_COLORS:
                tags.append(r[self.status_key])
            if tag and tag(r):
                tags.append(tag(r))
            self.tree.insert("", "end", iid=iid, values=vals, tags=tags)

    def selected(self):
        return [self.rows[i] for i in self.tree.selection() if i in self.rows]

    def selected_one(self):
        s = self.selected()
        if not s:
            messagebox.showinfo("Libris", "Pilih satu baris terlebih dahulu.")
            return None
        return s[0]


class Toolbar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

    def button(self, text, cmd, danger=False, secondary=False):
        fg = theme.DANGER if danger else (theme.PANEL2 if secondary else theme.ACCENT)
        b = ctk.CTkButton(self, text=text, command=guard(cmd), width=0, fg_color=fg,
                          text_color=theme.TEXT if secondary else "white",
                          hover_color=theme.PANEL3 if secondary else (theme.ACCENT_HOVER if not danger else theme.DANGER_HOVER))
        b.pack(side="left", padx=(0, 6))
        return b

    def search(self, on_change, placeholder="Cari..."):
        var = tk.StringVar()
        e = ctk.CTkEntry(self, textvariable=var, placeholder_text=placeholder, width=260)
        e.pack(side="left", padx=(0, 8))
        var.trace_add("write", lambda *_: on_change())
        return var

    def combo(self, values, on_change, default=None, width=140):
        var = tk.StringVar(value=default or values[0])
        ctk.CTkOptionMenu(self, values=values, variable=var, width=width, command=lambda _: on_change()).pack(side="left", padx=(0, 8))
        return var


class FormDialog(ctk.CTkToplevel):
    """fields: [(key,label,tipe,opsi)] tipe: entry|combo|text|password."""

    def __init__(self, master, title, fields, initial=None, on_save=None, width=440):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=theme.BG)
        self.transient(master.winfo_toplevel())
        self.on_save, self.vars, self.widgets = on_save, {}, {}
        initial = initial or {}
        body = ctk.CTkScrollableFrame(self, fg_color=theme.BG, width=width, height=min(70 * len(fields) + 20, 520))
        body.pack(fill="both", expand=True, padx=12, pady=12)
        for key, label, kind, *opt in fields:
            ctk.CTkLabel(body, text=label, font=theme.font(12), text_color=theme.MUTED).pack(anchor="w", pady=(6, 0))
            val = initial.get(key)
            if kind == "combo":
                v = tk.StringVar(value=str(val if val not in (None, "") else (opt[0][0] if opt and opt[0] else "")))
                w = ctk.CTkOptionMenu(body, values=list(opt[0]), variable=v)
            elif kind == "text":
                w = ctk.CTkTextbox(body, height=70)
                w.insert("1.0", "" if val is None else str(val))
                v = None
            else:
                v = tk.StringVar(value="" if val is None else str(val))
                w = ctk.CTkEntry(body, textvariable=v, show="*" if kind == "password" else "")
            w.pack(fill="x")
            self.vars[key], self.widgets[key] = v, w
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(bar, text="Simpan", command=self._save, fg_color=theme.ACCENT).pack(side="right")
        ctk.CTkButton(bar, text="Batal", command=self.destroy, fg_color=theme.PANEL2, text_color=theme.TEXT,
                      hover_color=theme.PANEL3).pack(side="right", padx=6)
        self.after(120, self.grab_set)

    def values(self):
        out = {}
        for k, v in self.vars.items():
            out[k] = v.get().strip() if v is not None else self.widgets[k].get("1.0", "end").strip()
        return out

    def _save(self):
        try:
            self.on_save(self.values())
        except ServiceError as e:
            messagebox.showwarning("Libris", str(e), parent=self)
            return
        self.destroy()


class ScanEntry(ctk.CTkEntry):
    """Kolom scan: Enter memanggil callback lalu mengosongkan dan memfokuskan ulang."""

    def __init__(self, master, on_scan, placeholder="Pindai barcode lalu Enter", **kw):
        super().__init__(master, placeholder_text=placeholder, **kw)
        self.on_scan = guard(on_scan)
        self.bind("<Return>", self._enter)

    def _enter(self, _):
        code = self.get().strip()
        if code:
            self.on_scan(code)
        self.delete(0, "end")
        self.focus_set()


def ask_save(master, **kw):
    from tkinter import filedialog
    return filedialog.asksaveasfilename(parent=master, **kw)
