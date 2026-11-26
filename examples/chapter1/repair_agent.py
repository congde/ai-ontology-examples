import argparse
import http.client
import json
import os
import sqlite3
from contextlib import closing
from urllib.parse import urlsplit

TASK = "核查告警 A-001，必要时准备维修工单"
READ = {"tool": "read_evidence", "alarm_id": "A-001"}
EVIDENCE = {
    "alarm": {"alarm_id": "A-001", "device_id": "E-001",
              "name": "主轴振动告警", "time": "09:00"},
    "observation": {"device_id": "E-001", "state": "运行中", "time": "09:10"},
    "repair_result": None,
}


def model_proposal():
    url = urlsplit(os.environ.get("MODEL_CHAT_URL", ""))
    model = os.environ.get("MODEL_NAME", "")
    key = os.environ.get("MODEL_API_KEY")
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not model or not url.hostname or not url.path or
            url.username or url.password or url.fragment or
            (url.scheme != "https" and not (local and url.scheme == "http"))):
        raise ValueError("请配置完整模型地址和模型名，远程地址须使用 HTTPS")
    messages = [
        {"role": "system", "content": '只可提议只读工具。仅输出单个 JSON 对象，'
         '格式为 {"tool":"read_evidence","alarm_id":"告警编号"}。'},
        {"role": "user", "content": TASK},
    ]
    payload = json.dumps({"model": model, "messages": messages})
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    connect = (http.client.HTTPSConnection if url.scheme == "https"
               else http.client.HTTPConnection)
    target = url.path + ("?" + url.query if url.query else "")
    with closing(connect(url.hostname, url.port, timeout=20)) as conn:
        conn.request("POST", target, payload, headers)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f"模型 HTTP 状态 {response.status}")
        data = json.loads(response.read())
    return json.loads(data["choices"][0]["message"]["content"])

def open_store():
    return sqlite3.connect("repair_demo.sqlite3", timeout=5)


def prepare(db, proposal):
    if proposal != READ:
        raise ValueError("拒绝未经许可的工具或告警，未写入维修工单")
    evidence = json.dumps(EVIDENCE, ensure_ascii=False)
    db.execute("INSERT OR IGNORE INTO drafts VALUES (?, ?)", ("R-001", evidence))
    return {
        "request_id": "R-001", "status": "待审批",
        "tool_proposal": proposal, "evidence": EVIDENCE,
        "suggestion": "核查本次振动告警，维修结论未取得",
    }


def lookup(db, request_id):
    row = db.execute(
        "SELECT work_order_id, status FROM work_orders WHERE request_id = ?",
        (request_id,),
    ).fetchone()
    if row:
        return {"request_id": request_id, "work_order_id": row[0],
                "status": row[1], "result": "已创建"}
    draft = db.execute(
        "SELECT 1 FROM drafts WHERE request_id = ?", (request_id,)
    ).fetchone()
    return {"request_id": request_id, "status": "尚无工单回执" if draft else "未找到请求"}


def approve(db, request_id):
    db.execute("BEGIN IMMEDIATE")
    prior = lookup(db, request_id)
    if prior["status"] == "未找到请求":
        raise ValueError("请先准备草案")
    if "work_order_id" in prior:
        return prior
    db.execute("INSERT INTO approvals VALUES (?, ?)", (request_id, "本地模拟维修主管"))
    db.execute("INSERT INTO work_orders VALUES (?, ?, ?)", (request_id, "W-001", "待派工"))
    return lookup(db, request_id)

def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("propose").add_argument("--live", action="store_true")
    for name in ("approve", "receipt"):
        commands.add_parser(name).add_argument("request_id")
    args = parser.parse_args()
    try:
        proposal = None
        if args.command == "propose":
            proposal = model_proposal() if args.live else READ
        with closing(open_store()) as db, db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS drafts (
                    request_id TEXT PRIMARY KEY, evidence TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS approvals (
                    request_id TEXT PRIMARY KEY REFERENCES drafts, actor TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS work_orders (
                    request_id TEXT PRIMARY KEY REFERENCES approvals,
                    work_order_id TEXT UNIQUE NOT NULL, status TEXT NOT NULL);
            """)
            if args.command == "propose":
                result = prepare(db, proposal)
                receipt = lookup(db, result["request_id"])
                if "work_order_id" in receipt:
                    result["status"] = "已创建"
                result["mode"] = "模型接口" if args.live else "本地重放"
            elif args.command == "approve":
                result = approve(db, args.request_id)
            else:
                result = lookup(db, args.request_id)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, KeyError, IndexError, TypeError, OSError,
            http.client.HTTPException, sqlite3.Error) as err:
        parser.exit(1, f"未能完成本步：{err}\n")


if __name__ == "__main__":
    main()
