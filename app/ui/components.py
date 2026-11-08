"""Komponen bersama: dialog, toast, kartu, tabel, toolbar, form, kolom scan, strip umpan balik.

API publik dipertahankan: info, confirm, guard, DataTable, Toolbar, FormDialog, ScanEntry, Card, StatCard.
Hanya modul ini yang boleh memakai tkinter.messagebox / simpledialog (kini tidak dipakai sama sekali).
"""
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from app.services.base import ServiceError
from . import theme


# ---------------------------------------------------------------- util gaya
def _btn_colors(variant):
    """(fg, hover, teks, border) untuk varian tombol: primary|secondary|danger|ghost."""
    if variant == "primary":
        return theme.ACCENT, theme.ACCENT_HOVER, theme.ON_ACCENT, theme.ACCENT
    if variant == "danger":
        return theme.DANGER, theme.DANGER_HOVER, theme.ON_DANGER, theme.DANGER
    if variant == "ghost":
        return "transparent", theme.PANEL2, theme.SOFT, "transparent"
    return theme.PANEL2, theme.PANEL3, theme.TEXT, theme.LINE      # secondary


def make_button(master, text, command, variant="primary", width=0, height=None, **kw):
    fg, hover, txt, border = _btn_colors(variant)
    return ctk.CTkButton(master, text=text, command=command, width=width, height=height or theme.H_CTRL,
                         fg_color=fg, hover_color=hover, text_color=txt, border_width=1 if variant != "ghost" else 0,
                         border_color=border, corner_radius=theme.R_BTN, font=theme.font(theme.FS_CAPTION, True), **kw)


def style_entry(master, height=None, **kw):
    return ctk.CTkEntry(master, height=height or theme.H_CTRL, corner_radius=theme.R_INPUT, fg_color=theme.INPUT,
                        border_color=theme.LINE, text_color=theme.TEXT, placeholder_text_color=theme.MUTED,
                        font=theme.font(theme.FS_BODY), **kw)


def style_option(master, values, variable, width=140, command=None):
    return ctk.CTkOptionMenu(master, values=list(values), variable=variable, width=width, height=theme.H_CTRL,
                             corner_radius=theme.R_INPUT, fg_color=theme.INPUT, button_color=theme.PANEL2,
                             button_hover_color=theme.PANEL3, text_color=theme.TEXT, dropdown_fg_color=theme.PANEL2,
                             dropdown_text_color=theme.TEXT, dropdown_hover_color=theme.PANEL3,
                             font=theme.font(theme.FS_CAPTION), dropdown_font=theme.font(theme.FS_CAPTION),
                             command=command)


def section_label(master, text):
    return ctk.CTkLabel(master, text=text, font=theme.font(theme.FS_SECTION, True), text_color=theme.TEXT)


def caption(master, text="", **kw):
    kw.setdefault("text_color", theme.MUTED)
    return ctk.CTkLabel(master, text=text, font=theme.font(theme.FS_CAPTION), **kw)


# ---------------------------------------------------------------- dialog modal
def _parent_window():
    root = tk._default_root
    if root is None:
        return None
    try:
        f = root.focus_get()
        top = f.winfo_toplevel() if f is not None else root
        return top if top.winfo_exists() else root
    except Exception:
        return root


