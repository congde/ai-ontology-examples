# 设备维修工单系统

09:00，数控加工中心 `E-001` 报主轴振动告警 `A-001`。09:10 的设备观测为“运行中”，本次告警的维修结论待核。值班员据此提出申请 `R-001`，维修主管批准后由执行岗位提交。维修系统创建工单 `W-001`，状态为“待派工”。交班人按原申请号查回执，审计岗位沿同号查看申请是怎样办成的。

## 一条命令跑完全程

使用 Python 3.11 或更高版本，在仓库根目录运行。首次演练请选一个新的数据库文件名，后续命令沿用该文件来复查。默认演练使用本地数据、内置工具提议和 SQLite，无需安装第三方包。

```text
python -X utf8 -m repair_system --db demo.sqlite3 demo
```

核对 JSON 输出中是否出现 `R-001` 和 `W-001`。成功回执的 `result` 为“已创建”，工单 `status` 为“待派工”。这份回执证明工单已经建立。实际派工、维修与验收各有自己的现场记录。省略 `--db` 时，系统使用当前目录的 `repair_workflow.sqlite3`。

如果已有演练数据库保存在 `examples` 目录，可从仓库根目录用 `--db` 指向该文件，例如 `--db examples/demo.sqlite3`，继续反查原申请。

命令入口在 [`__main__.py`](__main__.py)。[`scenario.json`](scenario.json) 提供演练数据，[`domain.py`](domain.py) 管理证据归属和操作权限，[`workflow.py`](workflow.py) 管理审批、工单、回执和审计。[`model.py`](model.py) 负责连接可选的模型端点。

## 按岗位检查每一步

在仓库根目录运行下列命令。使用新的 `trace.sqlite3`，分别观察审批前、审批后和执行后的状态。请逐条运行，模拟超时命令返回退出码 `2` 后，再执行下一条反查。

```text
python -X utf8 -m repair_system --db trace.sqlite3 read --actor operator
python -X utf8 -m repair_system --db trace.sqlite3 propose --actor operator
python -X utf8 -m repair_system --db trace.sqlite3 receipt R-001 --actor operator
python -X utf8 -m repair_system --db trace.sqlite3 approve R-001 --actor supervisor
python -X utf8 -m repair_system --db trace.sqlite3 submit R-001 --actor executor --simulate-timeout
python -X utf8 -m repair_system --db trace.sqlite3 receipt R-001 --actor operator
python -X utf8 -m repair_system --db trace.sqlite3 submit R-001 --actor executor
python -X utf8 -m repair_system --db trace.sqlite3 history R-001 --actor auditor
python -X utf8 -m repair_system --db trace.sqlite3 metrics --actor auditor
```

| 在哪一步 | 核对什么 |
| --- | --- |
| 值班员查证和起草 | 先看到 09:00 的告警、09:10 的运行观测和本次维修结论缺项，再得到“待审批”的申请 `R-001` |
| 审批前查回执 | 看到“尚无工单回执” |
| 主管批准 | 看到该申请已获批准，执行人员可以按原申请提交 |
| 模拟响应超时 | 首次提交返回“响应超时”和“待反查”。继续执行下一行，用原申请号反查 |
| 反查和重试 | 反查得到待派工的 `W-001`。重复提交仍返回同一工单 |
| 审计和指标 | 按 `R-001` 查看办理经过。重复提交后，`requests`、`approved` 和 `created` 应均为 1 |

指标只统计审计岗位获准查看的设备。建单率 `creation_rate` 用已建单申请数 `created` 除以申请数 `requests`。一笔申请重发仍只算一笔，尚无申请时返回空值。

用另一份空库复做前三步，在审批前以 `executor` 试提交 `R-001`。应看到“申请尚未审批”，再查仍无工单回执。把第一步的 `--actor operator` 改为 `--actor other`，应看到“未找到可访问的告警”。对照正常和异常两种运行结果，检查系统在拒绝后保留了哪些业务状态。

在仓库根目录运行[回归测试](../tests/test_repair_system.py)，可核对正常办理、审批前提交、跨设备读取和超时反查是否仍符合预期。

```text
python -X utf8 -m unittest discover -s tests -v
```

## 可选的模型提议

