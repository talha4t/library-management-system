"""Start the app (same as `python main.py`).

    python run.py                   # sign-in window, Librarian selected
    python run.py --role member     # sign-in window, Member selected

To see the librarian and member views side by side, open a second window in
another terminal with `python main.py --role member`. Both use library.db.
"""
from main import main

if __name__ == "__main__":
    main()
