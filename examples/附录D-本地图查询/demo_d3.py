import json
from pathlib import Path

from semantica.context import ContextGraph

# 将两份教学记录按各自身份入图
graph = ContextGraph(advanced_analytics=False, node_embeddings=False)
sources = [
    {"entity_id": "T-001", "type": "ticket", "label": "设备故障单，处理中",
     "document": "智造集团教学工单清单", "location": "T-001 行",
     "quote": ("| T-001 | C-001 | E-001（CNC-500） | 设备故障 | 高 |"
               " 2025-01-08 | 处理中 |")},
    {"entity_id": "E-001", "type": "equipment", "label": "设备台账，运行中（曾故障）",
     "document": "智造集团教学设备台账", "location": "E-001 行",
     "quote": ("| E-001 | CNC-500 | 数控加工中心 | C-001（华北机械） |"
               " T-001, T-003 | 运行中（曾故障） |")},
]
for item in sources:
    graph.add_node(item["entity_id"], item["type"], item["label"])
graph.add_edge("T-001", "E-001", "affectsEquipment")

# 记录审核决定和它所依据的来源，供溯源步骤读回
outcome = "留在未完成清单并请有权人复核"
decision_id = graph.record_decision(
    category="handover",
    scenario="是否从未完成交班中移除故障单",
    reasoning="设备有运行观测，工单缺本次处理结论",
    outcome=outcome,
    confidence=1.0,
    entities=["T-001", "E-001"],
    decision_maker="teaching-reviewer",
)
assert decision_id
record = {"decision_id": decision_id, "outcome": outcome,
          "source_version": "教学样本v1.1", "sources": sources}
Path("ticket-context.json").write_text(
    json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("已记录教学决定", decision_id)
