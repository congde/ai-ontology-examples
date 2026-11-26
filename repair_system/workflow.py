import json
import re
import sqlite3
from contextlib import closing, contextmanager

from .domain import DomainError, authorize, evidence_fingerprint, read_evidence, validate_proposal


APPLICATION_ID = 0x41524D54
SCHEMA_VERSION = 1
SCHEMA = (
    """
CREATE TABLE IF NOT EXISTS requests (
    number INTEGER PRIMARY KEY,
    alarm_id TEXT UNIQUE NOT NULL,
    device_id TEXT NOT NULL,
    evidence TEXT NOT NULL,
    approved_fingerprint TEXT,
    approver TEXT,
    CHECK ((approved_fingerprint IS NULL) = (approver IS NULL))
)
""",
    """
CREATE TABLE IF NOT EXISTS work_orders (
    number INTEGER PRIMARY KEY,
    request_number INTEGER UNIQUE NOT NULL REFERENCES requests(number),
    status TEXT NOT NULL
)
""",
    """
CREATE TABLE IF NOT EXISTS events (
    number INTEGER PRIMARY KEY,
    request_number INTEGER NOT NULL REFERENCES requests(number),
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    event TEXT NOT NULL,
    actor TEXT NOT NULL,
    detail TEXT NOT NULL
)
""",
)


class ReceiptUnknown(RuntimeError):
    """The simulated receiver committed the request, but the reply did not arrive."""

    def __init__(self, request_id):
        self.request_id = request_id
        super().__init__(f"{request_id} 提交响应超时，请按原申请号反查")


