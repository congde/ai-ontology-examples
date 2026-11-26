import sqlite3
import sys
from contextlib import closing
from pathlib import Path

folder = Path(__file__).resolve().parent
query_file, *setup_files = sys.argv[1:] or ["orders.sql"]
with closing(sqlite3.connect(":memory:")) as connection:
    for name in setup_files:
        connection.executescript((folder / name).read_text(encoding="utf-8-sig"))
    sql = (folder / query_file).read_text(encoding="utf-8-sig")
    for row in connection.execute(sql):
        display = ["NULL" if value is None else value for value in row]
        print(*display, sep=" / ")