有[告警沙箱、模型回放与系统接入](../examples/chapter1/接入与回放.md)所述的兼容模型端点时，可在同一终端设置 `MODEL_CHAT_URL`、`MODEL_NAME`，并在服务要求时设置 `MODEL_API_KEY`。然后在仓库根目录用新数据库运行下列命令。

```text
python -X utf8 -m repair_system --db repair_model.sqlite3 propose --actor operator --live
```

联网模式沿用第1章固定的 `A-001` 任务。模型提议的工具及告警编号仍由程序检查。读者可以先跑本地演练，再比较两种方式生成的草稿和证据。

## 对照书中章节并改动一项条件

| 书中内容 | 在系统里怎么核对 |
| --- | --- |
| §1.1、§2.1、§4.2　从值班请求到应用分工 | 先用 `demo` 看完整过程，再用 `read` 和 `propose` 分辨事实、工具提议和办理请求 |
| §5.2、§6.2、§7.1、§8.4　业务对象、约束、指标和来源 | 在 [scenario.json](scenario.json) 找告警、设备与观测的关联，在 [domain.py](domain.py) 看系统怎样核对归属。对照 `history` 和 `metrics`，复查一次重复提交怎样影响计数 |
| 第 11.2 节、第 12.1–12.3 节　工具授权、审批和回执 | 用四种岗位轮流操作，在 [workflow.py](workflow.py) 查看审批和执行怎样绑定原申请，再用超时和重复提交检验回执 |
| 第 13.2 节、第 14.2 节、第 15.3 节、第 16.3 节　评测、接入和迁移 | 先记录正常与拒绝案例的预期结果。换到另一条产线时，重新核对资产归属、值班权限、审批条件和回执来源，再判断哪些做法可沿用 |

先读取 `A-000` 和 `A-001`。两条告警关联同一设备，但只有 `A-000` 有维修结论。再把 `repair_system/scenario.json` 复制为当前目录下的 `repair_scenario.json`，移除副本中设备 `E-001` 的观测，重读 `A-001`。设备身份和告警应仍然可查，观测应留空。

```text
python -X utf8 -m repair_system --db trace.sqlite3 read --actor operator --alarm A-000
python -X utf8 -m repair_system --db trace.sqlite3 read --actor operator --alarm A-001
python -X utf8 -m repair_system --scenario repair_scenario.json --db comparison.sqlite3 read --actor operator --alarm A-001
```

### 审批后更换规则版本

先执行前两行，用新的 `revision.sqlite3` 创建并批准一份草稿。接着复制默认场景 `repair_system/scenario.json` 为当前目录下的 `scenario_v2.json`，只把其中的 `rule_version` 从 `repair-v1` 改为 `repair-v2`。再从第三行继续。

```text
python -X utf8 -m repair_system --db revision.sqlite3 propose --actor operator
python -X utf8 -m repair_system --db revision.sqlite3 approve R-001 --actor supervisor
python -X utf8 -m repair_system --scenario scenario_v2.json --db revision.sqlite3 submit R-001 --actor executor
python -X utf8 -m repair_system --scenario scenario_v2.json --db revision.sqlite3 propose --actor operator
python -X utf8 -m repair_system --scenario scenario_v2.json --db revision.sqlite3 approve R-001 --actor supervisor
python -X utf8 -m repair_system --scenario scenario_v2.json --db revision.sqlite3 submit R-001 --actor executor
```

第三行应因证据版本变化被拒绝。第四行用新版本更新同一申请，状态重新为“待审批”。主管重新批准后，最后一行才应创建 `W-001`。这组变化可以用来复查第 6.3 节的定义与反例、第 12.1 节的审批条件。

系统在本机用合成场景模拟企业办理，`--actor` 是演练岗位，SQLite 是沙箱记录。现场接入时，按第10–14章核实真实身份、来源系统、写入接口和责任岗位，并用同一组正常与反例验证。

## 第1章纸书单文件练习

[repair_agent.py](../examples/chapter1/repair_agent.py) 提供第 1 章可独立运行的告警、审批和反查练习。把它复制到空目录，在该目录执行 `python -X utf8 repair_agent.py propose`，然后按[告警沙箱、模型回放与系统接入](../examples/chapter1/接入与回放.md)运行审批和反查。这个单文件程序使用当前目录的 `repair_demo.sqlite3`，可以看到完整系统中的取证、审批和写入怎样从一个入门程序逐步拆开。