def _serialize(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _identifier(prefix, number):
    return f"{prefix}-{number:03d}"


class Workflow:
    def __init__(self, db_path, scenario):
        self.db_path = db_path
        self.scenario = scenario
        with self._transaction(write=True) as db:
            app_id = db.execute("PRAGMA application_id").fetchone()[0]
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if app_id == APPLICATION_ID and version == SCHEMA_VERSION:
                return
            existing = db.execute(
                "SELECT 1 FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
            ).fetchone()
            if app_id or version or existing is not None:
                raise DomainError("该数据库不适用于此工作流，请选择新的 SQLite 文件")
            for statement in SCHEMA:
                db.execute(statement)
            db.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @contextmanager
    def _transaction(self, write=False):
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db

    def _request(self, db, actor, operation, request_id):
        match = re.fullmatch(r"R-([0-9]{3,18})", request_id)
        if not match or _identifier("R", int(match[1])) != request_id:
            raise DomainError("无效的申请号")
        request = db.execute(
            "SELECT * FROM requests WHERE number = ?", (int(match[1]),)
        ).fetchone()
        if request is None:
            raise DomainError("未找到可访问的申请")
        try:
            authorize(self.scenario, actor, operation, request["device_id"])
        except DomainError:
            raise DomainError("未找到可访问的申请") from None
        return request

    @staticmethod
    def _receipt(db, request):
        order = db.execute(
            "SELECT number, status FROM work_orders WHERE request_number = ?",
            (request["number"],),
        ).fetchone()
        if order is None:
            return None
        return {
            "request_id": _identifier("R", request["number"]),
            "work_order_id": _identifier("W", order["number"]),
            "status": order["status"],
            "result": "已创建",
        }

    @staticmethod
    def _event(db, request_number, event, actor, **detail):
        db.execute(
            "INSERT INTO events (request_number, event, actor, detail) VALUES (?, ?, ?, ?)",
            (request_number, event, actor, _serialize(detail)),
        )

    def _verify_evidence(self, request, actor):
        evidence = read_evidence(self.scenario, request["alarm_id"], actor)
        if _serialize(evidence) != request["evidence"]:
            raise DomainError("证据已变化，请重新提出草案并审批")
        return evidence_fingerprint(evidence)

    def propose(self, actor, alarm_id, proposal):
        authorize(self.scenario, actor, "propose")
        validate_proposal(proposal, alarm_id)
        evidence = read_evidence(self.scenario, alarm_id, actor)
        device_id = evidence["device_id"]
        authorize(self.scenario, actor, "propose", device_id)
        snapshot = _serialize(evidence)
        status = "待审批"
        with self._transaction(write=True) as db:
            request = db.execute("SELECT * FROM requests WHERE alarm_id = ?", (alarm_id,)).fetchone()
            if request is None:
                if evidence["repair_result"] is not None:
                    raise DomainError("本次告警已有维修结论，请由业务岗位核实后续安排")
                cursor = db.execute(
                    "INSERT INTO requests (alarm_id, device_id, evidence) VALUES (?, ?, ?)",
                    (alarm_id, device_id, snapshot),
                )
                number = cursor.lastrowid
                self._event(db, number, "draft_created", actor, evidence=evidence)
            else:
                number = request["number"]
                authorize(self.scenario, actor, "propose", request["device_id"])
                if request["device_id"] != device_id:
                    raise DomainError("告警关联的设备已变化，请由业务岗位核实")
                if self._receipt(db, request) is not None:
                    status = "已创建"
                    evidence = json.loads(request["evidence"])
                elif evidence["repair_result"] is not None:
                    raise DomainError("本次告警已有维修结论，请由业务岗位核实后续安排")
                elif request["evidence"] != snapshot:
                    db.execute(
                        """UPDATE requests SET evidence = ?,
                           approved_fingerprint = NULL, approver = NULL WHERE number = ?""",
                        (snapshot, number),
                    )
                    self._event(db, number, "evidence_updated", actor, evidence=evidence)
                elif request["approver"] is not None:
                    status = "已批准"
        return {"request_id": _identifier("R", number), "status": status, "evidence": evidence}

    def approve(self, actor, request_id):
        authorize(self.scenario, actor, "approve")
        status = "已批准"
        with self._transaction(write=True) as db:
            request = self._request(db, actor, "approve", request_id)
            if self._receipt(db, request) is not None:
                status = "已创建"
            else:
                fingerprint = self._verify_evidence(request, actor)
                if request["approver"] != actor or request["approved_fingerprint"] != fingerprint:
                    db.execute(
                        "UPDATE requests SET approved_fingerprint = ?, approver = ? WHERE number = ?",
                        (fingerprint, actor, request["number"]),
                    )
                    self._event(db, request["number"], "approved", actor,
                                evidence_fingerprint=fingerprint)
        return {"request_id": request_id, "status": status}

    def submit(self, actor, request_id, *, simulate_timeout=False):
        authorize(self.scenario, actor, "submit")
        with self._transaction(write=True) as db:
            request = self._request(db, actor, "submit", request_id)
            receipt = self._receipt(db, request)
            if receipt is None:
                if request["approver"] is None:
                    raise DomainError("申请尚未审批")
                authorize(self.scenario, request["approver"], "approve", request["device_id"])
                fingerprint = self._verify_evidence(request, actor)
                if fingerprint != request["approved_fingerprint"]:
                    raise DomainError("批准的证据版本与本次提交不一致")
                db.execute(
                    "INSERT INTO work_orders (request_number, status) VALUES (?, ?)",
                    (request["number"], "待派工"),
                )
                receipt = self._receipt(db, request)
                self._event(db, request["number"], "order_created", actor, **receipt)
            if simulate_timeout:
                self._event(db, request["number"], "response_lost", actor)
        if simulate_timeout:
            raise ReceiptUnknown(request_id)
        return receipt

    def receipt(self, actor, request_id):
        authorize(self.scenario, actor, "receipt")
        with self._transaction() as db:
            request = self._request(db, actor, "receipt", request_id)
            return self._receipt(db, request) or {
                "request_id": request_id,
                "status": "尚无工单回执",
            }

    def history(self, actor, request_id):
        authorize(self.scenario, actor, "audit")
        with self._transaction() as db:
            request = self._request(db, actor, "audit", request_id)
            rows = db.execute(
                """SELECT event, actor, recorded_at, detail FROM events
                   WHERE request_number = ? ORDER BY number""",
                (request["number"],),
            ).fetchall()
        return [dict(row, detail=json.loads(row["detail"])) for row in rows]

    def metrics(self, actor):
        authorize(self.scenario, actor, "audit")
        counts = {"requests": 0, "approved": 0, "created": 0}
        with self._transaction() as db:
            rows = db.execute(
                """SELECT r.device_id, r.approver, w.number AS order_number
                   FROM requests r LEFT JOIN work_orders w ON w.request_number = r.number"""
            )
            for row in rows:
                try:
                    authorize(self.scenario, actor, "audit", row["device_id"])
                except DomainError:
                    continue
                counts["requests"] += 1
                counts["approved"] += row["approver"] is not None
                counts["created"] += row["order_number"] is not None
        counts["creation_rate"] = counts["created"] / counts["requests"] if counts["requests"] else None
        return counts
