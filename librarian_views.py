"""Screens for the librarian (full CRUD + issue/return)."""
import tkinter as tk
from collections import Counter
from datetime import date, timedelta
from tkinter import ttk

import store
import theme as T
from widgets import (STATUS_TAG, BarChart, Card, DateEntry, Dialog, FilterCombo, Page, SearchEntry,
                     Segmented, Table, book_title, confirm, due_badge, empty, fmt_date, greeting,
                     label, list_row, member_name, page_header, stat_row)

ALL_CATEGORIES = "All categories"


# ---------- dialogs ----------
def book_dialog(master, book_id, on_saved):
    b = store.book(book_id) if book_id else None
    d = Dialog(master, "Edit book" if b else "Add book")
    title = d.field("Title", ttk.Entry)
    author = d.field("Author", ttk.Entry)
    left, right = d.columns()
    category = d.field("Category", ttk.Combobox, parent=left, values=store.categories(), state="readonly")
    copies = d.field("Copies", ttk.Spinbox, parent=right, from_=0, to=999)
    if b:
        title.insert(0, b["title"])
        author.insert(0, b["author"])
        category.set(b["category"])
        copies.set(b["quantity"])
        label(d.body, f"{store.on_loan(book_id)} copies currently on loan", "small", fg=T.MUTED).pack(anchor="w")
    else:
        category.set(category["values"][0] if category["values"] else "")
        copies.set(1)

    def save():
        t, a = title.get().strip(), author.get().strip()
        if not t or not a:
            return d.show_error("Title and author are required.")
        if not category.get():
            return d.show_error("Create a category first (Catalogue → Categories).")
        try:
            qty = int(copies.get())
        except ValueError:
            return d.show_error("Copies must be a whole number.")
        if qty < (0 if b else 1):
            return d.show_error("Add at least one copy.")
        try:
            if b:
                store.update_book(book_id, t, a, category.get(), qty)
            else:
                store.add_book(t, a, category.get(), qty)
        except ValueError as e:
            return d.show_error(str(e))
        d.destroy()
        on_saved("Book updated" if b else f"“{t}” added")

    d.actions("Save changes" if b else "Add book", save)
    d.open(focus=title)


def member_dialog(master, member_id, on_saved):
    m = store.member(member_id) if member_id else None
    d = Dialog(master, "Edit member" if m else "Add member")
    name = d.field("Full name", ttk.Entry)
    phone = d.field("Phone", ttk.Entry)
    email = d.field("Email", ttk.Entry)
    if m:
        name.insert(0, m["name"])
        phone.insert(0, m["phone"] or "")
        email.insert(0, m["email"] or "")

    def save():
        n, p, e = name.get().strip(), phone.get().strip(), email.get().strip()
        if not n:
            return d.show_error("Name is required.")
        if e and "@" not in e:
            return d.show_error("That email address does not look right.")
        if m:
            store.update_member(member_id, n, p, e)
        else:
            store.add_member(n, p, e)
        d.destroy()
        on_saved("Member updated" if m else f"{n} added")

    d.actions("Save changes" if m else "Add member", save)
    d.open(focus=name)


def category_dialog(master, category, on_saved):
    """category is None (add) or a row from store.category_rows() (rename)."""
    d = Dialog(master, "Rename category" if category else "New category", 400)
    name = d.field("Name", ttk.Entry)
    if category:
        name.insert(0, category["name"])
        name.select_range(0, "end")
        if category["titles"]:
            label(d.body, f"{category['titles']} book(s) will move to the new name.", "small",
                  fg=T.MUTED).pack(anchor="w")
    else:
        label(d.body, "e.g. Philosophy, Children, Biography", "small", fg=T.MUTED).pack(anchor="w")

    def save():
        try:
            if category:
                store.rename_category(category["category_id"], name.get())
            else:
                store.add_category(name.get())
        except ValueError as e:
            return d.show_error(str(e))
        d.destroy()
        on_saved("Category renamed" if category else f"“{name.get().strip()}” added")

    d.actions("Save" if category else "Add category", save)
    d.open(focus=name)


