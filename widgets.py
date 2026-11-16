"""Reusable Tkinter widgets and small helpers used by both views."""
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

import store
import theme as T


# ---------- text helpers ----------
def fmt_date(d):
    return d.strftime("%d %b %Y") if d else "—"


def greeting():
    hour = datetime.now().hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"


def book_title(book_id):
    b = store.book(book_id)
    return b["title"] if b else f"#{book_id}"


def member_name(member_id):
    m = store.member(member_id)
    return m["name"] if m else f"#{member_id}"


def due_badge(r):
    """(text, kind) describing how soon a loan is due."""
    days = (r["due_date"] - date.today()).days
    if days < 0:
        return f"{-days}d overdue", "red"
    if days == 0:
        return "Due today", "amber"
    if days <= 3:
        return f"Due in {days}d", "amber"
    return f"Due in {days}d", "blue"


STATUS_TAG = {"Overdue": "red", "Borrowed": None, "Returned": "muted"}


# ---------- basic building blocks ----------
def label(parent, text="", font="body", fg=T.TEXT, bg=T.BG, **kw):
    return tk.Label(parent, text=text, font=T.FONTS[font], fg=fg, bg=bg, **kw)


def badge(parent, text, kind):
    return tk.Label(parent, text=text, font=T.FONTS["small_b"], bg=T.bg_of(kind), fg=T.fg_of(kind),
                    padx=8, pady=2)


def banner(parent, text, kind="amber"):
    return tk.Label(parent, text=text, font=T.FONTS["body"], bg=T.bg_of(kind), fg=T.fg_of(kind),
                    anchor="w", justify="left", padx=14, pady=10)


def empty(parent, text):
    label(parent, text, "body", fg=T.MUTED).pack(pady=18)


def page_header(parent, title, subtitle=""):
    """Title + subtitle on the left. Returns (actions_frame, subtitle_label)."""
    row = tk.Frame(parent, bg=T.BG)
    row.pack(fill="x", pady=(0, 18))
    actions = tk.Frame(row, bg=T.BG)
    actions.pack(side="right", anchor="s")
    left = tk.Frame(row, bg=T.BG)
    left.pack(side="left", fill="x", expand=True)
    label(left, title, "h1").pack(anchor="w")
    sub = label(left, subtitle, "body", fg=T.MUTED)
    sub.pack(anchor="w", pady=(2, 0))
    return actions, sub


def logo(parent, bg):
    c = tk.Canvas(parent, width=30, height=30, bg=bg, highlightthickness=0)
    c.create_rectangle(0, 0, 30, 30, fill=T.PRIMARY, outline=T.PRIMARY)
    c.create_text(15, 15, text="L", fill="#FFFFFF", font=T.FONTS["brand"])
    return c


class Card(tk.Frame):
    def __init__(self, parent, title=None, padx=18, pady=16):
        super().__init__(parent, bg=T.BG, highlightthickness=1, highlightbackground=T.BORDER,
                         highlightcolor=T.BORDER)
        self.body = tk.Frame(self, bg=T.BG)
        self.body.pack(fill="both", expand=True, padx=padx, pady=pady)
        if title:
            label(self.body, title, "h2").pack(anchor="w", pady=(0, 6))


class StatCard(Card):
    def __init__(self, parent, title, value, hint=None):
        super().__init__(parent, padx=18, pady=14)
        label(self.body, title, "small", fg=T.MUTED).pack(anchor="w")
        label(self.body, str(value), "stat").pack(anchor="w", pady=(2, 0))
        if hint:
            label(self.body, hint, "small", fg=T.MUTED).pack(anchor="w")


def stat_row(parent, items, columns=None):
    """A row of equal-width StatCards. items = [(title, value) or (title, value, hint)]."""
    row = tk.Frame(parent, bg=T.BG)
    row.pack(fill="x", pady=(0, 16))
    columns = columns or len(items)
    for i in range(columns):
        row.columnconfigure(i, weight=1, uniform="stat")
    for i, item in enumerate(items):
        StatCard(row, *item).grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
    return row


