# Library Management System

A desktop library management app built with Python (Tkinter) for a Database Management System course. It covers the four CRUD operations plus search, using raw SQL with no ORM.

## Features

**Librarian**
- Dashboard: totals, books that need attention, recent activity, copies by category
- Books and members: add, edit, delete, search, filter
- Issue and return books, with automatic late fines (5 Tk per day)
- Overdue list and full borrow history

**Member**
- Home: books currently borrowed, due dates, fines
- Browse the catalogue and see what is available
- Own loan history and profile

## Run

You only need Python 3. The app uses just the standard library (`tkinter` + `sqlite3`), so there is nothing to install with pip.

```bash
python run.py            # opens a librarian window and a member window
python main.py           # opens a single window (choose the role at sign-in)
```

On macOS with Homebrew Python, install Tk first: `brew install python-tk@3.14`.

On first run the app creates `library.db` and fills it with sample data. Delete that file to start fresh.

| Role | Sign in with |
|---|---|
| Librarian | `admin` / `admin123` |
| Member | `rahim@example.com` / `01711000001` |

## Database

| Table | Columns |
|---|---|
| Books | book_id, title, author, category, quantity |
| Members | member_id, name, phone, email |
| Borrow | borrow_id, book_id → Books, member_id → Members, issue_date, due_date, return_date, fine |
| Librarian | librarian_id, username, password |

The schema diagram is in [Library_Schema_Diagram.pdf](Library_Schema_Diagram.pdf). All SQL lives in [store.py](store.py). The database is SQLite for now, and the tables match the MySQL design, so moving to MySQL only means changing that file.

## Project layout

| File | Purpose |
|---|---|
| `main.py` | App entry point, sign-in screen, navigation |
| `librarian_views.py` | Librarian screens |
| `member_views.py` | Member screens |
| `widgets.py` | Shared widgets (tables, dialogs, cards) |
| `theme.py` | Colors, fonts, styles |
| `store.py` | Database access (raw SQL) |
| `sample_data.py` | Demo data loaded on first run |
| `run.py` | Opens both windows at once |
