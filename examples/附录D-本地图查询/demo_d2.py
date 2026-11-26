import csv
import json
from pathlib import Path

from semantica.semantic_extract.types import Triplet
from semantica.triplet_store import TripletStore

# 摄取经人工核对的订单关系，并保留来源字段
source = Path("orders.csv")
with source.open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))

base = "https://example.org/enterprise/"
store = TripletStore(backend="oxigraph")
for row in rows:
    store.add_triplet(Triplet(
        subject=base + row["order_id"],
        predicate=base + "belongsTo",
        object=base + row["customer_id"],
    ))

# 沿用9.5节同一关系名称查询O-001
result = store.execute_query("""
PREFIX ex: <https://example.org/enterprise/>
SELECT ?customer WHERE { ex:O-001 ex:belongsTo ?customer . }
""")
customers = [row["customer"]["value"] for row in result.bindings]
assert customers == [base + "C-001"], customers
used_rows = [row for row in rows if row["order_id"] == "O-001"]
print(json.dumps({"customers": customers, "file": source.name,
                  "source_rows": used_rows}, ensure_ascii=False))
