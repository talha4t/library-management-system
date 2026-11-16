"""Data access layer (raw SQL).

Both apps (librarian and member) read and write through these functions, so they
share one database. For now it is a local SQLite file (library.db); the tables match
the MySQL schema, so moving to MySQL later means changing only this file.
"""
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import sample_data

DB_PATH = Path(__file__).parent / "library.db"
FINE_PER_DAY = 5.0  # Tk per late day
LOAN_DAYS = 14

sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode()))

SCHEMA = """
CREATE TABLE IF NOT EXISTS Category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(50) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Books (
    book_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    title     VARCHAR(200) NOT NULL,
    author    VARCHAR(100) NOT NULL,
    category  VARCHAR(50)  NOT NULL,
    quantity  INT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS Members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name      VARCHAR(100) NOT NULL,
    phone     VARCHAR(20),
    email     VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS Borrow (
    borrow_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INT NOT NULL REFERENCES Books(book_id),
    member_id   INT NOT NULL REFERENCES Members(member_id),
    issue_date  DATE NOT NULL,
    due_date    DATE NOT NULL,
    return_date DATE,
    fine        DECIMAL(8,2) NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS Librarian (
    librarian_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username     VARCHAR(50) NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL
);
"""


def _conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _query(sql, params=()):
    with closing(_conn()) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _one(sql, params=()):
    rows = _query(sql, params)
    return rows[0] if rows else None


def _execute(sql, params=()):
    with closing(_conn()) as conn, conn:
        conn.execute(sql, params)


def init():
    """Create tables and load sample data the first time."""
    with closing(_conn()) as conn, conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM Books").fetchone()[0]:
            # older databases had no Category table: fill it from the books
            if not conn.execute("SELECT COUNT(*) FROM Category").fetchone()[0]:
                conn.execute("INSERT INTO Category (name) SELECT DISTINCT category FROM Books")
            return
        conn.executemany("INSERT INTO Category (name) VALUES (?)", [(c,) for c in sample_data.CATEGORIES])
        conn.executemany("INSERT INTO Books VALUES (:book_id, :title, :author, :category, :quantity)",
                         sample_data.BOOKS)
        conn.executemany("INSERT INTO Members VALUES (:member_id, :name, :phone, :email)",
                         sample_data.MEMBERS)
        conn.executemany("INSERT INTO Borrow VALUES (:borrow_id, :book_id, :member_id, :issue_date,"
                         " :due_date, :return_date, :fine)", sample_data.BORROWS)
        conn.executemany("INSERT INTO Librarian VALUES (:librarian_id, :username, :password)",
                         sample_data.LIBRARIANS)


# ---------- auth ----------
def authenticate(username, password):
    return _one("SELECT * FROM Librarian WHERE username = ? AND password = ?", (username, password))


def authenticate_member(email, phone):
    """Members have no password column, so they sign in with email + phone."""
    return _one("SELECT * FROM Members WHERE LOWER(email) = LOWER(?) AND phone = ?", (email, phone))


# ---------- reads ----------
def books():
    return _query("SELECT * FROM Books ORDER BY book_id")


def members():
    return _query("SELECT * FROM Members ORDER BY member_id")


def borrows():
    return _query("SELECT * FROM Borrow ORDER BY borrow_id")


def borrow(borrow_id):
    return _one("SELECT * FROM Borrow WHERE borrow_id = ?", (borrow_id,))


def book(book_id):
    return _one("SELECT * FROM Books WHERE book_id = ?", (book_id,))


def member(member_id):
    return _one("SELECT * FROM Members WHERE member_id = ?", (member_id,))


def on_loan(book_id):
    return _one("SELECT COUNT(*) AS n FROM Borrow WHERE book_id = ? AND return_date IS NULL",
                (book_id,))["n"]


def available(b):
    return b["quantity"] - on_loan(b["book_id"])


def active_loans(member_id=None):
    if member_id is None:
        return _query("SELECT * FROM Borrow WHERE return_date IS NULL ORDER BY due_date")
    return _query("SELECT * FROM Borrow WHERE return_date IS NULL AND member_id = ? ORDER BY due_date",
                  (member_id,))


def member_loans(member_id):
    return _query("SELECT * FROM Borrow WHERE member_id = ? ORDER BY issue_date DESC", (member_id,))


def is_overdue(r, today=None):
    return r["return_date"] is None and r["due_date"] < (today or date.today())


def status(r):
    if r["return_date"] is not None:
        return "Returned"
    return "Overdue" if is_overdue(r) else "Borrowed"


