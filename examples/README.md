# 《让AI管理业务》配套练习

本目录与《让AI管理业务：本体驱动的智能体落地实践》四篇十六章 v2026.11.26 版正文对应。下载解压后，可在本地阅读说明和运行示例。

设备维修工单主程序位于仓库根目录的 `repair_system/`。从这里找到[仓库首页](../README.md)的启动命令，或进入[系统操作指南](../repair_system/README.md)按岗位完成告警核查、审批、建单和反查。

## 按章节查找程序和运行说明

| 章节 | 随书示例 |
| --- | --- |
| 第 1 章 | [从设备告警到维修工单](chapter1/README.md) |
| 第 2 章 | [检查查询对象、工具和权限](chapter2/README.md) |
| 第 3 章 | [两入口规则变更](#业务规则与查询) |
| 第 5 章 | [告警证据核查](第5章-告警证据核查/README.md) |
| 第 6 章 | [申请与回执](第6章-申请与回执/README.md) |
| 第 7 章 | [订单金额复算、退回重复计算与指标定义](订单金额复算/README.md) |
| 第 9 章 | [订单归属校验和四单交班复算](第9章-候选校验/README.md) |
| 第 10 章 | [接入与回放](chapter1/接入与回放.md) |
| 第 11 章 | [工单查询与交班材料](工单查询与交班/README.md)、[终端交付核查](第11章-终端交付/README.md) |
| 第 12 章 | [派工超时、安全反查与重复提交](派工超时/README.md) |
| 第 13 章 | [查询范围复测](第13章-查询范围复测.md) |
| 附录 D | [本地图查询与来源记录](附录D-本地图查询/README.md) |

还可完成[读者独立试做](读者独立试做.md)，做完后打开[独立试做核对](独立试做核对.md)。

## 迁移和对照练习

下面的工单、订单和交付案例各自使用独立的教学数据。跑完主案例后，可用它们检验相同方法在不同业务里的表现。建议使用 Python 3.12，从各示例目录执行命令，涉及依赖的两组练习各用一个独立虚拟环境。

### 业务规则与查询

在[两入口规则变更](两入口规则变更)目录运行 `python -X utf8 compare.py`。六种规则安排的清单都列出 T-001、T-003。第 2、4 种安排中的交班卡沿用旧定义，应把“待验收”标为待核。

在[工单查询与交班](工单查询与交班)目录运行以下命令，依次检查原四单、五单中新增单处理中、五单中新增单已完成。

```text
python -X utf8 ticket_practice.py four --output runs/four
python -X utf8 ticket_practice.py open --output runs/open
python -X utf8 ticket_practice.py completed --output runs/completed
```

`query-result.json` 分别应列出 2、3、2 张工单。处理中版本新增 T-005，`handover.md` 的设备栏应写“原文明确未关联”。重复运行时，请给 `--output` 另起目录名。

练习查询范围时，先将整个工单目录复制到可写位置。复制 `查询请求.json` 为 `请求-单状态.json`，只把 `arguments.statuses` 改成 `["处理中"]`，再运行下面的命令。原定义下应拒绝。若再把工作副本中的 `业务定义.json` 的 `unfinished_statuses` 也改为 `["处理中"]`，用新的输出目录重跑，只会得到 T-001。

```text
python -X utf8 ticket_practice.py four --request 请求-单状态.json --output runs/single-status
```

### 订单金额与终端交付

在[订单金额复算](订单金额复算)目录运行以下命令。

```text
python -X utf8 run_orders.py
python -X utf8 run_orders.py customer_totals.sql customer_orders.sql
python -X utf8 delivery_value.py
```

第一条按客户列出签约金额与已交付金额，合计分别为 2700 和 1650 万元。第二条还给出缺项数。第三条对比两个到货与退回汇总的结果，错误连接为 3100，按到货单复算为 1600。

在[终端交付](第11章-终端交付)目录运行以下命令。核对尚未验收 10 台，其中到货待验 2 台、尚未到货 8 台。第三条把核对结果写入 `delivery-handover-output/`。

```text
python -X utf8 delivery_check.py
python -X utf8 delivery_test.py
python -X utf8 delivery_handover.py
```

### 图查询与关单材料检查

第 9.5 节的五组结构与归属对照见[第 9 章订单归属校验](第9章-候选校验/README.md)。

在[候选校验](第9章-候选校验)目录用独立的 Python 环境安装依赖。

```text
python -m pip install -r requirements.txt
python -X utf8 validate_query.py
```

正常输入应查到 C-001，缺少客户关系及连到错误类型的两种候选均应被拒绝。沿用这一环境，在[四单查询](工单查询与关单材料校验/四单查询)目录运行 `python -X utf8 query_rdf_tickets.py`，应列出 T-001、T-003。在[关单材料](工单查询与关单材料校验/关单材料)目录运行 `python -X utf8 check_request.py`，应看到形状通过、可比较配对 1 组、明确错配 1 行。

### 派工超时后的反查

在[派工超时](派工超时)目录运行以下命令。核对旧请求在重复提交时只对应一笔业务记录。改参数重发及换身份反查各有明确的拒绝结果。

```text
python -X utf8 dispatch_demo.py
python -X utf8 dispatch_verify.py
```

### 本地图查询与来源记录

在[本地图查询](附录D-本地图查询)目录用另一个 Python 3.12 环境运行。先完成依赖安装，再按顺序执行三个脚本。

```text
python -m pip install "semantica[tripletstore-oxigraph]==0.7.0"
python -X utf8 demo_d2.py
python -X utf8 demo_d3.py
python -X utf8 demo_d4.py
```

查询应返回客户 C-001。后两条分别生成 `ticket-context.json` 和 `ticket-source.json`，决定编号与来源版本应一致，导出的两条来源都应带校验值。
