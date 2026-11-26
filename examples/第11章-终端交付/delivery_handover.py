import json
from pathlib import Path
from delivery_check import ROWS, delivery_status, read_quantities

scope = "海辰商贸／终端行"
keys = ("unaccepted", "waiting", "not_arrived")

def check(candidate, expected):
    if set(candidate) != set(expected) | {"eta"}:
        return "退回：字段范围不符"
    for key in ("scope", "batch"):
        if candidate[key] != expected[key]:
            return "退回：对象或批次不符"
    for key in keys:
        if type(candidate[key]) is not int or candidate[key] != expected[key]:
            return "退回：数量或分类不符"
    if candidate["eta"] is not None:
        return "退回：没有到货日期依据"
    return (
        f"{expected['scope']}（{expected['batch']}）："
        f"未验收{expected['unaccepted']}台，其中"
        f"{expected['waiting']}台到货待验收，"
        f"{expected['not_arrived']}台尚未到货。"
    )

def review_candidates(result, batch):
    expected = {key: result[key] for key in keys}
    expected.update(scope=scope, batch=batch)
    good = dict(expected, eta=None)
    extra = max(1, result["not_arrived"])
    candidates = [
        ("正常", good),
        ("分错类", dict(good, waiting=good["waiting"] + extra, not_arrived=0)),
        ("补了日期", dict(good, eta="明天")),
        ("旧批次", dict(good, batch="上次汇总")),
        ("未约定备注", dict(good, note="已全部发运")),
    ]
    review = []
    for name, candidate in candidates:
        message = check(candidate, expected)
        review.append({"case": name, "candidate": candidate, "result": message})
    return review

def follow_up(result, quantities):
    tasks = []
    if result["waiting"] > 0:
        tasks.append(f"请验收方确认{result['waiting']}台的验收安排")
    if result["not_arrived"] > 0:
        tasks.append(f"请交付方核实{result['not_arrived']}台的到货或发运安排")
    if tasks:
        return "待核：" + "；".join(tasks) + "。目前没有日期依据。"
    if quantities["ordered"] == 0:
        return "本批订购0台，无需跟进到货或验收。"
    return f"本批{quantities['accepted']}台已全部验收。"

def write_handover(rows, batch, folder):
    result = delivery_status(rows, batch)
    quantities, sources = read_quantities(rows, batch)
    review = review_candidates(result, batch)
    audit = {"scope": scope, "batch": batch, "quantities": quantities,
             "tool_result": result, "review": review}
    folder.mkdir()
    (folder / "candidate-review.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    accepted = review[0]["result"]
    if not accepted.startswith("退回："):
        basis = "；".join(f"{sources[key]}：{quantities[key]}台"
                         for key in ("ordered", "arrived", "accepted"))
        body = ("# 终端交付交班（教学示例）\n\n" + accepted + "\n\n"
                "数量依据：" + basis + "。\n\n"
                + follow_up(result, quantities) + "\n")
        (folder / "handover.md").write_text(body, encoding="utf-8")
    return review


if __name__ == "__main__":
    folder = Path("delivery-handover-output")
    for item in write_handover(ROWS, "本次汇总", folder):
        print(item["case"], item["result"])
