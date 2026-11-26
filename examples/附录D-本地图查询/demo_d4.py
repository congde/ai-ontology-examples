import json
from pathlib import Path

from semantica.provenance import ProvenanceManager, verify_checksum

# 读回上一节的决定编号和原始来源指针
record = json.loads(Path("ticket-context.json").read_text(encoding="utf-8"))
manager = ProvenanceManager()
entries = []
for item in record["sources"]:
    entry = manager.track_entity(
        entity_id=item["entity_id"],
        source=item["document"],
        source_location=item["location"],
        source_quote=item["quote"],
    )
    assert verify_checksum(entry)
    entries.append(entry.to_dict())

# 导出同一决定与两份来源记录的关联
output = Path("ticket-source.json")
export = {"decision_id": record["decision_id"],
          "outcome": record["outcome"], "source_version": record["source_version"],
          "sources": entries}
output.write_text(
    json.dumps(export, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
print(output.name, export["decision_id"])