def return_dialog(master, borrow_id, on_done):
    r = store.borrow(borrow_id)
    d = Dialog(master, "Return book", 420)
    label(d.body, book_title(r["book_id"]), "body_b").pack(anchor="w")
    label(d.body, f"{member_name(r['member_id'])} · due {fmt_date(r['due_date'])}", "small",
          fg=T.MUTED).pack(anchor="w", pady=(0, 14))
    ret = d.field(f"Return date ({DateEntry.HINT})", DateEntry)
    info = tk.Label(d.body, font=T.FONTS["body_b"], padx=12, pady=8, anchor="w")
    info.pack(fill="x", pady=(0, 6))

    def preview(*_):
        try:
            when = ret.get_date()
        except ValueError:
            info.configure(text="Enter a date like 15-11-2026", bg=T.SUBTLE, fg=T.MUTED)
            return None
        fine = store.fine_for(r["due_date"], when)
        if fine:
            info.configure(text=f"{(when - r['due_date']).days} days late · fine {fine:.0f} Tk "
                                f"({store.FINE_PER_DAY:.0f} Tk/day)", bg=T.bg_of("amber"), fg=T.fg_of("amber"))
        else:
            info.configure(text="On time · no fine", bg=T.bg_of("green"), fg=T.fg_of("green"))
        return when

    ret.var.trace_add("write", preview)
    preview()

    def save():
        when = preview()
        if when is None:
            return d.show_error("Enter a valid return date.")
        try:
            fine = store.return_loan(borrow_id, when)
        except ValueError as e:
            return d.show_error(str(e))
        d.destroy()
        on_done("Book returned" + (f" · {fine:.0f} Tk fine" if fine else ""))

    d.actions("Confirm return", save)
    d.open(focus=ret)


def loan_columns(*drop):
    cols = [("id", "ID", 50, "e"), ("book", "Book", 220, "w"), ("member", "Member", 150, "w"),
            ("issued", "Issued", 110, "w"), ("due", "Due", 110, "w"), ("returned", "Returned", 110, "w"),
            ("status", "Status", 90, "w"), ("fine", "Fine", 80, "e")]
    return [c for c in cols if c[0] not in drop]


def loan_rows(loans, *drop):
    rows = []
    for r in loans:
        st = store.status(r)
        values = {"id": r["borrow_id"], "book": book_title(r["book_id"]), "member": member_name(r["member_id"]),
                  "issued": fmt_date(r["issue_date"]), "due": fmt_date(r["due_date"]),
                  "returned": fmt_date(r["return_date"]), "status": st,
                  "fine": f"{store.current_fine(r):.0f} Tk"}
        keys = [c[0] for c in loan_columns(*drop)]
        rows.append((r["borrow_id"], [values[k] for k in keys], STATUS_TAG[st]))
    return rows


