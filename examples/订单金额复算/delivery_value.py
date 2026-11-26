import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
PRAGMA foreign_keys = ON;
CREATE TABLE orders(
  id TEXT PRIMARY KEY, price INTEGER NOT NULL);
CREATE TABLE arrivals(
  id TEXT PRIMARY KEY, line TEXT NOT NULL REFERENCES orders(id),
  qty INTEGER NOT NULL);
CREATE TABLE returns(
  id TEXT PRIMARY KEY, arrival TEXT NOT NULL REFERENCES arrivals(id),
  qty INTEGER NOT NULL);
INSERT INTO orders VALUES ('L01', 500), ('L02', 300);
INSERT INTO arrivals VALUES
  ('D01', 'L01', 3), ('D02', 'L01', 1), ('D03', 'L02', 2);
INSERT INTO returns VALUES ('R01', 'D01', 1), ('R02', 'D01', 1);
""")
wrong = db.execute("""
SELECT a.line, SUM(a.qty), SUM(COALESCE(r.qty, 0)),
       SUM(a.qty - COALESCE(r.qty, 0)),
       SUM(a.qty - COALESCE(r.qty, 0)) * o.price
FROM arrivals AS a
JOIN orders AS o ON o.id = a.line
LEFT JOIN returns AS r ON r.arrival = a.id
GROUP BY a.line, o.price
ORDER BY a.line
""").fetchall()
print("直接连接", wrong)
right = db.execute("""
WITH by_arrival AS (
  SELECT arrival, SUM(qty) AS qty
  FROM returns GROUP BY arrival
)
SELECT a.line, SUM(a.qty), SUM(COALESCE(r.qty, 0)),
       SUM(a.qty - COALESCE(r.qty, 0)),
       SUM(a.qty - COALESCE(r.qty, 0)) * o.price
FROM arrivals AS a
JOIN orders AS o ON o.id = a.line
LEFT JOIN by_arrival AS r ON r.arrival = a.id
GROUP BY a.line, o.price
ORDER BY a.line
""").fetchall()
print("先汇总退回", right)
print("两种合计", sum(x[4] for x in wrong), sum(x[4] for x in right))
