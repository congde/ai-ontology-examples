import argparse
import http.client
import json
import sqlite3
import sys
from pathlib import Path

from .domain import DomainError, authorize, load_scenario, read_evidence
from .model import model_proposal
from .workflow import ReceiptUnknown, Workflow


def replay_proposal(alarm_id):
    return {"tool": "read_evidence", "alarm_id": alarm_id}


def run_demo(workflow, scenario):
    alarm_id = "A-001"
    evidence = read_evidence(scenario, alarm_id, "operator")
    draft = workflow.propose("operator", alarm_id, replay_proposal(alarm_id))
    request_id = draft["request_id"]
    before = workflow.receipt("operator", request_id)
    approved = workflow.approve("supervisor", request_id)
    if "work_order_id" in before:
        submission = "按原请求查到已有回执"
    else:
        try:
            workflow.submit("executor", request_id, simulate_timeout=True)
        except ReceiptUnknown:
            submission = "响应超时，按原请求反查"
        else:
            submission = "已获得回执"
    receipt = workflow.receipt("operator", request_id)
    retry = workflow.submit("executor", request_id)
    return {
        "alarm_id": alarm_id,
        "evidence": evidence,
        "draft": draft,
        "before_submit": before,
        "approval": approved,
        "submission": submission,
        "receipt": receipt,
        "retry": retry,
        "history": workflow.history("auditor", request_id),
        "metrics": workflow.metrics("auditor"),
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="python -m repair_system",
        description="在本地演练设备告警核查、维修工单审批、建单与反查。",
    )
    parser.add_argument("--db", type=Path, default=Path("repair_workflow.sqlite3"),
                        help="本地 SQLite 文件，和第1章单文件练习分别存放")
    parser.add_argument("--scenario", type=Path, help="自定义场景 JSON，默认使用项目中的教学数据")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="演练从告警到超时后的回执反查")
    for name, help_text in (
        ("read", "读取告警及关联证据"),
        ("propose", "校验工具提议并保存维修工单草案"),
        ("approve", "按草案证据批准一项请求"),
        ("submit", "提交已获批的请求"),
        ("receipt", "按原请求号反查回执"),
        ("history", "按原请求号回查办理轨迹"),
        ("metrics", "按获准资产统计请求、审批和建单"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--actor", required=True, help="场景里定义的模拟身份")
        if name in {"read", "propose"}:
            command.add_argument("--alarm", default="A-001", help="告警编号")
        if name in {"approve", "submit", "receipt", "history"}:
            command.add_argument("request_id", help="原申请编号")
        if name == "propose":
            command.add_argument("--live", action="store_true", help="让模型提出第1章 A-001 的读取工具")
        if name == "submit":
            command.add_argument("--simulate-timeout", action="store_true", help="提交成功后模拟回执丢失")
    return parser.parse_args(argv)


def execute(args, scenario):
    if args.command == "read":
        return read_evidence(scenario, args.alarm, args.actor)
    workflow = Workflow(args.db, scenario)
    if args.command == "demo":
        return run_demo(workflow, scenario)
    if args.command == "metrics":
        return workflow.metrics(args.actor)
    if args.command == "propose":
        if args.live:
            if args.alarm != "A-001":
                raise DomainError("模型选项仅使用书中 A-001 的固定教学任务")
            evidence = read_evidence(scenario, args.alarm, args.actor)
            authorize(scenario, args.actor, "propose", evidence["device_id"])
            proposal = model_proposal()
        else:
            proposal = replay_proposal(args.alarm)
        return workflow.propose(args.actor, args.alarm, proposal)
    if args.command == "submit":
        return workflow.submit(args.actor, args.request_id, simulate_timeout=args.simulate_timeout)
    operation = {
        "approve": workflow.approve,
        "receipt": workflow.receipt,
        "history": workflow.history,
    }
    return operation[args.command](args.actor, args.request_id)


def main(argv=None):
    args = parse_args(argv)
    try:
        result = execute(args, load_scenario(args.scenario))
    except ReceiptUnknown as error:
        result = {"request_id": error.request_id, "status": "响应超时", "result": "待反查"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    except (ValueError, KeyError, IndexError, TypeError, OSError,
            http.client.HTTPException, sqlite3.Error) as error:
        print(f"未能完成本步：{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
