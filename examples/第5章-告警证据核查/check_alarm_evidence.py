def has_confirmed_conclusion(alert_id, conclusion):
    return (
        conclusion is not None
        and conclusion.get("alert_id") == alert_id
        and conclusion.get("confirmed") is True
    )


device_kind = "数控加工中心"
direct_parent = {"数控加工中心": "设备"}
assert direct_parent[device_kind] == "设备"

assert not has_confirmed_conclusion("A-001", None)
assert not has_confirmed_conclusion(
    "A-001", {"alert_id": "A-002", "confirmed": True}
)
assert not has_confirmed_conclusion(
    "A-001", {"alert_id": "A-001", "confirmed": False}
)
assert has_confirmed_conclusion(
    "A-001", {"alert_id": "A-001", "confirmed": True}
)
print("设备类型和告警结论的四种检查通过")
