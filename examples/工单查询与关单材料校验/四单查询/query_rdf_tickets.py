from pathlib import Path
from rdflib import Graph
graph = Graph().parse("ticket-data.ttl", format="turtle")
query = Path("ticket-query.rq").read_text(encoding="utf-8-sig")
for ticket, status in graph.query(query):
    print(str(ticket).rsplit("/", 1)[-1], status)