def fine_for(due, returned):
    days = (returned - due).days
    return days * FINE_PER_DAY if days > 0 else 0.0


def current_fine(r):
    """Fine already charged (returned) or fine so far (still out)."""
    if r["return_date"] is not None:
        return float(r["fine"])
    return fine_for(r["due_date"], date.today())


def categories():
    return [r["name"] for r in _query("SELECT name FROM Category ORDER BY name")]


def category_rows():
    """Each category with how many titles and copies use it."""
    return _query("""
        SELECT c.category_id, c.name, COUNT(b.book_id) AS titles, COALESCE(SUM(b.quantity), 0) AS copies
        FROM Category c LEFT JOIN Books b ON b.category = c.name
        GROUP BY c.category_id, c.name ORDER BY c.name""")


# ---------- category writes ----------
def _check_category_name(name, ignore_id=None):
    name = name.strip()
    if not name:
        raise ValueError("Category name is required.")
    if len(name) > 50:
        raise ValueError("Category name must be 50 characters or fewer.")
    clash = _one("SELECT category_id FROM Category WHERE LOWER(name) = LOWER(?)", (name,))
    if clash and clash["category_id"] != ignore_id:
        raise ValueError(f"A category called “{name}” already exists.")
    return name


def add_category(name):
    _execute("INSERT INTO Category (name) VALUES (?)", (_check_category_name(name),))


def rename_category(category_id, new_name):
    old = _one("SELECT name FROM Category WHERE category_id = ?", (category_id,))["name"]
    new_name = _check_category_name(new_name, ignore_id=category_id)
    with closing(_conn()) as conn, conn:
        conn.execute("UPDATE Category SET name = ? WHERE category_id = ?", (new_name, category_id))
        conn.execute("UPDATE Books SET category = ? WHERE category = ?", (new_name, old))


def delete_category(category_id):
    row = _one("SELECT name FROM Category WHERE category_id = ?", (category_id,))
    used = _one("SELECT COUNT(*) AS n FROM Books WHERE category = ?", (row["name"],))["n"]
    if used:
        raise ValueError(f"{used} book(s) use “{row['name']}”. Move them to another category first.")
    _execute("DELETE FROM Category WHERE category_id = ?", (category_id,))


# ---------- book writes ----------
def add_book(title, author, category, quantity):
    _execute("INSERT INTO Books (title, author, category, quantity) VALUES (?, ?, ?, ?)",
             (title, author, category, int(quantity)))


def update_book(book_id, title, author, category, quantity):
    n = on_loan(book_id)
    if quantity < n:
        raise ValueError(f"{n} copies are on loan, so quantity cannot be lower than that.")
    _execute("UPDATE Books SET title = ?, author = ?, category = ?, quantity = ? WHERE book_id = ?",
             (title, author, category, int(quantity), book_id))


def delete_book(book_id):
    if on_loan(book_id):
        raise ValueError("This book has copies on loan. Return them first.")
    _execute("DELETE FROM Borrow WHERE book_id = ?", (book_id,))
    _execute("DELETE FROM Books WHERE book_id = ?", (book_id,))


# ---------- member writes ----------
def add_member(name, phone, email):
    _execute("INSERT INTO Members (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))


def update_member(member_id, name, phone, email):
    _execute("UPDATE Members SET name = ?, phone = ?, email = ? WHERE member_id = ?",
             (name, phone, email, member_id))


def delete_member(member_id):
    if active_loans(member_id):
        raise ValueError("This member still has books on loan.")
    _execute("DELETE FROM Borrow WHERE member_id = ?", (member_id,))
    _execute("DELETE FROM Members WHERE member_id = ?", (member_id,))


# ---------- circulation ----------
def issue(book_id, member_id, issue_date, due_date):
    if available(book(book_id)) <= 0:
        raise ValueError("No copies available.")
    if due_date < issue_date:
        raise ValueError("Due date must be on or after the issue date.")
    _execute("INSERT INTO Borrow (book_id, member_id, issue_date, due_date, return_date, fine)"
             " VALUES (?, ?, ?, ?, NULL, 0)", (book_id, member_id, issue_date, due_date))


def return_loan(borrow_id, return_date):
    r = borrow(borrow_id)
    if return_date < r["issue_date"]:
        raise ValueError("Return date cannot be before the issue date.")
    fine = fine_for(r["due_date"], return_date)
    _execute("UPDATE Borrow SET return_date = ?, fine = ? WHERE borrow_id = ?",
             (return_date, fine, borrow_id))
    return fine
