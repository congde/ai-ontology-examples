import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TICKET_FIELDS = {"单号", "客户号", "设备号", "事项", "优先级", "创建日期", "处理状态"}
DEVICE_FIELDS = {"设备号", "型号", "部署客户", "运行状态"}
NORMALIZED_CATEGORY = ("T-004", "事项", "O-005逾期付款的催付", "催付")
MODE_LABELS = {"four": "四单", "open": "五单处理中", "completed": "五单已完成"}
UNKNOWN = ["T-001本单处理结论", "T-001与T-003是否承接"]
FIELD_PATTERNS = {
    "单号": (r"(T-\d{3})",),
    "客户号": (r"(C-\d{3})",),
    "设备号": (r"(E-\d{3})",),
    "事项": (r"事项为([^，；。]+)", r"处理([^，；。]+)，优先级", r"(设备故障|资料补充)工单"),
    "优先级": (r"优先级([高中低])", r"([高中低])优先级"),
    "创建日期": (r"(\d{4}-\d{2}-\d{2})创建",),
    "处理状态": (r"当前([^，；。]+)",),
    "型号": (r"型号为([^，；。]+)",),
    "部署客户": (r"部署于客户(C-\d{3})",),
    "运行状态": (r"台账状态为([^，；。]+)",),
}


def read_json(file):
    return json.loads(file.read_text(encoding="utf-8-sig"))


def reading_value(item, field, text):
    if field == "设备号" and "未关联设备" in text:
        return ""
    for pattern in FIELD_PATTERNS[field]:
        match = re.search(pattern, text)
        if match:
            return match[1]
    raise ValueError(f"{item}的{field}无法从本练习规定的写法定位。请返回原文核对")


def check_review(sources, review_file, definition):
    source_by_id = {locator.split("/", 1)[1]: locator for locator in sources}
    expected = {
        (item, field)
        for item, locator in source_by_id.items()
        for field in (DEVICE_FIELDS if locator.startswith("乙/") else TICKET_FIELDS)
    }
    adopted = {item: {"依据": {}} for item in source_by_id}
    with review_file.open(encoding="utf-8-sig", newline="") as stream:
        checks = list(csv.DictReader(stream))
    remaining = expected.copy()
    for check in checks:
        item, field = check["对象"], check["字段"]
        if (item, field) not in remaining:
            raise ValueError(f"未知或重复审核项：{item}的{field}")
        remaining.remove((item, field))
        where = source_by_id[item]
        pointers = check["来源"].split("；")
        if item == "T-003" and field in {"客户号", "设备号"}:
            if pointers != [where, "甲/T-001"] or "客户和设备与T-001相同" not in sources[where]:
                raise ValueError(f"{item}的{field}须同时引用本单和被指代工单")
        elif pointers != [where]:
            raise ValueError(f"{item}的{field}须引用本对象原文")
        candidate, value = check["候选值"], check["采用值"]
        if not check["理由"].strip():
            raise ValueError(f"{item}的{field}缺审核理由")
        decision = check["决定"]
        evidenced = reading_value(item, field, sources[pointers[-1]])
        if decision == "采用原值":
            if value != candidate:
                raise ValueError(f"{item}的{field}标为采用原值，但采用值改变")
            if value != evidenced:
                raise ValueError(f"{item}的{field}采用值与该字段的原文不符：{evidenced or '明确未关联'}")
        elif decision == "类别归一":
            if (item, field, evidenced, value) != NORMALIZED_CATEGORY or candidate != evidenced:
                raise ValueError(f"{item}的{field}不符合本例约定的类别归一")
        elif decision == "纠正候选":
            if candidate == value or value != evidenced:
                raise ValueError(f"{item}的{field}应保留与原文不符的候选，并采用原文支持的值")
        else:
            raise ValueError(f"{item}的{field}缺可采用的决定")
        if field == "处理状态" and value not in definition["valid_statuses"]:
            raise ValueError(f"{item}状态不在本例所用定义范围")
        if field == "单号" and value != item:
            raise ValueError(f"{item}的单号与对象标识不符")
        adopted[item][field] = value or None
        adopted[item]["依据"][field] = pointers
    if remaining:
        keys = "、".join(f"{item}/{field}" for item, field in sorted(remaining))
        raise ValueError(f"有{len(remaining)}项审核未完成：{keys}")
    return adopted, len(expected)


