from delivery_check import ROWS, delivery_status

scope = "本次汇总"
zero = ROWS[:2] + [("accepted", "终端行", "台", scope, 0, "验收汇总")]
over = ROWS[:2] + [("accepted", "终端行", "台", scope, 13, "验收汇总")]
other = ROWS[:2] + [("accepted", "终端行", "台", "其他批", 10, "验收汇总")]
cases = [
    ("正常", ROWS, (10, 2, 8)),
    ("明确无验收", zero, (20, 12, 8)),
    ("缺少验收", ROWS[:2], "材料未取全，不计算"),
    ("数量倒挂", over, "数量与本次核查条件矛盾"),
    ("两份到货汇总", ROWS + [ROWS[1]], "同类汇总重复，先核对采用版本"),
    ("范围串用", other, "材料范围不一致"),
]
for name, rows, expected in cases:
    try:
        result = delivery_status(rows, scope)
        actual = (result["unaccepted"], result["waiting"], result["not_arrived"])
    except ValueError as exc:
        actual = str(exc)
    if actual != expected:
        raise AssertionError(f"{name}：预期 {expected!r}，实际 {actual!r}")
    if isinstance(actual, tuple):
        print(name, *actual)
    else:
        print(name, actual)
