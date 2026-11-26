MODEL = {
    "line": "终端行",
    "unit": "台",
    "fields": {
        "ordered": "订单行",
        "arrived": "到货汇总",
        "accepted": "验收汇总",
    },
}
ROWS = [
    ("ordered", "终端行", "台", "本次汇总", 20, "订单行"),
    ("arrived", "终端行", "台", "本次汇总", 12, "到货汇总"),
    ("accepted", "终端行", "台", "本次汇总", 10, "验收汇总"),
]

def read_quantities(rows, scope):
    values, sources = {}, {}
    for key, line, unit, batch, qty, basis in rows:
        if line != MODEL["line"] or unit != MODEL["unit"]:
            raise ValueError("订单行或单位不符")
        if batch != scope:
            raise ValueError("材料范围不一致")
        if key not in MODEL["fields"] or basis != MODEL["fields"][key]:
            raise ValueError("字段或来源不符")
        if key in values:
            raise ValueError("同类汇总重复，先核对采用版本")
        if type(qty) is not int or qty < 0:
            raise ValueError("数量必须是非负整数")
        values[key], sources[key] = qty, basis
    if values.keys() != MODEL["fields"].keys():
        raise ValueError("材料未取全，不计算")
    return values, sources

def delivery_status(rows, scope):
    values, sources = read_quantities(rows, scope)
    ordered = values["ordered"]
    arrived = values["arrived"]
    accepted = values["accepted"]
    if not 0 <= accepted <= arrived <= ordered:
        raise ValueError("数量与本次核查条件矛盾")
    return {
        "unaccepted": ordered - accepted,
        "waiting": arrived - accepted,
        "not_arrived": ordered - arrived,
        "sources": sources,
    }


if __name__ == "__main__":
    print(delivery_status(ROWS, "本次汇总"))