def check_query(adopted, request, definition):
    expected = {
        "name": definition["tool"],
        "model_ref": definition["model_ref"],
        "arguments": {
            "customer": definition["customer"],
            "statuses": definition["unfinished_statuses"],
        },
    }
    if not isinstance(request, dict):
        raise ValueError("查询请求须为包含工具名、定义和参数的对象")
    args = request.get("arguments", {})
    statuses = args.get("statuses", []) if isinstance(args, dict) else []
    if (not isinstance(statuses, list) or sorted(statuses) != sorted(expected["arguments"]["statuses"])):
        raise ValueError("请求必须列全本次采用的未完成状态")
    normalized = {**request, "arguments": {**args, "statuses": expected["arguments"]["statuses"]}}
    if normalized != expected:
        raise ValueError("请求的工具、定义或客户范围与练习要求不符")
    tickets = [
        adopted[item] for item in sorted(adopted)
        if "单号" in adopted[item]
        and adopted[item]["客户号"] == args["customer"]
        and adopted[item]["处理状态"] in statuses
    ]
    devices = {}
    for ticket in tickets:
        item = ticket["设备号"]
        if item is None:
            continue
        record = adopted.get(item)
        if not record or record.get("部署客户") != ticket["客户号"]:
            raise ValueError(f"{ticket['单号']}的设备资料未取得或不在本客户范围")
        devices[item] = record
    return {"定义": definition["model_ref"], "工单": tickets, "设备": devices, "待核": UNKNOWN}


def handover(result):
    tickets = result["工单"]
    lines = ["# 华北机械未完成工单交班", "", f"本次教学范围内共 {len(tickets)} 单。定义 {result['定义']}。", ""]
    for ticket in tickets:
        item = ticket["单号"]
        status = ticket["处理状态"]
        status_source = "、".join(ticket["依据"]["处理状态"])
        device = ticket["设备号"] or "原文明确未关联"
        device_source = "、".join(ticket["依据"]["设备号"])
        lines.append(f"- {item}，{ticket['事项']}，{ticket['优先级']}优先级，{status}（{status_source}）。设备关联：{device}（{device_source}）。")
    for item, device in result["设备"].items():
        location = "、".join(device["依据"]["运行状态"])
        lines.append(f"- 设备台账另记 {item}（{device['型号']}）{device['运行状态']}（{location}）。")
    lines.extend(["", "请有权接班岗位分别核实：" + "、".join(result["待核"]) + "。", "",
                  "本次为本地教学重建。无模型调用、企业查询或业务变更。"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="重做书中工单查询。所有材料均为教学数据。")
    parser.add_argument("case", choices=MODE_LABELS)
    parser.add_argument("--output", required=True, type=Path, help="本次新的输出目录")
    parser.add_argument("--review", type=Path, help="用修改过的审核副本复测")
    parser.add_argument("--request", type=Path, help="用修改过的查询请求复测")
    args = parser.parse_args()
    case = ROOT / MODE_LABELS[args.case]
    source_file = case / "原文.json"
    review_file = args.review or case / "审核.csv"
    definition_file = ROOT / "业务定义.json"
    request_file = args.request or ROOT / "查询请求.json"
    try:
        definition = read_json(definition_file)
        adopted, count = check_review(read_json(source_file), review_file, definition)
        result = check_query(adopted, read_json(request_file), definition)
        text = handover(result)
        input_files = {
            "原文": source_file,
            "审核": review_file,
            "业务定义": definition_file,
            "查询请求": request_file,
        }
        name_counts = Counter(file.name for file in input_files.values())
        inputs = {}
        for role, file in input_files.items():
            key = file.name if name_counts[file.name] == 1 else f"{role}/{file.name}"
            inputs[key] = hashlib.sha256(file.read_bytes()).hexdigest()
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "query-result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (args.output / "handover.md").write_text(text, encoding="utf-8")
        (args.output / "run.json").write_text(
            json.dumps({"模式": "教学重建", "审核项数": count, "模型调用": 0, "输入SHA-256": inputs},
                       ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"未完成：{exc}\n")
    print(f"{count}项审核，入选：{'、'.join(ticket['单号'] for ticket in result['工单'])}。")


if __name__ == "__main__":
    main()