# ---------- pages ----------
class DashboardPage(Page):
    def build(self):
        page_header(self, f"{greeting()}, {self.shell.user}", date.today().strftime("%A, %d %B %Y"))
        books, loans = store.books(), store.active_loans()
        overdue = [r for r in loans if store.is_overdue(r)]
        stat_row(self, [("Total copies", sum(b["quantity"] for b in books), f"{len(books)} titles"),
                        ("On loan", len(loans)), ("Members", len(store.members())), ("Overdue", len(overdue))])

        main = tk.Frame(self, bg=T.BG)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3, uniform="m")
        main.columnconfigure(1, weight=2, uniform="m")
        left, right = tk.Frame(main, bg=T.BG), tk.Frame(main, bg=T.BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        right.grid(row=0, column=1, sticky="nsew")

        attention = Card(left, "Needs attention")
        attention.pack(fill="x", pady=(0, 16))
        soon = sorted((r for r in loans if (r["due_date"] - date.today()).days <= 3), key=lambda r: r["due_date"])
        if not soon:
            empty(attention.body, "Nothing due in the next 3 days.")
        shown = soon[:3]
        for i, r in enumerate(shown):
            list_row(attention.body, book_title(r["book_id"]), member_name(r["member_id"]),
                     badge_spec=due_badge(r), last=i == len(shown) - 1)
        if len(soon) > len(shown):
            label(attention.body, f"+{len(soon) - len(shown)} more on the Overdue page", "small",
                  fg=T.MUTED).pack(anchor="w", pady=(6, 0))

        recent_card = Card(left, "Recent activity")
        recent_card.pack(fill="x")
        recent = sorted(store.borrows(), key=lambda r: r["return_date"] or r["issue_date"], reverse=True)[:4]
        if not recent:
            empty(recent_card.body, "No activity yet.")
        for i, r in enumerate(recent):
            returned = r["return_date"] is not None
            text = f"{member_name(r['member_id'])} {'returned' if returned else 'borrowed'} {book_title(r['book_id'])}"
            list_row(recent_card.body, text, right_text=fmt_date(r["return_date"] or r["issue_date"]),
                     last=i == len(recent) - 1)

        actions = Card(right, "Quick actions")
        actions.pack(fill="x", pady=(0, 16))
        ttk.Button(actions.body, text="Issue a book", style="Primary.TButton",
                   command=lambda: self.shell.navigate("circulation")).pack(fill="x", pady=(4, 8))
        ttk.Button(actions.body, text="+  Add book", style="Secondary.TButton",
                   command=lambda: book_dialog(self, None, self.saved)).pack(fill="x", pady=(0, 8))
        ttk.Button(actions.body, text="+  Add member", style="Secondary.TButton",
                   command=lambda: member_dialog(self, None, self.saved)).pack(fill="x")

        chart = Card(right, "Copies by category")
        chart.pack(fill="x")
        counts = Counter()
        for b in books:
            counts[b["category"]] += b["quantity"]
        if counts:
            BarChart(chart.body, sorted(counts.items())).pack(fill="x")
        else:
            empty(chart.body, "No books yet.")

    def saved(self, msg):
        self.toast(msg)
        self.shell.navigate("dashboard")


class BooksPage(Page):
    def build(self):
        actions, self.subtitle = page_header(self, "Books")
        ttk.Button(actions, text="+  Add book", style="Primary.TButton",
                   command=lambda: book_dialog(self, None, self.saved)).pack()

        bar = tk.Frame(self, bg=T.BG)
        bar.pack(fill="x", pady=(0, 12))
        self.search = SearchEntry(bar, "Search title, author or category…", self.refresh)
        self.search.pack(side="left", fill="x", expand=True)
        self.category = ttk.Combobox(bar, values=[ALL_CATEGORIES] + store.categories(), state="readonly", width=16)
        self.category.set(ALL_CATEGORIES)
        self.category.pack(side="left", padx=(12, 0))
        self.category.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.only_available = tk.BooleanVar()
        ttk.Checkbutton(bar, text="Only available", variable=self.only_available,
                        command=self.refresh).pack(side="left", padx=(14, 0))

        self.table = Table(self, [("id", "ID", 50, "e"), ("title", "Title", 250, "w"),
                                  ("author", "Author", 200, "w"), ("category", "Category", 120, "w"),
                                  ("available", "Available", 90, "center"), ("status", "Status", 110, "w")],
                           height=12, on_select=self.on_select, on_open=self.edit,
                           empty_text="No books match your filters.")
        foot = tk.Frame(self, bg=T.BG)
        foot.pack(side="bottom", fill="x", pady=(12, 0))
        self.delete_btn = ttk.Button(foot, text="Delete", style="Danger.TButton", command=self.delete)
        self.delete_btn.pack(side="right")
        self.edit_btn = ttk.Button(foot, text="Edit", style="Secondary.TButton",
                                   command=lambda: self.edit(self.table.selected()))
        self.edit_btn.pack(side="right", padx=(0, 8))
        self.hint = label(foot, "", "body", fg=T.MUTED)
        self.hint.pack(side="left")
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        q, cat = self.search.text().lower(), self.category.get()
        books = store.books()
        rows = []
        for b in books:
            avail = store.available(b)
            if q and q not in f"{b['title']} {b['author']} {b['category']}".lower():
                continue
            if cat != ALL_CATEGORIES and b["category"] != cat:
                continue
            if self.only_available.get() and avail <= 0:
                continue
            rows.append((b["book_id"], [b["book_id"], b["title"], b["author"], b["category"],
                                        f"{avail} of {b['quantity']}", "In stock" if avail > 0 else "All on loan"],
                         None if avail > 0 else "red"))
        self.table.load(rows)
        self.subtitle.configure(text=f"{len(books)} titles in the catalogue · showing {len(rows)}")
        self.on_select(None)

    def on_select(self, book_id):
        state = "normal" if book_id else "disabled"
        self.edit_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        if book_id:
            self.hint.configure(text=f"Selected: {book_title(book_id)}", fg=T.TEXT)
        else:
            self.hint.configure(text="Select a book to edit or delete it. Double-click to edit.", fg=T.MUTED)

    def edit(self, book_id):
        if book_id:
            book_dialog(self, book_id, self.saved)

    def delete(self):
        book_id = self.table.selected()
        if not book_id or not confirm(self, "Delete book?", f"“{book_title(book_id)}” will be removed permanently."):
            return
        try:
            store.delete_book(book_id)
            self.saved("Book deleted")
        except ValueError as e:
            self.toast(str(e), error=True)

    def saved(self, msg):
        self.toast(msg)
        self.refresh()


class MembersPage(Page):
    def build(self):
        actions, self.subtitle = page_header(self, "Members")
        ttk.Button(actions, text="+  Add member", style="Primary.TButton",
                   command=lambda: member_dialog(self, None, self.saved)).pack()

        self.search = SearchEntry(self, "Search by name or member ID…", self.refresh)
        self.search.pack(fill="x", pady=(0, 12))
        self.table = Table(self, [("id", "ID", 50, "e"), ("name", "Name", 200, "w"), ("phone", "Phone", 140, "w"),
                                  ("email", "Email", 220, "w"), ("loans", "On loan", 80, "center")],
                           height=6, on_select=self.on_select, on_open=self.edit,
                           empty_text="No members match your search.")
        self.table.pack(fill="x")

        foot = tk.Frame(self, bg=T.BG)
        foot.pack(fill="x", pady=(12, 16))
        self.delete_btn = ttk.Button(foot, text="Delete", style="Danger.TButton", command=self.delete)
        self.delete_btn.pack(side="right")
        self.edit_btn = ttk.Button(foot, text="Edit", style="Secondary.TButton",
                                   command=lambda: self.edit(self.table.selected()))
        self.edit_btn.pack(side="right", padx=(0, 8))
        self.hint = label(foot, "", "body", fg=T.MUTED)
        self.hint.pack(side="left")

        self.loans_title = label(self, "Loans", "h2")
        self.loans_title.pack(anchor="w", pady=(0, 8))
        self.loans = Table(self, loan_columns("member", "id"), height=4,
                           empty_text="Select a member to see their loans.")
        self.loans.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        q = self.search.text().lower()
        members = store.members()
        rows = [(m["member_id"], [m["member_id"], m["name"], m["phone"], m["email"],
                                  len(store.active_loans(m["member_id"]))], None)
                for m in members if not q or q in m["name"].lower() or q == str(m["member_id"])]
        self.table.load(rows)
        self.subtitle.configure(text=f"{len(members)} registered members")
        self.on_select(None)

    def on_select(self, member_id):
        state = "normal" if member_id else "disabled"
        self.edit_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        if member_id:
            history = store.member_loans(member_id)
            self.hint.configure(text=f"Selected: {member_name(member_id)}", fg=T.TEXT)
            self.loans_title.configure(text=f"Loans of {member_name(member_id)} · {len(history)}")
            self.loans.empty.configure(text="This member has not borrowed anything yet.")
            self.loans.load(loan_rows(history, "member", "id"))
        else:
            self.hint.configure(text="Select a member to see loans, edit or delete. Double-click to edit.",
                                fg=T.MUTED)
            self.loans_title.configure(text="Loans")
            self.loans.empty.configure(text="Select a member to see their loans.")
            self.loans.load([])

    def edit(self, member_id):
        if member_id:
            member_dialog(self, member_id, self.saved)

    def delete(self):
        member_id = self.table.selected()
        if not member_id or not confirm(self, "Delete member?",
                                        f"{member_name(member_id)} will be removed permanently."):
            return
        try:
            store.delete_member(member_id)
            self.saved("Member deleted")
        except ValueError as e:
            self.toast(str(e), error=True)

    def saved(self, msg):
        self.toast(msg)
        self.refresh()


class CategoriesPage(Page):
    def build(self):
        actions, self.subtitle = page_header(self, "Categories")
        ttk.Button(actions, text="+  New category", style="Primary.TButton",
                   command=lambda: category_dialog(self, None, self.saved)).pack()

        foot = tk.Frame(self, bg=T.BG)
        foot.pack(side="bottom", fill="x", pady=(12, 0))
        self.delete_btn = ttk.Button(foot, text="Delete", style="Danger.TButton", command=self.delete)
        self.delete_btn.pack(side="right")
        self.rename_btn = ttk.Button(foot, text="Rename", style="Secondary.TButton",
                                     command=lambda: self.rename(self.table.selected()))
        self.rename_btn.pack(side="right", padx=(0, 8))
        self.hint = label(foot, "", "body", fg=T.MUTED)
        self.hint.pack(side="left")

        self.table = Table(self, [("name", "Category", 260, "w"), ("titles", "Titles", 100, "center"),
                                  ("copies", "Copies", 100, "center")],
                           height=12, on_select=self.on_select, on_open=self.rename,
                           empty_text="No categories yet. Add one to start organising books.")
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        self.rows = {r["category_id"]: r for r in store.category_rows()}
        self.table.load([(cid, [r["name"], r["titles"], r["copies"]], None if r["titles"] else "muted")
                         for cid, r in self.rows.items()])
        self.subtitle.configure(text=f"{len(self.rows)} categories · used to group books in the catalogue")
        self.on_select(None)

    def on_select(self, category_id):
        state = "normal" if category_id else "disabled"
        self.rename_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        if category_id:
            self.hint.configure(text=f"Selected: {self.rows[category_id]['name']}", fg=T.TEXT)
        else:
            self.hint.configure(text="Select a category to rename or delete it. Only empty ones can be deleted.",
                                fg=T.MUTED)

    def rename(self, category_id):
        if category_id:
            category_dialog(self, self.rows[category_id], self.saved)

    def delete(self):
        category_id = self.table.selected()
        if not category_id:
            return
        name = self.rows[category_id]["name"]
        if not confirm(self, "Delete category?", f"“{name}” will be removed."):
            return
        try:
            store.delete_category(category_id)
            self.saved("Category deleted")
        except ValueError as e:
            self.toast(str(e), error=True)

    def saved(self, msg):
        self.toast(msg)
        self.refresh()


class CirculationPage(Page):
    def build(self):
        page_header(self, "Issue & Return", "Lend books to members and check them back in")
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        issue_tab, return_tab = tk.Frame(self.tabs, bg=T.BG), tk.Frame(self.tabs, bg=T.BG)
        self.tabs.add(issue_tab, text="Issue a book")
        self.tabs.add(return_tab, text=f"Return · {len(store.active_loans())} on loan")
        self.build_issue(issue_tab)
        self.build_return(return_tab)
        if getattr(self.shell, "arg", None) == "return":
            self.tabs.select(1)

    # --- issue ---
    def build_issue(self, tab):
        card = Card(tab, padx=20, pady=18)
        card.pack(fill="x", pady=(16, 0))
        g = card.body
        g.columnconfigure(0, weight=1, uniform="c")
        g.columnconfigure(1, weight=1, uniform="c")

        members = [(m["member_id"], f"{m['name']}  ·  #{m['member_id']}") for m in store.members()]
        books = [(b["book_id"], f"{b['title']} — {b['author']}  ({store.available(b)} left)")
                 for b in store.books() if store.available(b) > 0]
        label(g, "Member", "small_b").grid(row=0, column=0, sticky="w", pady=(0, 4))
        label(g, "Book", "small_b").grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(12, 0))
        self.member = FilterCombo(g, members, on_pick=self.update_issue)
        self.member.grid(row=1, column=0, sticky="ew")
        self.book = FilterCombo(g, books, on_pick=self.update_issue)
        self.book.grid(row=1, column=1, sticky="ew", padx=(12, 0))

        label(g, f"Issue date ({DateEntry.HINT})", "small_b").grid(row=2, column=0, sticky="w", pady=(14, 4))
        label(g, f"Due date ({DateEntry.HINT})", "small_b").grid(row=2, column=1, sticky="w", pady=(14, 4),
                                                                padx=(12, 0))
        self.issued = DateEntry(g)
        self.issued.grid(row=3, column=0, sticky="ew")
        self.due = DateEntry(g, date.today() + timedelta(days=store.LOAN_DAYS))
        self.due.grid(row=3, column=1, sticky="ew", padx=(12, 0))
        self.issued.bind("<FocusOut>", self.sync_due)

        self.note = label(g, "", "small", fg=T.MUTED, anchor="w", justify="left")
        self.note.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.issue_btn = ttk.Button(g, text="Issue book", style="Primary.TButton", command=self.do_issue)
        self.issue_btn.grid(row=5, column=0, sticky="w", pady=(14, 0))
        if not books:
            label(tab, "Every copy is currently on loan.", "body", fg=T.MUTED).pack(anchor="w", pady=12)
        self.update_issue()

    def sync_due(self, _=None):
        try:
            self.due.set_date(self.issued.get_date() + timedelta(days=store.LOAN_DAYS))
        except ValueError:
            pass

    def update_issue(self, _=None):
        member_id, book_id = self.member.value(), self.book.value()
        self.issue_btn.configure(state="normal" if member_id and book_id else "disabled")
        if member_id:
            loans = store.active_loans(member_id)
            late = [r for r in loans if store.is_overdue(r)]
            text = f"{member_name(member_id)} has {len(loans)} book(s) on loan"
            if late:
                self.note.configure(text=f"{text}, {len(late)} overdue.", fg=T.fg_of("red"))
            else:
                self.note.configure(text=text + ".", fg=T.MUTED)
        else:
            self.note.configure(text="Type in a box to search, then pick from the list. "
                                     f"Loan period is {store.LOAN_DAYS} days.", fg=T.MUTED)

    def do_issue(self):
        member_id, book_id = self.member.value(), self.book.value()
        if not (member_id and book_id):
            return
        try:
            store.issue(book_id, member_id, self.issued.get_date(), self.due.get_date())
        except ValueError as e:
            msg = str(e)
            if "does not match format" in msg or "unconverted" in msg:
                msg = f"Dates must look like {date.today():%d-%m-%Y}."
            self.note.configure(text=msg, fg=T.fg_of("red"))
            return
        self.toast(f"Issued to {member_name(member_id)} · due {fmt_date(self.due.get_date())}")
        self.shell.navigate("circulation")

    # --- return ---
    def build_return(self, tab):
        loans = store.active_loans()
        self.loans = Table(tab, loan_columns("returned"), height=11, on_select=self.on_select,
                           on_open=self.open_return, empty_text="No books are on loan right now.")
        self.loans.tree.heading("fine", text="Fine so far")
        self.loans.load(loan_rows(loans, "returned"))
        foot = tk.Frame(tab, bg=T.BG)
        foot.pack(side="bottom", fill="x", pady=(12, 0))
        self.loans.pack(fill="both", expand=True, pady=(16, 0))
        self.return_btn = ttk.Button(foot, text="Return selected book", style="Primary.TButton",
                                     command=lambda: self.open_return(self.loans.selected()))
        self.return_btn.pack(side="right")
        self.return_hint = label(foot, "", "body", fg=T.MUTED)
        self.return_hint.pack(side="left")
        self.on_select(None)

    def on_select(self, borrow_id):
        self.return_btn.configure(state="normal" if borrow_id else "disabled")
        self.return_hint.configure(text="Select a loan to check the book back in. Double-click works too."
                                   if not borrow_id else f"Selected: {book_title(store.borrow(borrow_id)['book_id'])}")

    def open_return(self, borrow_id):
        if borrow_id:
            return_dialog(self, borrow_id, self.returned)

    def returned(self, msg):
        self.toast(msg)
        self.shell.navigate("circulation", arg="return")