class Dialog(ctk.CTkToplevel):
    """Dialog modal bergaya. Enter = tombol utama, Esc = batal. `Dialog.current` dipakai pengujian."""
    current = None
    ICONS = {"info": ("i", "blue"), "warn": ("!", "amber"), "error": ("×", "red"), "ask": ("?", "blue"), "ok": ("✓", "green")}

    def __init__(self, title, message, kind="info", buttons=(("OK", True, "primary"),), cancel_value=None,
                 default=0, parent=None, width=440):
        parent = parent or _parent_window()
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=theme.PANEL)
        self.resizable(False, False)
        self.result, self._cancel, self._buttons, self._default = cancel_value, cancel_value, [], default
        if parent is not None:
            self.transient(parent.winfo_toplevel())
        glyph, bk = self.ICONS.get(kind, self.ICONS["info"])
        fg, bg, line = theme.badge_style(bk)[0], theme.badge_style(bk)[1], theme.badge_style(bk)[2]
        body = ctk.CTkFrame(self, fg_color="transparent"); body.pack(fill="both", expand=True, padx=theme.PAD, pady=(theme.PAD, theme.SP3))
        icon = ctk.CTkFrame(body, width=36, height=36, corner_radius=18, fg_color=bg, border_width=1, border_color=line)
        icon.pack(side="left", anchor="n"); icon.pack_propagate(False)
        ctk.CTkLabel(icon, text=glyph, text_color=fg, font=theme.font(16, True)).pack(expand=True)
        txt = ctk.CTkFrame(body, fg_color="transparent"); txt.pack(side="left", fill="both", expand=True, padx=(theme.SP4, 0))
        ctk.CTkLabel(txt, text=title, font=theme.font(theme.FS_SECTION, True), text_color=theme.TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text=message, font=theme.font(theme.FS_BODY), text_color=theme.SOFT, anchor="w",
                     justify="left", wraplength=width - 120).pack(anchor="w", pady=(theme.SP2, 0))
        bar = ctk.CTkFrame(self, fg_color="transparent"); bar.pack(fill="x", padx=theme.PAD, pady=(theme.SP3, theme.PAD))
        for i, (label, value, variant) in enumerate(reversed(list(buttons))):
            b = make_button(bar, label, lambda v=value: self._close(v), variant, width=96)
            b.pack(side="right", padx=(theme.SP2, 0))
            self._buttons.append((value, b))
        self._buttons.reverse()
        self.bind("<Return>", lambda e: self.invoke(self._default))
        self.bind("<Escape>", lambda e: self._close(self._cancel))
        self.protocol("WM_DELETE_WINDOW", lambda: self._close(self._cancel))
        self.update_idletasks()
        self._center(parent, width)
        Dialog.current = self
        self.after(120, self._grab)

    def _center(self, parent, width):
        self.update_idletasks()
        w, h = max(width, self.winfo_reqwidth()), self.winfo_reqheight()
        if parent is not None:
            x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - h) // 3
        else:
            x, y = (self.winfo_screenwidth() - w) // 2, (self.winfo_screenheight() - h) // 3
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def _grab(self):
        try:
            self.grab_set(); self.focus_force()
            if self._buttons:
                self._buttons[self._default][1].focus_set()
        except tk.TclError:
            pass

    def invoke(self, index=None):
        self._close(self._buttons[self._default if index is None else index][0])

    def _close(self, value):
        self.result = value
        if Dialog.current is self:
            Dialog.current = None
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def show(self):
        self.wait_window(self)
        return self.result


def info(msg, title="Libris"):
    Dialog(title, msg, "info").show()


def warn(msg, title="Perhatian"):
    Dialog(title, msg, "warn").show()


def error(msg, title="Terjadi kesalahan"):
    Dialog(title, msg, "error").show()


def confirm(msg, title="Konfirmasi", yes="Ya", no="Batal", danger=False) -> bool:
    return bool(Dialog(title, msg, "ask", ((no, False, "secondary"), (yes, True, "danger" if danger else "primary")),
                       cancel_value=False, default=1).show())


