"""Fresh-process Tk checks using only temporary databases."""

from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory


def run_checks():
    root = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(root / "copying.py")], timeout=25, check=True)
    with TemporaryDirectory(prefix="arcs-tk-") as directory:
        database = Path(directory) / "arcs.sqlite3"
        for mode in ("create", "reopen"):
            subprocess.run([sys.executable, str(root / "smoke.py"), mode, str(database)],
                           timeout=25, check=True)
        author_database = Path(directory) / "authoring.sqlite3"
        for mode in ("create", "reopen"):
            subprocess.run([sys.executable, str(root / "authoring.py"), mode, str(author_database)],
                           timeout=35, check=True)
        subprocess.run([sys.executable, str(root / "searching.py"), str(Path(directory) / "search.sqlite3")],
                       timeout=35, check=True)
        for failure in ("CORE", "MEM", "DISK", "WRITE"):
            failed_database = Path(directory) / f"{failure}.sqlite3"
            result = subprocess.run([sys.executable, str(root / "failure.py"), failure,
                                     str(failed_database)], timeout=25, capture_output=True, text=True)
            assert result.returncode == 1, result.stdout + result.stderr
            assert "closed and joined" in result.stdout, result.stdout + result.stderr
            print(result.stdout.strip())
            if failure == "WRITE":
                connection = sqlite3.connect(failed_database)
                try:
                    assert connection.execute("SELECT count(*) FROM basic").fetchone()[0] == 0
                    assert connection.execute("SELECT count(*) FROM arc").fetchone()[0] == 0
                finally:
                    connection.close()


if __name__ == "__main__":
    run_checks()