def list_row(parent, title, sub=None, badge_spec=None, right_text=None, last=False):
    row = tk.Frame(parent, bg=T.BG)
    row.pack(fill="x")
    inner = tk.Frame(row, bg=T.BG)
    inner.pack(fill="x", pady=9)
    if badge_spec:
        badge(inner, *badge_spec).pack(side="right")
    elif right_text:
        label(inner, right_text, "small", fg=T.MUTED).pack(side="right")
    left = tk.Frame(inner, bg=T.BG)
    left.pack(side="left", fill="x", expand=True)
    label(left, title, "body_b" if sub else "body", anchor="w", justify="left").pack(anchor="w")
    if sub:
        label(left, sub, "small", fg=T.MUTED).pack(anchor="w")
    if not last:
        tk.Frame(row, bg=T.DIVIDER, height=1).pack(fill="x")


def kv_row(parent, key, value, last=False):
    row = tk.Frame(parent, bg=T.BG)
    row.pack(fill="x")
    inner = tk.Frame(row, bg=T.BG)
    inner.pack(fill="x", pady=10)
    label(inner, key, "body", fg=T.MUTED).pack(side="left")
    label(inner, value, "body_b").pack(side="right")
    if not last:
        tk.Frame(row, bg=T.DIVIDER, height=1).pack(fill="x")


