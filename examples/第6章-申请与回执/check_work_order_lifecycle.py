orders_by_request = {}


def create_order(request_id, alert_id, approved_request, authorized):
    if not authorized or approved_request != (request_id, alert_id):
        return None
    existing = orders_by_request.get(request_id)
    if existing is not None:
        if existing["alert_id"] != alert_id:
            return None
        return existing
    receipt = {
        "alert_id": alert_id,
        "work_order_id": f"W-{len(orders_by_request) + 1:03d}",
        "status": "待派工",
    }
    orders_by_request[request_id] = receipt
    return receipt


approved = ("R-001", "A-001")
assert create_order("R-001", "A-001", None, True) is None
assert create_order("R-001", "A-001", approved, False) is None
assert len(orders_by_request) == 0

first = create_order("R-001", "A-001", approved, True)
assert first["work_order_id"] == "W-001" and first["status"] == "待派工"
assert orders_by_request["R-001"] == first
assert create_order("R-001", "A-001", approved, True) == first
assert create_order("R-001", "A-002", ("R-001", "A-002"), True) is None
assert len(orders_by_request) == 1
print("批准、写入、反查、重试和冲突检查通过")
