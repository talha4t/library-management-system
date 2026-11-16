"""In-memory sample data. Shapes match the MySQL tables in the schema diagram,
so this module can later be replaced by real SQL queries."""
from datetime import date, timedelta

today = date.today()

CATEGORIES = ["Science", "Novel", "History", "Programming", "Mathematics"]

BOOKS = [
    {"book_id": 1, "title": "A Brief History of Time", "author": "Stephen Hawking", "category": "Science", "quantity": 3},
    {"book_id": 2, "title": "Pather Panchali", "author": "Bibhutibhushan Bandyopadhyay", "category": "Novel", "quantity": 2},
    {"book_id": 3, "title": "Sapiens", "author": "Yuval Noah Harari", "category": "History", "quantity": 4},
    {"book_id": 4, "title": "Python Crash Course", "author": "Eric Matthes", "category": "Programming", "quantity": 5},
    {"book_id": 5, "title": "Database System Concepts", "author": "Abraham Silberschatz", "category": "Programming", "quantity": 3},
    {"book_id": 6, "title": "Himu", "author": "Humayun Ahmed", "category": "Novel", "quantity": 2},
    {"book_id": 7, "title": "Discrete Mathematics", "author": "Kenneth Rosen", "category": "Mathematics", "quantity": 2},
]

MEMBERS = [
    {"member_id": 1, "name": "Rahim Uddin", "phone": "01711000001", "email": "rahim@example.com"},
    {"member_id": 2, "name": "Nusrat Jahan", "phone": "01811000002", "email": "nusrat@example.com"},
    {"member_id": 3, "name": "Arif Hasan", "phone": "01911000003", "email": "arif@example.com"},
    {"member_id": 4, "name": "Sadia Islam", "phone": "01611000004", "email": "sadia@example.com"},
]

BORROWS = [
    # returned on time
    {"borrow_id": 1, "book_id": 1, "member_id": 1, "issue_date": today - timedelta(days=30),
     "due_date": today - timedelta(days=16), "return_date": today - timedelta(days=18), "fine": 0.0},
    # returned late (fine already charged)
    {"borrow_id": 2, "book_id": 3, "member_id": 2, "issue_date": today - timedelta(days=25),
     "due_date": today - timedelta(days=11), "return_date": today - timedelta(days=8), "fine": 15.0},
    # still borrowed, not due yet
    {"borrow_id": 3, "book_id": 4, "member_id": 1, "issue_date": today - timedelta(days=3),
     "due_date": today + timedelta(days=11), "return_date": None, "fine": 0.0},
    # still borrowed, overdue
    {"borrow_id": 4, "book_id": 2, "member_id": 3, "issue_date": today - timedelta(days=20),
     "due_date": today - timedelta(days=6), "return_date": None, "fine": 0.0},
    {"borrow_id": 5, "book_id": 5, "member_id": 4, "issue_date": today - timedelta(days=5),
     "due_date": today + timedelta(days=9), "return_date": None, "fine": 0.0},
]

LIBRARIANS = [
    {"librarian_id": 1, "username": "admin", "password": "admin123"},
]