# ---------- table ----------
class Table(tk.Frame):
    """Treeview with headings, scrollbar, zebra rows, colored rows and an empty state.

    columns = [(key, heading, width, anchor)]; load() takes [(iid, values, tag_or_None)].
    """

    def __init__(self, parent, columns, height=10, on_select=None, on_open=None,
                 empty_text="Nothing to show."):
        super().__init__(parent, bg=T.BG, highlightthickness=1, highlightbackground=T.BORDER)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings",
                                 height=height, selectmode="browse")
        for key, heading, width, anchor in columns:
            self.tree.heading(key, text=heading, anchor=anchor)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=True)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.tree.tag_configure("odd", background=T.ZEBRA)
        self.tree.tag_configure("muted", foreground=T.MUTED)
        for kind in T.KINDS:
            self.tree.tag_configure(kind, foreground=T.fg_of(kind))
        self.empty = tk.Label(self, text=empty_text, bg=T.BG, fg=T.MUTED, font=T.FONTS["body"])
        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda e: on_select(self.selected()))
        if on_open:
            self.tree.bind("<Double-1>", lambda e: self._open(on_open))

    def _open(self, callback):
        if self.selected() is not None:
            callback(self.selected())

    def load(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, (iid, values, tag) in enumerate(rows):
            tags = ["odd"] if i % 2 else []
            if tag:
                tags.append(tag)
            self.tree.insert("", "end", iid=str(iid), values=values, tags=tags)
        if rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")

    def selected(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None


# ---------- inputs ----------
class SearchEntry(ttk.Entry):
    """Entry with a grey placeholder; calls on_change() whenever the text changes."""

    def __init__(self, parent, placeholder, on_change, **kw):
        self.var = tk.StringVar()
        super().__init__(parent, textvariable=self.var, **kw)
        self.placeholder = placeholder
        self._ph = False
        self._show_placeholder()
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", lambda e: self._show_placeholder())
        self.bind("<Escape>", lambda e: self.var.set(""))
        self.var.trace_add("write", lambda *a: None if self._ph else on_change())

    def _show_placeholder(self):
        if not self.var.get():
            self._ph = True
            self.var.set(self.placeholder)
            self.configure(foreground=T.MUTED)

    def _clear_placeholder(self, _=None):
        if self._ph:
            self._ph = False
            self.var.set("")
            self.configure(foreground=T.TEXT)

    def text(self):
        return "" if self._ph else self.var.get().strip()


class FilterCombo(ttk.Combobox):
    """Combobox you can type into to filter the list. items = [(id, label)]."""

    def __init__(self, parent, items, on_pick=None, **kw):
        super().__init__(parent, **kw)
        self.on_pick = on_pick
        self.set_items(items)
        self.bind("<KeyRelease>", self._filter)
        self.bind("<<ComboboxSelected>>", lambda e: self._picked())

    def set_items(self, items):
        self.items = {lbl: i for i, lbl in items}
        self.labels = [lbl for _, lbl in items]
        self["values"] = self.labels

    def _filter(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        q = self.get().strip().lower()
        self["values"] = [lbl for lbl in self.labels if q in lbl.lower()]
        self._picked()

    def _picked(self):
        if self.on_pick:
            self.on_pick(self.value())

    def value(self):
        return self.items.get(self.get())


class DateEntry(ttk.Entry):
    FMT = "%d-%m-%Y"
    HINT = "DD-MM-YYYY"

    def __init__(self, parent, value=None, **kw):
        self.var = tk.StringVar(value=(value or date.today()).strftime(self.FMT))
        super().__init__(parent, textvariable=self.var, **kw)

    def get_date(self):
        """Parsed date; raises ValueError if the text is not a valid date."""
        return datetime.strptime(self.var.get().strip(), self.FMT).date()

    def set_date(self, d):
        self.var.set(d.strftime(self.FMT))


class Segmented(tk.Frame):
    """Pill-style single choice control."""

    def __init__(self, parent, options, value, on_change=None):
        super().__init__(parent, bg=T.SUBTLE, padx=3, pady=3)
        self.value, self.on_change, self.buttons = value, on_change, {}
        for opt in options:
            b = tk.Label(self, text=opt, font=T.FONTS["body_b"], padx=14, pady=6, cursor="hand2")
            b.pack(side="left", fill="x", expand=True)
            b.bind("<Button-1>", lambda e, o=opt: self.set(o, notify=True))
            self.buttons[opt] = b
        self._paint()

    def set(self, value, notify=False):
        self.value = value
        self._paint()
        if notify and self.on_change:
            self.on_change(value)

    def _paint(self):
        for opt, b in self.buttons.items():
            on = opt == self.value
            b.configure(bg=T.BG if on else T.SUBTLE, fg=T.TEXT if on else T.MUTED)


# ---------- dialogs & feedback ----------
class Dialog(tk.Toplevel):
    """Modal dialog: add fields with field(), finish with actions(), then open()."""

    def __init__(self, master, title, width=440):
        super().__init__(master)
        self.withdraw()
        self.title(title)
        self.configure(bg=T.BG)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.width = width
        self.body = tk.Frame(self, bg=T.BG)
        self.body.pack(fill="both", expand=True, padx=24, pady=22)
        label(self.body, title, "h2").pack(anchor="w", pady=(0, 14))
        self.error = label(self.body, "", "small", fg=T.fg_of("red"), wraplength=width - 48,
                           justify="left", anchor="w")
        self.bind("<Escape>", lambda e: self.destroy())

    def field(self, text, factory, parent=None, **kw):
        parent = parent or self.body
        label(parent, text, "small_b").pack(anchor="w", pady=(0, 4))
        widget = factory(parent, **kw)
        widget.pack(fill="x", pady=(0, 12))
        return widget

    def columns(self):
        row = tk.Frame(self.body, bg=T.BG)
        row.pack(fill="x")
        left, right = tk.Frame(row, bg=T.BG), tk.Frame(row, bg=T.BG)
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        right.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return left, right

    def actions(self, primary_text, on_primary, danger=False):
        self.error.pack(fill="x")
        row = tk.Frame(self.body, bg=T.BG)
        row.pack(fill="x", pady=(10, 0))
        ttk.Button(row, text=primary_text, style="DangerSolid.TButton" if danger else "Primary.TButton",
                   command=on_primary).pack(side="right")
        ttk.Button(row, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(
            side="right", padx=(0, 8))
        self.bind("<Return>", lambda e: on_primary())

    def show_error(self, msg):
        self.error.configure(text=msg)

    def open(self, focus=None):
        self.update_idletasks()
        top = self.master.winfo_toplevel()
        w, h = max(self.width, self.winfo_reqwidth()), self.winfo_reqheight()
        x = top.winfo_rootx() + (top.winfo_width() - w) // 2
        y = top.winfo_rooty() + max(40, (top.winfo_height() - h) // 3)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        (focus or self).focus_set()


def confirm(master, title, message, ok_text="Delete"):
    d = Dialog(master, title, 400)
    label(d.body, message, "body", fg=T.MUTED, wraplength=350, justify="left").pack(anchor="w", pady=(0, 6))
    result = {"ok": False}

    def ok():
        result["ok"] = True
        d.destroy()

    d.actions(ok_text, ok, danger=True)
    d.open()
    master.wait_window(d)
    return result["ok"]


def toast(root, message, error=False):
    """Small message at the bottom of the window that disappears by itself."""
    lbl = tk.Label(root, text=("✕  " if error else "✓  ") + message, font=T.FONTS["body_b"],
                   bg=T.fg_of("red") if error else T.TOAST, fg="#FFFFFF", padx=16, pady=10)
    lbl.place(relx=0.5, rely=1.0, y=-28, anchor="s")
    lbl.lift()
    root.after(2800, lbl.destroy)


class BarChart(tk.Canvas):
    """Simple horizontal bar chart. data = [(label, value)]."""

    def __init__(self, parent, data):
        self.data = data
        self.row_h = 30
        super().__init__(parent, bg=T.BG, highlightthickness=0, height=max(1, len(data)) * self.row_h + 4)
        self.bind("<Configure>", self._draw)

    def _draw(self, _=None):
        self.delete("all")
        w = self.winfo_width()
        if w < 60 or not self.data:
            return
        small, bold = T.FONTS["small"], T.FONTS["small_b"]
        label_w = 110
        top = max(v for _, v in self.data) or 1
        for i, (name, value) in enumerate(self.data):
            y = i * self.row_h + 6
            bar_w = (w - label_w - 40) * value / top
            self.create_text(label_w - 10, y + 9, text=name, anchor="e", fill=T.MUTED, font=small)
            self.create_rectangle(label_w, y, label_w + bar_w, y + 18, fill=T.PRIMARY, width=0)
            self.create_text(label_w + bar_w + 6, y + 9, text=str(value), anchor="w", fill=T.TEXT, font=bold)


# ---------- app frame ----------
class Sidebar(tk.Frame):
    def __init__(self, parent, sections, on_nav, role_text, user_text, on_logout):
        super().__init__(parent, bg=T.SIDEBAR, width=232)
        self.pack_propagate(False)
        brand = tk.Frame(self, bg=T.SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(22, 14))
        logo(brand, T.SIDEBAR).pack(side="left")
        label(brand, "Library", "brand", bg=T.SIDEBAR).pack(side="left", padx=(10, 0))

        self.items, self.active = {}, None
        for title, entries in sections:
            if title:
                label(self, title, "small_b", fg=T.MUTED, bg=T.SIDEBAR).pack(anchor="w", padx=24, pady=(14, 4))
            for key, text, icon in entries:
                item = tk.Label(self, text=f"{icon}   {text}", anchor="w", font=T.FONTS["body"],
                                bg=T.SIDEBAR, fg=T.TEXT, padx=12, pady=7, cursor="hand2")
                item.pack(fill="x", padx=12, pady=1)
                item.bind("<Button-1>", lambda e, k=key: on_nav(k))
                item.bind("<Enter>", lambda e, k=key: self._hover(k, True))
                item.bind("<Leave>", lambda e, k=key: self._hover(k, False))
                self.items[key] = item

        bottom = tk.Frame(self, bg=T.SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=20, pady=20)
        label(bottom, role_text, "small", fg=T.MUTED, bg=T.SIDEBAR).pack(anchor="w")
        label(bottom, user_text, "body_b", bg=T.SIDEBAR).pack(anchor="w", pady=(0, 10))
        ttk.Button(bottom, text="Sign out", style="Secondary.TButton", command=on_logout).pack(fill="x")

    def set_active(self, key):
        self.active = key
        for k, item in self.items.items():
            on = k == key
            item.configure(bg=T.SELECT if on else T.SIDEBAR, font=T.FONTS["body_b" if on else "body"])

    def _hover(self, key, entering):
        if key != self.active:
            self.items[key].configure(bg=T.HOVER if entering else T.SIDEBAR)


class Page(tk.Frame):
    """Base class for a screen. Subclasses implement build()."""

    def __init__(self, master, shell):
        super().__init__(master, bg=T.BG)
        self.shell = shell
        self.app = shell.app
        self.build()

    def build(self):
        raise NotImplementedError

    def toast(self, message, error=False):
        toast(self.app, message, error)
