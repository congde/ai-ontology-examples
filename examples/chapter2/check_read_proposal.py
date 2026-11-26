def admits_read(proposal, selected_alert, readable_alerts):
    tool, alert = proposal
    return (
        tool == "read_evidence"
        and alert == selected_alert
        and alert in readable_alerts
    )


current_alert = "A-001"
readable = {"A-001", "A-002"}
assert admits_read(("read_evidence", "A-001"), current_alert, readable)
assert not admits_read(("read_evidence", "A-002"), current_alert, readable)
assert not admits_read(("create_work_order", "A-001"), current_alert, readable)
assert not admits_read(("read_evidence", "A-001"), current_alert, set())
print("四项查询边界检查通过")
