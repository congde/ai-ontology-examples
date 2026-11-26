from contextlib import closing

from dispatch_demo import CALLER, QUEUE, REQUEST, TICKET
from dispatch_demo import find_todo, open_demo, submit
from dispatch_demo import NEXT_DUTY, lookup_handover


def compare_retry(retry_id, retry_caller=CALLER):
    with closing(open_demo()) as db:
        try:
            submit(db, CALLER, REQUEST, TICKET, QUEUE,
                   drop_reply=True)
        except TimeoutError:
            original = find_todo(db, CALLER, REQUEST)
        else:
            raise AssertionError("没有复现响应超时")
        assert original == (1, TICKET, QUEUE), original
        result = submit(db, retry_caller, retry_id, TICKET, QUEUE)
        saved = find_todo(db, retry_caller, retry_id)
        assert saved == (result[0], TICKET, QUEUE), saved
        total, = db.execute("SELECT count(*) FROM todo").fetchone()
        return original[0], result[0], total

normal = compare_retry(REQUEST)
changed = compare_retry("R-02")
print("沿用原编号", normal)
print("更换编号", changed)
assert normal == (1, 1, 1), normal
assert changed == (1, 2, 2), changed

with closing(open_demo()) as db:
    original = submit(db, CALLER, REQUEST, TICKET, QUEUE)
    for ticket, queue, label in (
        (TICKET, "Q-B", "改队列"),
        ("WO-B", QUEUE, "改工单"),
    ):
        try:
            submit(db, CALLER, REQUEST, ticket, queue)
        except ValueError as error:
            assert str(error) == "原请求的参数不一致", error
            print("沿用编号但" + label, error)
        else:
            raise AssertionError(label + "后仍接受原请求编号")
        assert find_todo(db, CALLER, REQUEST) == original
        assert db.execute("SELECT count(*) FROM todo").fetchone() == (1,)

with closing(open_demo()) as db:
    original = submit(db, CALLER, REQUEST, TICKET, QUEUE)
    assert find_todo(db, NEXT_DUTY, REQUEST) is None
    assert lookup_handover(db, NEXT_DUTY, CALLER, REQUEST) == original
    print("接班人名下查空，按原申请反查得到待办", original[0])
    for reader, request_id in (("duty-c", REQUEST), (NEXT_DUTY, "R-02")):
        try:
            lookup_handover(db, reader, CALLER, request_id)
        except PermissionError as error:
            print(reader, request_id, error)
        else:
            raise AssertionError("允许了超出授权范围的反查")
    assert db.execute("SELECT count(*) FROM todo").fetchone() == (1,)

wrong_caller = compare_retry(REQUEST, NEXT_DUTY)
print("换调用者重发原编号", wrong_caller)
assert wrong_caller == (1, 2, 2), wrong_caller