class OverduePage(Page):
    def build(self):
        page_header(self, "Overdue", "Books past their due date that are still out")
        rows = [r for r in store.active_loans() if store.is_overdue(r)]
        if not rows:
            card = Card(self)
            card.pack(fill="x")
            label(card.body, "✓  All caught up. Nothing is overdue.", "body_b", fg=T.fg_of("green")).pack(anchor="w")
            return
        stat_row(self, [("Overdue loans", len(rows)),
                        ("Fines so far", f"{sum(store.current_fine(r) for r in rows):.0f} Tk")], columns=4)
        cols = [("id", "ID", 50, "e"), ("book", "Book", 220, "w"), ("member", "Member", 160, "w"),
                ("due", "Due", 110, "w"), ("late", "Days late", 90, "center"), ("fine", "Fine so far", 100, "e")]
        self.table = Table(self, cols, height=9, on_select=self.on_select, on_open=self.open_return)
        self.table.load([(r["borrow_id"], [r["borrow_id"], book_title(r["book_id"]), member_name(r["member_id"]),
                                           fmt_date(r["due_date"]), (date.today() - r["due_date"]).days,
                                           f"{store.current_fine(r):.0f} Tk"], "red") for r in rows])
        foot = tk.Frame(self, bg=T.BG)
        foot.pack(side="bottom", fill="x", pady=(12, 0))
        self.table.pack(fill="both", expand=True)
        self.btn = ttk.Button(foot, text="Return selected book", style="Primary.TButton",
                              command=lambda: self.open_return(self.table.selected()))
        self.btn.pack(side="right")
        label(foot, "Select a loan to mark it returned.", "body", fg=T.MUTED).pack(side="left")
        self.on_select(None)

    def on_select(self, borrow_id):
        self.btn.configure(state="normal" if borrow_id else "disabled")

    def open_return(self, borrow_id):
        if borrow_id:
            return_dialog(self, borrow_id, self.returned)

    def returned(self, msg):
        self.toast(msg)
        self.shell.navigate("overdue")


