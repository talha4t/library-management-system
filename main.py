"""Library Management System - desktop app (Tkinter).

    python main.py                  # opens the sign-in window (Librarian selected)
    python main.py --role member    # opens with Member selected
"""
import argparse
import tkinter as tk
from tkinter import ttk

import librarian_views
import member_views
import store
import theme as T
from widgets import Segmented, Sidebar, label, logo


class LoginView(tk.Frame):
    TEXT = {
        "Librarian": ("Username", "Password", "Manage books, members and loans",
                      "Demo: admin / admin123"),
        "Member": ("Email", "Phone", "Use the email and phone you registered with",
                   "Demo: rahim@example.com / 01711000001"),
    }

    def __init__(self, master, app, role):
        super().__init__(master, bg=T.BG)
        self.app = app
        box = tk.Frame(self, bg=T.BG)
        box.place(relx=0.5, rely=0.45, anchor="center")

        brand = tk.Frame(box, bg=T.BG)
        brand.pack(anchor="w")
        logo(brand, T.BG).pack(side="left")
        label(brand, "Library", "brand").pack(side="left", padx=(10, 0))
        label(box, "Sign in", "h1").pack(anchor="w", pady=(18, 2))
        self.subtitle = label(box, "", "body", fg=T.MUTED)
        self.subtitle.pack(anchor="w", pady=(0, 16))

        self.role = Segmented(box, ["Librarian", "Member"], role, self.switch)
        self.role.pack(fill="x", pady=(0, 18))
        self.label1 = label(box, "", "small_b")
        self.label1.pack(anchor="w", pady=(0, 4))
        self.entry1 = ttk.Entry(box, width=38)
        self.entry1.pack(fill="x", pady=(0, 12))
        self.label2 = label(box, "", "small_b")
        self.label2.pack(anchor="w", pady=(0, 4))
        self.entry2 = ttk.Entry(box, width=38, show="•")
        self.entry2.pack(fill="x", pady=(0, 6))
        self.error = label(box, "", "small", fg=T.fg_of("red"))
        self.error.pack(anchor="w", pady=(0, 6))
        ttk.Button(box, text="Sign in", style="Primary.TButton", command=self.submit).pack(fill="x")
        self.hint = label(box, "", "small", fg=T.MUTED)
        self.hint.pack(anchor="w", pady=(12, 0))

        for e in (self.entry1, self.entry2):
            e.bind("<Return>", lambda _: self.submit())
        self.switch(role)

    def switch(self, role):
        first, second, subtitle, hint = self.TEXT[role]
        self.label1.configure(text=first)
        self.label2.configure(text=second)
        self.subtitle.configure(text=subtitle)
        self.hint.configure(text=hint)
        self.error.configure(text="")
        self.entry1.delete(0, "end")
        self.entry2.delete(0, "end")
        self.entry1.focus_set()

    def submit(self):
        a, b = self.entry1.get().strip(), self.entry2.get()
        if self.role.value == "Librarian":
            user = store.authenticate(a, b)
            if user:
                return self.app.open_librarian(user["username"])
            self.error.configure(text="Incorrect username or password.")
        else:
            member = store.authenticate_member(a, b.strip())
            if member:
                return self.app.open_member(member["member_id"])
            self.error.configure(text="No member found with that email and phone.")
        self.entry2.delete(0, "end")


class Shell(tk.Frame):
    """Sidebar on the left, current page on the right."""

    def __init__(self, master, app, sections, pages, role_text, user_text, **attrs):
        super().__init__(master, bg=T.BG)
        self.app, self.pages, self.page, self.arg = app, pages, None, None
        for k, v in attrs.items():
            setattr(self, k, v)
        self.sidebar = Sidebar(self, sections, self.navigate, role_text, user_text, app.show_login)
        self.sidebar.pack(side="left", fill="y")
        tk.Frame(self, bg=T.BORDER, width=1).pack(side="left", fill="y")
        self.content = tk.Frame(self, bg=T.BG)
        self.content.pack(side="left", fill="both", expand=True, padx=36, pady=(28, 24))
        self.navigate(next(iter(pages)))

    def navigate(self, key, arg=None):
        self.arg = arg
        if self.page:
            self.page.destroy()
        self.page = self.pages[key](self.content, self)
        self.page.pack(fill="both", expand=True)
        self.sidebar.set_active(key)


class App(tk.Tk):
    def __init__(self, role="Librarian"):
        super().__init__()
        self.default_role = role
        offset = 40 if role == "Librarian" else 140  # so two windows do not cover each other
        self.geometry(f"1200x780+{offset}+{offset - 10}")
        self.minsize(1040, 700)
        self.configure(bg=T.BG)
        T.setup(self)
        store.init()
        self.show_login()

    def _show(self, build):
        for w in self.winfo_children():
            w.destroy()
        build().pack(fill="both", expand=True)

    def show_login(self):
        self.title("Library · Sign in")
        self._show(lambda: LoginView(self, self, self.default_role))

    def open_librarian(self, username):
        self.title("Library · Librarian")
        self._show(lambda: Shell(self, self, librarian_views.SECTIONS, librarian_views.PAGES,
                                 "Librarian", username, user=username))

    def open_member(self, member_id):
        self.default_role = "Member"
        self.title("Library · Member")
        self._show(lambda: Shell(self, self, member_views.SECTIONS, member_views.PAGES,
                                 "Member", store.member(member_id)["name"], member_id=member_id))


def main():
    parser = argparse.ArgumentParser(description="Library Management System")
    parser.add_argument("--role", choices=["librarian", "member"], default="librarian")
    args = parser.parse_args()
    App(role=args.role.capitalize()).mainloop()


if __name__ == "__main__":
    main()
