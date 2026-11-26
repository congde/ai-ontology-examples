# 工单查询与交班

第 11.2.1 和 11.3.1 节的 2026 年 11 月 16 日教学记录节录如下。第一份保存实际请求，第二份保存书中列出的业务定义部分。历史运行和交班答复摘要见正文。

- [历史查询请求](历史查询请求-20261116.json) 使用工单查询工具，查询 C-001 的“处理中”和“待派工”，定义编号为 `ticket-query-1`。
- [历史业务定义节录](历史业务定义节录-20261116.json) 保留状态和客户字段、当前任务限于 C-001、只读要求以及工具名。

## 离线复做

保持当前目录和三套输入结构完整，再进入当前目录，使用 Python 运行：

```text
python -X utf8 ticket_practice.py four --output runs/four
python -X utf8 ticket_practice.py open --output runs/open
python -X utf8 ticket_practice.py completed --output runs/completed
```

案例脚本用本目录的 [业务定义](业务定义.json) 和 [查询请求](查询请求.json)，均为离线练习配套文件。历史业务定义节录仅供阅读对照，其结构与离线执行所用定义不同。输出目录必须是新目录。三组应分别取回 2、3、2 张单。四单的查询结果为 T-001、T-003；处理中副本另收录 T-005。检查 `query-result.json` 中的来源和 `handover.md` 的交班文字；`run.json` 记录使用的版本、输入及实际模型调用数。本地筛选不调模型。

若要比较参数与定义，先把本目录完整复制一份，在工作副本中将查询请求另存为 `请求-单状态.json`，只把状态列表改为含“处理中”。用下面的命令运行。原定义仍要求两种状态，程序会在查询前拒绝。

```text
python -X utf8 ticket_practice.py four --request 请求-单状态.json --output runs/one-status-rejected
```

再把工作副本中 `业务定义.json` 的 `unfinished_statuses` 改成只含“处理中”，仍用同一查询请求，换新输出目录重跑。应只返回 T-001。原资料保留在原目录。