class HistoryPage(Page):
    def build(self):
        page_header(self, "Borrow history", "Every loan, past and present")
        bar = tk.Frame(self, bg=T.BG)
        bar.pack(fill="x", pady=(0, 12))
        members = [(0, "All members")] + [(m["member_id"], f"{m['name']}  ·  #{m['member_id']}")
                                         for m in store.members()]
        self.member = FilterCombo(bar, members, on_pick=lambda _: self.refresh(), width=30)
        self.member.set("All members")
        self.member.pack(side="left")
        self.status = Segmented(bar, ["All", "Borrowed", "Overdue", "Returned"], "All", lambda _: self.refresh())
        self.status.pack(side="left", padx=(14, 0))

        self.table = Table(self, loan_columns(), height=13, empty_text="No loans match these filters.")
        self.summary = label(self, "", "small", fg=T.MUTED)
        self.summary.pack(side="bottom", anchor="w", pady=(10, 0))
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        member_id, status = self.member.value(), self.status.value
        if member_id is None and self.member.get().strip() not in ("", "All members"):
            rows = []  # typed text that matches nobody yet
        else:
            rows = [r for r in store.borrows()
                    if (not member_id or r["member_id"] == member_id)
                    and (status == "All" or store.status(r) == status)]
        rows.sort(key=lambda r: r["issue_date"], reverse=True)
        self.table.load(loan_rows(rows))
        self.summary.configure(text=f"{len(rows)} loan(s) · total fines "
                                    f"{sum(store.current_fine(r) for r in rows):.0f} Tk")


SECTIONS = [
    ("", [("dashboard", "Dashboard", "▦")]),
    ("CATALOGUE", [("books", "Books", "▤"), ("categories", "Categories", "◫"), ("members", "Members", "☷")]),
    ("CIRCULATION", [("circulation", "Issue & Return", "⇄"), ("overdue", "Overdue", "◷"),
                     ("history", "History", "↺")]),
]
PAGES = {"dashboard": DashboardPage, "books": BooksPage, "categories": CategoriesPage, "members": MembersPage,
         "circulation": CirculationPage, "overdue": OverduePage, "history": HistoryPage}
