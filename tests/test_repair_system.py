from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from repair_system.domain import DomainError, load_scenario, read_evidence
from repair_system.workflow import ReceiptUnknown, Workflow


CASE = "A-001"
RECEIPT = {"request_id": "R-001", "work_order_id": "W-001", "status": "待派工", "result": "已创建"}
ROOT = Path(__file__).resolve().parents[1]


def proposal(alarm_id=CASE):
    return {"tool": "read_evidence", "alarm_id": alarm_id}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.db_path = Path(temporary.name) / "workflow.sqlite3"
        self.scenario = load_scenario()
        self.workflow = Workflow(self.db_path, self.scenario)

    def draft(self):
        return self.workflow.propose("operator", CASE, proposal())["request_id"]

    def test_observation_and_repair_outcome_are_separate(self):
        evidence = read_evidence(self.scenario, CASE, "operator")
        self.assertEqual(evidence["observation"]["state"], "运行中")
        self.assertIsNone(evidence["repair_result"])
        historical = read_evidence(self.scenario, "A-000", "operator")
        self.assertEqual(historical["device_id"], evidence["device_id"])
        self.assertEqual(historical["repair_result"]["alarm_id"], "A-000")
        with self.assertRaisesRegex(DomainError, "已有维修结论"):
            self.workflow.propose("operator", "A-000", proposal("A-000"))

    def test_model_can_only_suggest_scoped_read(self):
        inputs = [
            {"tool": "create_work_order", "alarm_id": CASE},
            proposal("A-002"),
            {**proposal(), "approved": True},
        ]
        for candidate in inputs:
            with self.subTest(candidate=candidate), self.assertRaises(DomainError):
                self.workflow.propose("operator", CASE, candidate)
        self.assertEqual(self.workflow.metrics("auditor")["requests"], 0)

    def test_submission_timeout_receipt_and_retries(self):
        request_id = self.draft()
        self.assertEqual(request_id, "R-001")
        self.assertEqual(self.workflow.receipt("operator", request_id)["status"], "尚无工单回执")
        with self.assertRaisesRegex(DomainError, "尚未审批"):
            self.workflow.submit("executor", request_id)
        with self.assertRaises(DomainError):
            self.workflow.approve("operator", request_id)
        self.workflow.approve("supervisor", request_id)
        self.assertEqual(self.workflow.receipt("operator", request_id)["status"], "尚无工单回执")
        with self.assertRaises(ReceiptUnknown):
            self.workflow.submit("executor", request_id, simulate_timeout=True)
        restarted = Workflow(self.db_path, load_scenario())
        self.assertEqual(restarted.receipt("operator", request_id), RECEIPT)
        self.assertEqual(restarted.submit("executor", request_id), RECEIPT)
        self.assertEqual(restarted.metrics("auditor")["created"], 1)
        self.assertEqual(
            [event["event"] for event in restarted.history("auditor", request_id)],
            ["draft_created", "approved", "order_created", "response_lost"],
        )

    def test_snapshot_change_requires_new_approval(self):
        request_id = self.draft()
        self.workflow.approve("supervisor", request_id)
        changed = load_scenario()
        changed["rule_version"] = "repair-v2"
        changed_workflow = Workflow(self.db_path, changed)
        with self.assertRaisesRegex(DomainError, "证据已变化"):
            changed_workflow.submit("executor", request_id)
        updated = changed_workflow.propose("operator", CASE, proposal())
        self.assertEqual((updated["request_id"], updated["status"]), (request_id, "待审批"))
        with self.assertRaisesRegex(DomainError, "尚未审批"):
            changed_workflow.submit("executor", request_id)
        changed_workflow.approve("supervisor", request_id)
        self.assertEqual(changed_workflow.submit("executor", request_id), RECEIPT)

    def test_revoke_approval_role_before_execution(self):
        request_id = self.draft()
        self.workflow.approve("supervisor", request_id)
        changed = load_scenario()
        changed["actors"]["supervisor"]["device_ids"] = []
        changed_workflow = Workflow(self.db_path, changed)
        with self.assertRaises(DomainError):
            changed_workflow.submit("executor", request_id)
        self.assertEqual(changed_workflow.receipt("operator", request_id)["status"], "尚无工单回执")

    def test_audit_and_receipts_stay_within_asset_scope(self):
        first = self.draft()
        second = self.workflow.propose("other", "A-002", proposal("A-002"))["request_id"]
        self.assertNotEqual(first, second)
        with self.assertRaisesRegex(DomainError, "^未找到可访问的告警$"):
            read_evidence(self.scenario, "A-002", "operator")
        with self.assertRaises(DomainError):
            self.workflow.receipt("other", first)
        with self.assertRaises(DomainError):
            self.workflow.history("auditor", second)
        self.assertEqual(
            self.workflow.metrics("auditor"),
            {"requests": 1, "approved": 0, "created": 0, "creation_rate": 0.0},
        )

    def test_concurrent_first_submission_creates_one_work_order(self):
        request_id = self.draft()
        self.workflow.approve("supervisor", request_id)
        with ThreadPoolExecutor(max_workers=8) as workers:
            futures = [
                workers.submit(self.workflow.submit, "executor", request_id) for _ in range(16)
            ]
            self.assertEqual([future.result(timeout=15) for future in futures], [RECEIPT] * 16)
        self.assertEqual(self.workflow.metrics("auditor")["created"], 1)
        history = self.workflow.history("auditor", request_id)
        self.assertEqual(sum(event["event"] == "order_created" for event in history), 1)

    def test_another_database_is_rejected_without_being_modified(self):
        original = self.db_path.with_name("chapter1.sqlite3")
        with closing(sqlite3.connect(original)) as db, db:
            db.execute("CREATE TABLE drafts (request_id TEXT PRIMARY KEY)")
        before = original.read_bytes()
        with self.assertRaisesRegex(DomainError, "请选择新的 SQLite 文件"):
            Workflow(original, self.scenario)
        self.assertEqual(original.read_bytes(), before)

    def test_cli_demo_reads_shared_workflow(self):
        command = [sys.executable, "-X", "utf8", "-m", "repair_system",
                   "--db", str(self.db_path), "demo"]
        run = subprocess.run(command, cwd=ROOT, check=True, capture_output=True,
                             encoding="utf-8", timeout=20)
        first = json.loads(run.stdout)
        self.assertEqual(first["before_submit"]["status"], "尚无工单回执")
        self.assertEqual(first["receipt"], first["retry"])
        second = json.loads(subprocess.run(
            command, cwd=ROOT, check=True, capture_output=True, encoding="utf-8", timeout=20
        ).stdout)
        self.assertEqual(first["history"], second["history"])

    def test_chapter_one_resource_script_matches_repository_copy(self):
        book = ROOT / "让AI读懂企业/四篇十六章书稿"
        if not any((book / "第一篇-认知篇").glob("第1章-*.md")):
            self.skipTest("当前副本只包含配套代码")
        resource = book / "随书资源/技术详解/第01章-技术详解.md"
        fences = re.findall(r"^```python\n(.*?)\n```$", resource.read_text(encoding="utf-8"), re.M | re.S)
        self.assertEqual(len(fences), 3)
        script = ROOT / "examples/chapter1/repair_agent.py"
        self.assertEqual(script.read_text(encoding="utf-8"), "\n\n".join(fences) + "\n")


if __name__ == "__main__":
    unittest.main()
