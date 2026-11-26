import csv
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent / "工单查询与交班" / "四单" / "审核.csv"
OLD = ("规则1", {"处理中", "待派工", "已完成"}, {"处理中", "待派工"})
NEW = ("规则2", OLD[1] | {"待验收"}, OLD[2] | {"待验收"})


def classify(status, rules):
    _, allowed, unfinished = rules
    if status not in allowed:
        return "未识别状态，判断待核"
    return "纳入未完成" if status in unfinished else "不纳入未完成"


def evaluate(case, list_rules, card_rules):
    listed = "、".join(
        item for item, record in sorted(case.items())
        if record["客户号"] == "C-001" and classify(record["处理状态"], list_rules) == "纳入未完成"
    )
    ticket = case["T-003"]
    status = ticket["处理状态"]
    equipment = ticket["设备号"] or "未关联设备"
    card = f"{ticket['客户号']}；{equipment}；{status}；{classify(status, card_rules)}"
    return listed, card


def render():
    tickets = {}
    with CASE.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["对象"].startswith("T-") and row["字段"] in {"客户号", "设备号", "处理状态"}:
                tickets.setdefault(row["对象"], {})[row["字段"]] = row["采用值"]
    changed = {item: record.copy() for item, record in tickets.items()}
    changed["T-003"]["处理状态"] = "待验收"
    scenarios = [
        ("分别维护旧规则，变更前", tickets, OLD, OLD),
        ("只更新清单入口", changed, NEW, OLD),
        ("两个入口分别同步", changed, NEW, NEW),
        ("共用定义已发新版，卡片仍读旧版", changed, NEW, OLD),
        ("两个入口均使用共用定义新版", changed, NEW, NEW),
        ("两个入口均调用已更新的共用函数", changed, NEW, NEW),
    ]
    print("| 教学条件 | 清单实际规则 | 卡片实际规则 | 清单 | T-003交班卡 |")
    print("| --- | --- | --- | --- | --- |")
    for label, case, list_rules, card_rules in scenarios:
        tickets_in_scope, card = evaluate(case, list_rules, card_rules)
        print(f"| {label} | {list_rules[0]} | {card_rules[0]} | {tickets_in_scope} | {card} |")


if __name__ == "__main__":
    render()
