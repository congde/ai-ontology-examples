tickets = [
    ("T-001", "C-001", "处理中", "E-001", ("甲/T-001",)),
    ("T-002", "C-002", "已完成", "E-002", ("甲/T-002",)),
    ("T-003", "C-001", "待派工", "E-001", ("甲/T-003", "甲/T-001")),
    ("T-004", "C-003", "已完成", None, ("甲/T-004",)),
]
unfinished = {"处理中", "待派工"}

def select(rows, customer):
    return [row for row in rows if row[1] == customer and row[2] in unfinished]

selected = select(tickets, "C-001")
assert [row[0] for row in selected] == ["T-001", "T-003"]
for number, customer, state, equipment, refs in selected:
    print(number, state, equipment or "未列设备", "、".join(refs))

test_copy = list(tickets)
test_copy[2] = ("T-003", "C-001", "已完成", "E-001", ("测试副本",))
assert [row[0] for row in select(test_copy, "C-001")] == ["T-001"]
