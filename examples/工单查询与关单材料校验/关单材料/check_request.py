from pathlib import Path
from rdflib import Graph, Namespace, RDF
from pyshacl import validate
folder = Path(__file__).resolve().parent
def read(name):
    return (folder / name).read_text(encoding="utf-8-sig")
graph = Graph().parse(data=read("data.ttl"), format="turtle")
shapes = Graph().parse(data=read("shapes.ttl"), format="turtle")
ex = Namespace("https://example.org/enterprise/")
targets = set(graph.subjects(RDF.type, ex.CloseRequest))
conforms, _, _ = validate(graph, shacl_graph=shapes, inference="none")
rows = list(graph.query(read("ownership.rq")))
pairs = sum(1 for request in targets
            for _ in graph.objects(request, ex.forTicket)
            for record in graph.objects(request, ex.resolutionRecord)
            for _ in graph.objects(record, ex.forTicket))
print(f"候选申请数：{len(targets)}")
print(f"形状通过：{conforms}")
print(f"可比较配对数：{pairs}")
print(f"明确错配行数：{len(rows)}")
for row in rows:
    print(" ".join(str(value).rsplit("/", 1)[-1] for value in row))
