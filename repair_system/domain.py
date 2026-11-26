"""Data, access rules and evidence for the simulated repair workflow."""

from hashlib import sha256
import json
from pathlib import Path
import re


class DomainError(ValueError):
    """The request or input violates a business rule."""


ROLE_OPERATIONS = {
    "operator": {"read", "propose", "receipt"},
    "supervisor": {"read", "approve", "receipt"},
    "executor": {"read", "submit", "receipt"},
    "auditor": {"read", "audit", "receipt"},
}

RECORD_FIELDS = {
    "alarms": ("alarm_id", "device_id", "name", "time", "source"),
    "observations": ("device_id", "state", "time", "source"),
    "repair_results": ("alarm_id", "device_id", "conclusion", "time", "source"),
}


def load_scenario(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name("scenario.json")
    try:
        scenario = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise DomainError(f"无法读取场景文件 {path}: {error}") from error

    version = scenario.get("rule_version") if isinstance(scenario, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise DomainError("场景必须给出业务规则版本")
    actors = scenario.get("actors")
    if not isinstance(actors, dict):
        raise DomainError("场景必须给出角色和设备授权范围")
    for actor, entry in actors.items():
        role = entry.get("role") if isinstance(entry, dict) else None
        if (not isinstance(role, str) or role not in ROLE_OPERATIONS
                or not isinstance(entry.get("device_ids"), list)
                or not all(isinstance(item, str) for item in entry["device_ids"])):
            raise DomainError(f"账号 {actor} 的角色或设备范围不符合场景约定")
    for name, fields in RECORD_FIELDS.items():
        rows = scenario.get(name)
        if not isinstance(rows, list):
            raise DomainError(f"场景记录 {name} 应为列表")
        for row in rows:
            if (not isinstance(row, dict)
                    or not all(isinstance(row.get(field), str) and row[field] for field in fields)
                    or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", row["time"])):
                raise DomainError(f"场景记录 {name} 缺少字段或时点格式有误")
    alarms = {row["alarm_id"]: row["device_id"] for row in scenario["alarms"]}
    if len(alarms) != len(scenario["alarms"]):
        raise DomainError("同一告警编号在场景中只能出现一次")
    for result in scenario["repair_results"]:
        if alarms.get(result["alarm_id"]) != result["device_id"]:
            raise DomainError("维修结论必须能核对到原告警与设备")
    return scenario


def authorize(scenario, actor, operation, device_id=None):
    """Check the simulated actor's role and, when supplied, the device scope."""
    assignment = scenario["actors"].get(actor)
    if assignment is None or operation not in ROLE_OPERATIONS[assignment["role"]]:
        raise DomainError(f"账号 {actor} 无权执行 {operation}")
    if device_id is not None and device_id not in assignment["device_ids"]:
        raise DomainError(f"账号 {actor} 无权访问设备 {device_id}")


def validate_proposal(proposal, alarm_id):
    expected = {"tool": "read_evidence", "alarm_id": alarm_id}
    if not isinstance(proposal, dict) or proposal != expected:
        raise DomainError("模型提议须使用获准的只读工具和本次告警编号")
    return proposal


def read_evidence(scenario, alarm_id, actor):
    authorize(scenario, actor, "read")
    alarm = next((row for row in scenario["alarms"] if row["alarm_id"] == alarm_id), None)
    if alarm is None:
        raise DomainError("未找到可访问的告警")
    device_id = alarm["device_id"]
    try:
        authorize(scenario, actor, "read", device_id)
    except DomainError:
        raise DomainError("未找到可访问的告警") from None

    observation = max(
        (row for row in scenario["observations"] if row["device_id"] == device_id),
        key=lambda row: row["time"], default=None,
    )
    repair_result = max(
        (row for row in scenario["repair_results"]
         if row["alarm_id"] == alarm_id and row["device_id"] == device_id),
        key=lambda row: row["time"], default=None,
    )
    return {
        "device_id": device_id,
        "alarm": dict(alarm),
        "observation": dict(observation) if observation is not None else None,
        "repair_result": dict(repair_result) if repair_result is not None else None,
        "rule_version": scenario["rule_version"],
    }


def evidence_fingerprint(evidence):
    canonical = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()