def guard(fn):
    """Dekorator callback UI: ServiceError -> dialog peringatan; kesalahan tak terduga -> dialog error."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except ServiceError as e:
            warn(str(e))
        except Exception as e:
            error(f"{type(e).__name__}: {e}")
    return wrapper


def ask_int(title, label, initial=0, minvalue=None, parent=None):
    """Dialog angka bergaya; mengembalikan int atau None bila dibatalkan. Validasi inline."""
    out = {"v": None}
    dlg = FormDialog(parent or _parent_window(), title, [("n", label, "entry")], {"n": initial}, None, width=360)

    def save(vals):
        try:
            n = int(vals["n"].replace(".", ""))
        except ValueError:
            raise ServiceError("Masukkan bilangan bulat.")
        if minvalue is not None and n < minvalue:
            raise ServiceError(f"Nilai minimal {minvalue}.")
        out["v"] = n
    dlg.on_save = save
    dlg.wait_window(dlg)
    return out["v"]


# ---------------------------------------------------------------- toast
def toast(master, message, kind="ok", duration=2500):
    """Kartu kecil di pojok kanan bawah jendela, hilang sendiri. Untuk sukses non-kritis."""
    top = (master or tk._default_root).winfo_toplevel()
    old = getattr(top, "_libris_toast", None)
    if old is not None:
        try: old.destroy()
        except tk.TclError: pass
    fg, bg, line = theme.badge_style({"ok": "green", "warn": "amber", "error": "red"}.get(kind, "blue"))
    t = ctk.CTkFrame(top, fg_color=bg, border_width=1, border_color=line, corner_radius=theme.R_BTN)
    ctk.CTkLabel(t, text=message, text_color=fg, font=theme.font(theme.FS_CAPTION, True), wraplength=360,
                 justify="left").pack(padx=theme.SP4, pady=theme.SP3)
    t.place(relx=1.0, rely=1.0, x=-theme.PAD, y=-theme.PAD, anchor="se"); t.lift()
    top._libris_toast = t
    def hide():
        try: t.destroy()
        except tk.TclError: pass
    t.after(duration, hide)
    return t


# ---------------------------------------------------------------- kartu
class Card(ctk.CTkFrame):
    """Latar PANEL, garis 1 px LINE, radius 14. `title` menambahkan judul seksi di dalam kartu."""

    def __init__(self, master, title=None, subtitle=None, **kw):
        kw.setdefault("fg_color", theme.PANEL)
        super().__init__(master, border_width=1, border_color=theme.LINE, corner_radius=theme.R_CARD, **kw)
        if title:
            head = ctk.CTkFrame(self, fg_color="transparent"); head.pack(fill="x", padx=theme.PAD_CARD + 2, pady=(theme.PAD_CARD, 0))
            section_label(head, title).pack(anchor="w")
            if subtitle:
                caption(head, subtitle).pack(anchor="w")


class StatCard(Card):
    def __init__(self, master, label, value="0", color=None, small=False):
        super().__init__(master)
        color = color or theme.ACCENT
        bar = ctk.CTkFrame(self, height=3, width=28, corner_radius=2, fg_color=color)
        bar.pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(theme.PAD_CARD, 0))
        ctk.CTkLabel(self, text=label.upper(), font=theme.font(theme.FS_TH - 1, True), text_color=theme.MUTED).pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(theme.SP2, 0))
        self.value = ctk.CTkLabel(self, text=str(value), font=theme.font(theme.FS_STAT - (8 if small else 0), True), text_color=color)
        self.value.pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(0, theme.PAD_CARD))

    def set(self, v):
        self.value.configure(text=str(v))


class FeedbackStrip(ctk.CTkFrame):
    """Strip umpan balik besar untuk alur scanner; bertahan sampai pemindaian berikutnya."""

    def __init__(self, master):
        super().__init__(master, corner_radius=theme.R_CARD, border_width=1)
        self.title = ctk.CTkLabel(self, text="", font=theme.font(theme.FS_SECTION, True), anchor="w")
        self.detail = ctk.CTkLabel(self, text="", font=theme.font(theme.FS_BODY), anchor="w", justify="left", wraplength=900)
        self.title.pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(theme.SP3, 0))
        self.detail.pack(anchor="w", padx=theme.PAD_CARD + 2, pady=(0, theme.SP3))
        self.clear()

    def _paint(self, kind, title, detail=""):
        fg, bg, line = theme.badge_style(kind)
        self.configure(fg_color=bg, border_color=line)
        self.title.configure(text=title, text_color=fg)
        self.detail.configure(text=detail, text_color=fg)
        self.kind = kind

    def ok(self, title, detail=""):
        self._paint("green", "✓  " + title, detail)

    def fail(self, title, detail=""):
        self._paint("red", "×  " + title, detail)

    def warn(self, title, detail=""):
        self._paint("amber", "!  " + title, detail)

    def note(self, title, detail=""):
        self._paint("blue", title, detail)

    def clear(self):
        self.kind = "gray"
        fg, bg, line = theme.badge_style("gray")
        self.configure(fg_color=theme.PANEL, border_color=theme.LINE)
        self.title.configure(text="Siap memindai", text_color=theme.MUTED)
        self.detail.configure(text="Hasil pemindaian terakhir akan tampil di sini.", text_color=theme.MUTED)


# ---------------------------------------------------------------- tabel
class DataTable(ctk.CTkFrame):
    """Treeview bergaya. columns=[(key,judul,lebar)]. Status tampil sebagai '● Teks' berwarna."""

    def __init__(self, master, columns, height=14, status_key=None, multi=False, on_double=None):
        super().__init__(master, fg_color=theme.PANEL, border_width=1, border_color=theme.LINE, corner_radius=theme.R_CARD)
        self.columns, self.status_key, self.rows, self._order, self._sort, self._tagfn = columns, status_key, {}, [], (None, False), None
        self.empty = ctk.CTkLabel(self, text="Belum ada data", text_color=theme.MUTED, font=theme.font(theme.FS_BODY))
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings", height=height,
                                 style="Libris.Treeview", selectmode="extended" if multi else "browse")
        for key, title, width in columns:
            self.tree.heading(key, text=title.upper(), anchor="w", command=lambda k=key: self.sort_by(k))
            self.tree.column(key, width=width, anchor="w")
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Libris.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
        sb.pack(side="right", fill="y", padx=(0, 1), pady=1)
        self.tree.tag_configure("odd", background=theme.PANEL)
        self.tree.tag_configure("even", background=theme.PANEL2)
        for st, col in theme.STATUS_COLORS.items():
            self.tree.tag_configure(st, foreground=col)
        self.tree.tag_configure("late", foreground=theme.DANGER)
        if on_double:
            self.tree.bind("<Double-1>", lambda e: on_double())

    def _cell(self, key, r):
        v = r.get(key)
        v = "" if v is None else v
        return f"● {v}" if key == self.status_key and v != "" else v

    def load(self, rows, tag=None):
        self.tree.delete(*self.tree.get_children())
        self.rows, self._order = {}, []
        for i, r in enumerate(rows):
            iid = str(r.get("id", i)) if isinstance(r, dict) else str(i)
            if iid in self.rows:
                iid = f"{iid}_{i}"
            self.rows[iid] = r
            self._order.append(iid)
        self._sort, self._tagfn = (None, False), tag
        self._fill()

    def _fill(self):
        self.tree.delete(*self.tree.get_children())
        for n, iid in enumerate(self._order):
            r = self.rows[iid]
            tags = ["even" if n % 2 else "odd"]
            if self.status_key and r.get(self.status_key) in theme.STATUS_COLORS:
                tags.append(r[self.status_key])
            extra = self._tagfn(r) if self._tagfn else None
            if extra:
                tags.append(extra)
            self.tree.insert("", "end", iid=iid, values=[self._cell(k, r) for k, _, _ in self.columns], tags=tags)
        if self.rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.5, anchor="center")

    def sort_by(self, key):
        col, rev = self._sort
        rev = (not rev) if col == key else False
        def k(iid):
            v = self.rows[iid].get(key)
            try: return (0, float(str(v).replace("Rp", "").replace(".", "")))
            except ValueError: return (1, str(v or "").lower())
        self._order.sort(key=k, reverse=rev)
        self._sort = (key, rev)
        self._fill()

    def selected(self):
        return [self.rows[i] for i in self.tree.selection() if i in self.rows]

    def selected_one(self):
        s = self.selected()
        if not s:
            info("Pilih satu baris terlebih dahulu.")
            return None
        return s[0]


# ---------------------------------------------------------------- toolbar
class Toolbar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

    def button(self, text, cmd, danger=False, secondary=False, variant=None):
        variant = variant or ("danger" if danger else ("secondary" if secondary else "primary"))
        b = make_button(self, text, guard(cmd), variant)
        b.pack(side="left", padx=(0, theme.SP2))
        return b

    def search(self, on_change, placeholder="Cari..."):
        var = tk.StringVar()
        style_entry(self, textvariable=var, placeholder_text=placeholder, width=280).pack(side="left", padx=(0, theme.SP2))
        var.trace_add("write", lambda *_: on_change())
        return var

    def combo(self, values, on_change, default=None, width=140):
        var = tk.StringVar(value=default or values[0])
        style_option(self, values, var, width, lambda _: on_change()).pack(side="left", padx=(0, theme.SP2))
        return var


# ---------------------------------------------------------------- form
class FormDialog(ctk.CTkToplevel):
    """fields: [(key,label,tipe,opsi)] tipe: entry|combo|text|password. Error ditampilkan inline (merah)."""

    def __init__(self, master, title, fields, initial=None, on_save=None, width=440):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=theme.PANEL)
        if master is not None:
            self.transient(master.winfo_toplevel())
        self.on_save, self.vars, self.widgets = on_save, {}, {}
        initial = initial or {}
        ctk.CTkLabel(self, text=title, font=theme.font(theme.FS_SECTION, True), text_color=theme.TEXT).pack(anchor="w", padx=theme.PAD, pady=(theme.PAD, 0))
        body = ctk.CTkScrollableFrame(self, fg_color="transparent", width=width, height=min(66 * len(fields) + 10, 480))
        body.pack(fill="both", expand=True, padx=theme.SP3, pady=(theme.SP2, 0))
        first = None
        for key, label, kind, *opt in fields:
            ctk.CTkLabel(body, text=label.upper(), font=theme.font(theme.FS_TH - 1, True), text_color=theme.MUTED).pack(anchor="w", pady=(theme.SP3, 2))
            val = initial.get(key)
            if kind == "combo":
                v = tk.StringVar(value=str(val if val not in (None, "") else (opt[0][0] if opt and opt[0] else "")))
                w = style_option(body, opt[0], v, width=width - 40)
            elif kind == "text":
                w = ctk.CTkTextbox(body, height=72, corner_radius=theme.R_INPUT, fg_color=theme.INPUT, border_width=1,
                                   border_color=theme.LINE, text_color=theme.TEXT, font=theme.font(theme.FS_BODY))
                w.insert("1.0", "" if val is None else str(val)); v = None
            else:
                v = tk.StringVar(value="" if val is None else str(val))
                w = style_entry(body, textvariable=v, show="*" if kind == "password" else "")
                w.bind("<Return>", lambda e: self._save())
            w.pack(fill="x")
            if first is None and kind in ("entry", "password"):
                first = w
            self.vars[key], self.widgets[key] = v, w
        self.err = ctk.CTkLabel(self, text="", text_color=theme.DANGER, font=theme.font(theme.FS_CAPTION), wraplength=width - 20, justify="left", anchor="w")
        self.err.pack(fill="x", padx=theme.PAD, pady=(theme.SP2, 0))
        bar = ctk.CTkFrame(self, fg_color="transparent"); bar.pack(fill="x", padx=theme.PAD, pady=(theme.SP2, theme.PAD))
        make_button(bar, "Simpan", self._save, "primary", width=96).pack(side="right")
        make_button(bar, "Batal", self.destroy, "secondary", width=96).pack(side="right", padx=theme.SP2)
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        if master is not None:
            top = master.winfo_toplevel()
            self.geometry(f"+{top.winfo_rootx() + max(20, (top.winfo_width() - self.winfo_reqwidth()) // 2)}+{top.winfo_rooty() + 60}")
        self.after(120, lambda: (self.grab_set(), (first or self).focus_set()))

    def values(self):
        out = {}
        for k, v in self.vars.items():
            out[k] = v.get().strip() if v is not None else self.widgets[k].get("1.0", "end").strip()
        return out

    def _save(self):
        try:
            self.on_save(self.values())
        except ServiceError as e:
            self.err.configure(text=str(e))
            return
        except Exception as e:
            self.err.configure(text=f"Terjadi kesalahan: {e}")
            return
        self.destroy()


class ScanEntry(ctk.CTkEntry):
    """Kolom scan besar: Enter memanggil callback lalu mengosongkan dan memfokuskan ulang."""

    def __init__(self, master, on_scan, placeholder="Pindai barcode lalu Enter", **kw):
        kw.setdefault("height", theme.H_SCAN)
        super().__init__(master, placeholder_text=placeholder, corner_radius=theme.R_INPUT, fg_color=theme.INPUT,
                         border_color=theme.ACCENT, border_width=2, text_color=theme.TEXT,
                         placeholder_text_color=theme.MUTED, font=theme.font(theme.FS_SCAN, True), **kw)
        self.on_scan = guard(on_scan)
        self.bind("<Return>", self._enter)

    def _enter(self, _):
        code = self.get().strip()
        if code:
            self.on_scan(code)
        self.delete(0, "end")
        self.focus_set()

    def focus_soon(self):
        self.after(60, self.focus_set)


def ask_save(master, **kw):
    from tkinter import filedialog
    return filedialog.asksaveasfilename(parent=master, **kw)
