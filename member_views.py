"""Screens for a library member (read-only)."""
import tkinter as tk
from datetime import date
from tkinter import ttk

import store
import theme as T
from widgets import (STATUS_TAG, Card, Page, SearchEntry, Table, banner, book_title, due_badge, empty,
                     fmt_date, greeting, kv_row, label, list_row, page_header, stat_row)

ALL_CATEGORIES = "All categories"


class MemberPage(Page):
    @property
    def me(self):
        return store.member(self.shell.member_id)


class HomePage(MemberPage):
    def build(self):
        m = self.me
        page_header(self, f"{greeting()}, {m['name'].split()[0]}",
                    f"Member #{m['member_id']} · {date.today():%A, %d %B %Y}")
        loans = store.active_loans(m["member_id"])
        overdue = [r for r in loans if store.is_overdue(r)]
        history = store.member_loans(m["member_id"])
        stat_row(self, [("Books with you", len(loans)), ("Overdue", len(overdue)),
                        ("Fine due", f"{sum(store.current_fine(r) for r in overdue):.0f} Tk",
                         f"+{store.FINE_PER_DAY:.0f} Tk per late day")])
        if overdue:
            banner(self, f"You have {len(overdue)} overdue book(s). Please return them to the library "
                         "to stop the fine from growing.").pack(fill="x", pady=(0, 16))

        main = tk.Frame(self, bg=T.BG)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3, uniform="m")
        main.columnconfigure(1, weight=2, uniform="m")
        left, right = tk.Frame(main, bg=T.BG), tk.Frame(main, bg=T.BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        right.grid(row=0, column=1, sticky="nsew")

        current = Card(left, "Currently borrowed")
        current.pack(fill="x")
        if not loans:
            empty(current.body, "You have no books right now. Browse the catalogue to find one.")
        for i, r in enumerate(loans):
            list_row(current.body, book_title(r["book_id"]),
                     f"Borrowed {fmt_date(r['issue_date'])} · due {fmt_date(r['due_date'])}",
                     badge_spec=due_badge(r), last=i == len(loans) - 1)

        reading = Card(right, "Your reading")
        reading.pack(fill="x", pady=(0, 16))
        returned = [r for r in history if r["return_date"] is not None]
        kv_row(reading.body, "Books borrowed", str(len(history)))
        kv_row(reading.body, "Returned", str(len(returned)))
        kv_row(reading.body, "Fines paid", f"{sum(float(r['fine']) for r in returned):.0f} Tk")
        kv_row(reading.body, "Loan period", f"{store.LOAN_DAYS} days", last=True)
        ttk.Button(right, text="Browse books", style="Primary.TButton",
                   command=lambda: self.shell.navigate("browse")).pack(fill="x")


class BrowsePage(MemberPage):
    def build(self):
        _, self.subtitle = page_header(self, "Browse books",
                                       "See what is on the shelf. Ask the librarian to issue a book.")
        bar = tk.Frame(self, bg=T.BG)
        bar.pack(fill="x", pady=(0, 12))
        self.search = SearchEntry(bar, "Search title, author or category…", self.refresh)
        self.search.pack(side="left", fill="x", expand=True)
        self.category = ttk.Combobox(bar, values=[ALL_CATEGORIES] + store.CATEGORIES, state="readonly", width=16)
        self.category.set(ALL_CATEGORIES)
        self.category.pack(side="left", padx=(12, 0))
        self.category.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.only_available = tk.BooleanVar()
        ttk.Checkbutton(bar, text="Only available", variable=self.only_available,
                        command=self.refresh).pack(side="left", padx=(14, 0))

        self.table = Table(self, [("title", "Title", 280, "w"), ("author", "Author", 220, "w"),
                                  ("category", "Category", 130, "w"), ("availability", "Availability", 130, "w")],
                           height=14, empty_text="No books match your search.")
        self.count = label(self, "", "small", fg=T.MUTED)
        self.count.pack(side="bottom", anchor="w", pady=(10, 0))
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        q, cat = self.search.text().lower(), self.category.get()
        rows = []
        for b in store.books():
            avail = store.available(b)
            if q and q not in f"{b['title']} {b['author']} {b['category']}".lower():
                continue
            if cat != ALL_CATEGORIES and b["category"] != cat:
                continue
            if self.only_available.get() and avail <= 0:
                continue
            rows.append((b["book_id"], [b["title"], b["author"], b["category"],
                                        f"{avail} available" if avail > 0 else "All on loan"],
                         "green" if avail > 0 else "muted"))
        self.table.load(rows)
        self.count.configure(text=f"{len(rows)} book(s)")


class LoansPage(MemberPage):
    COLS = [("book", "Book", 260, "w"), ("issued", "Issued", 120, "w"), ("due", "Due", 120, "w"),
            ("returned", "Returned", 120, "w"), ("status", "Status", 100, "w"), ("fine", "Fine", 90, "e")]

    def build(self):
        page_header(self, "My loans", "Everything you have borrowed")
        history = store.member_loans(self.shell.member_id)
        current = [r for r in history if r["return_date"] is None]
        label(self, f"Fine rule: {store.FINE_PER_DAY:.0f} Tk for every day past the due date.", "small",
              fg=T.MUTED).pack(side="bottom", anchor="w", pady=(10, 0))
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        for title, loans, text in ((f"Current · {len(current)}", current, "You have no books right now."),
                                   (f"History · {len(history)}", history, "You have not borrowed anything yet.")):
            tab = tk.Frame(tabs, bg=T.BG)
            tabs.add(tab, text=title)
            table = Table(tab, self.COLS, height=12, empty_text=text)
            table.pack(fill="both", expand=True, pady=(16, 0))
            table.load([(r["borrow_id"], [book_title(r["book_id"]), fmt_date(r["issue_date"]),
                                          fmt_date(r["due_date"]), fmt_date(r["return_date"]), store.status(r),
                                          f"{store.current_fine(r):.0f} Tk"], STATUS_TAG[store.status(r)])
                        for r in loans])


class ProfilePage(MemberPage):
    def build(self):
        m = self.me
        page_header(self, "Profile", "Your library membership")
        row = tk.Frame(self, bg=T.BG)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1, uniform="p")
        row.columnconfigure(1, weight=1, uniform="p")
        card = Card(row)
        card.grid(row=0, column=0, sticky="ew")
        kv_row(card.body, "Member ID", f"#{m['member_id']}")
        kv_row(card.body, "Name", m["name"])
        kv_row(card.body, "Email", m["email"] or "—")
        kv_row(card.body, "Phone", m["phone"] or "—", last=True)
        label(self, "To change your details, please ask the librarian.", "small", fg=T.MUTED).pack(
            anchor="w", pady=(10, 0))


SECTIONS = [("", [("home", "Home", "⌂"), ("browse", "Browse books", "▤"),
                  ("loans", "My loans", "☰"), ("profile", "Profile", "◉")])]
PAGES = {"home": HomePage, "browse": BrowsePage, "loans": LoansPage, "profile": ProfilePage}
