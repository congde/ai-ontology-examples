import sqlite3
from contextlib import closing


CALLER, REQUEST = "duty-a", "R-01"
TICKET, QUEUE = "WO-A", "Q-A"
NEXT_DUTY = "duty-b"
READ_GRANTS = {(NEXT_DUTY, CALLER, REQUEST)}


def open_demo():
    db = sqlite3.connect(":memory:")
    db.execute("""
        CREATE TABLE todo (
            id INTEGER PRIMARY KEY,
            caller TEXT NOT NULL,
            request_id TEXT NOT NULL,
            ticket TEXT NOT NULL,
            queue TEXT NOT NULL,
            UNIQUE (caller, request_id)
        )
    """)
    return db

def find_todo(db, caller, request_id):
    return db.execute(
        "SELECT id, ticket, queue FROM todo "
        "WHERE caller = ? AND request_id = ?",
        (caller, request_id),
    ).fetchone()


def lookup_handover(db, reader, original_caller, request_id):
    if (reader, original_caller, request_id) not in READ_GRANTS:
        raise PermissionError("未获这笔原申请的反查权限")
    return find_todo(db, original_caller, request_id)

def submit(db, caller, request_id, ticket, queue,
           drop_reply=False):
    with db:
        db.execute(
            "INSERT INTO todo(caller, request_id, ticket, queue) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(caller, request_id) DO NOTHING",
            (caller, request_id, ticket, queue),
        )
        saved = find_todo(db, caller, request_id)
        if saved[1:] != (ticket, queue):
            raise ValueError("原请求的参数不一致")
    if drop_reply:
        raise TimeoutError("响应超时")
    return saved

if __name__ == "__main__":
    with closing(open_demo()) as db:
        try:
            submit(db, CALLER, REQUEST, TICKET, QUEUE,
                   drop_reply=True)
        except TimeoutError:
            print("交班：已提交，回执超时，结果待核。", CALLER, REQUEST)
        record = lookup_handover(db, NEXT_DUTY, CALLER, REQUEST)
        if record and record[1:] == (TICKET, QUEUE):
            print("补记：接班人查到原待办。", NEXT_DUTY, record)
        else:
            print("补记：结果仍待核。", REQUEST)
