import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

folder = Path(__file__).resolve().parent
data_file = sys.argv[1] if len(sys.argv) > 1 else "order.ttl"
data = Graph().parse(folder / data_file, format="turtle")
shape = Graph().parse(folder / "order_shape.ttl", format="turtle")
query = (folder / "order_query.rq").read_text(encoding="utf-8-sig")
conforms, _, report = validate(data, shacl_graph=shape)
print("结构通过" if conforms else "结构错误")
if not conforms:
    print(report)
for row in data.query(query):
    print("查得客户", row.customer)
