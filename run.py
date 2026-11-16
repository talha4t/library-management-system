"""Open two windows at once: one for the librarian and one for a member.

    python run.py

Both windows use the same database (library.db), so a book the librarian issues
shows up in the member window after switching pages. Close both windows to exit.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    procs = [subprocess.Popen([sys.executable, str(ROOT / "main.py"), "--role", role], cwd=ROOT)
             for role in ("librarian", "member")]
    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
