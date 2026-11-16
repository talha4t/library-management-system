# Library Management System

A desktop library management app built with Python (Tkinter) for a Database Management System course. It covers the four CRUD operations plus search, using raw SQL with no ORM.

## Features

**Librarian**
- Dashboard: totals, books that need attention, recent activity, copies by category
- Books and members: add, edit, delete, search, filter
- Categories: create, rename (books follow the new name), delete when empty
- Issue and return books, with automatic late fines (5 Tk per day)
- Overdue list and full borrow history

**Member**
- Home: books currently borrowed, due dates, fines
- Browse the catalogue and see what is available
- Own loan history and profile

## Setup on Windows

The app needs only Python 3. It uses just the standard library (`tkinter` + `sqlite3`), so there is nothing to install with pip.

### 1. Install Python

1. Download Python 3 from https://www.python.org/downloads/windows/
2. Run the installer and tick **Add python.exe to PATH** on the first screen.
3. Keep **tcl/tk and IDLE** ticked under *Customize installation*. It is on by default, and Tkinter needs it.

Open **Command Prompt** or **PowerShell** and check the install:

```bat
py --version
py -m tkinter
```

The second command opens a small test window. If it appears, Tkinter works. Close it and continue.

### 2. Get the code

With Git installed:

```bat
git clone https://github.com/talha4t/library-management-system.git
cd library-management-system
```

Without Git: on the GitHub page click **Code → Download ZIP**, extract it, then open a terminal in the extracted folder:

```bat
cd %USERPROFILE%\Downloads\library-management-system-main
```

### 3. Run the app

```bat
py run.py
```

This opens the sign-in window. Choose **Librarian** or **Member** at the top. `py main.py` does the same thing.

To open the window with the member role already selected:

```bat
py main.py --role member
```

To see the librarian and member views side by side, run `py run.py` in one terminal and `py main.py --role member` in a second terminal. Both windows share the same database.

### Optional: use a virtual environment

There are no packages to install, so this step is not required. If you prefer to keep projects separate:

```bat
py -m venv .venv
.venv\Scripts\activate
python run.py
```

In PowerShell, if activation is blocked, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Troubleshooting

| Problem | Fix |
|---|---|
| `'py' is not recognized` | Python is not installed, or PATH was not ticked. Reinstall Python and tick **Add python.exe to PATH**. |
| `No module named tkinter` | Run the Python installer again, choose **Modify**, and tick **tcl/tk and IDLE**. |
| You want to start with fresh sample data | Close the app and delete `library.db` in the project folder. |

## Setup on macOS / Linux

```bash
git clone https://github.com/talha4t/library-management-system.git
cd library-management-system
python3 run.py
```

With Homebrew Python on macOS, install Tk first: `brew install python-tk@3.14`. On Ubuntu/Debian: `sudo apt install python3-tk`.

## Sample data

On first run the app creates `library.db` and fills it with sample data. Delete that file to start fresh.

| Role | Sign in with |
|---|---|
| Librarian | `admin` / `admin123` |
| Member | `rahim@example.com` / `01711000001` |

## Database

| Table | Columns |
|---|---|
| Category | category_id, name (unique) |
| Books | book_id, title, author, category → Category.name, quantity |
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
| `run.py` | Starts the app (same as `main.py`) |
