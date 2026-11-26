# 第 9 章 订单归属校验

本练习对应第 9.5 节“验证订单关系的结构与归属”。教学原单记载订单 O-001 属于华北机械 C-001。用同一份规则和查询处理五个数据文件，分别记录结构结果、查询端点和发布决定。

## 运行五个对照

将本目录完整复制到可写的练习位置，进入该目录。需要 Python 3.12。首次安装依赖需要访问软件包源。清单锁定了书中使用的 `pyshacl==0.25.0` 和 `rdflib==6.3.2`。

Windows PowerShell 中运行以下命令。如果使用 Python 启动器，可把第一条换成 `py -3.12 -m venv .venv`。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 check_order.py
.\.venv\Scripts\python.exe -X utf8 check_order.py missing.ttl
.\.venv\Scripts\python.exe -X utf8 check_order.py wrong_type.ttl
.\.venv\Scripts\python.exe -X utf8 check_order.py wrong_customer.ttl
.\.venv\Scripts\python.exe -X utf8 check_order.py missing_order_type.ttl
```

macOS 或 Linux 中运行以下命令。

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -X utf8 check_order.py
.venv/bin/python -X utf8 check_order.py missing.ttl
.venv/bin/python -X utf8 check_order.py wrong_type.ttl
.venv/bin/python -X utf8 check_order.py wrong_customer.ttl
.venv/bin/python -X utf8 check_order.py missing_order_type.ttl
```

| 数据文件 | 规则实际检查的订单 | 首行输出 | 查询端点 | 结合原单的判断 |
|---|---|---|---|---|
| `order.ttl` | O-001 | 结构通过 | C-001 | 校验覆盖本单，归属与原单相符 |
| `missing.ttl` | O-001 | 结构错误 | 无结果 | 缺少客户关联 |
| `wrong_type.ttl` | O-001 | 结构错误 | E-001 | 关联指向设备 |
| `wrong_customer.ttl` | O-001 | 结构通过 | C-002 | 客户类型合法，归属与原单不符 |
| `missing_order_type.ttl` | 无 | 结构通过 | C-001 | 归属可以查到，订单没有进入校验，待纠正类型声明后复测 |

程序打印结构判定和查询端点。表中的检查覆盖由数据文件里的 `a ex:Order` 声明与规则的 `sh:targetClass ex:Order` 对照得到，采用决定还须和上面的教学原单核对。

## 对照原文件

- [order.ttl](order.ttl) 是原始图数据。
- [order_shape.ttl](order_shape.ttl) 检查被选中的每笔订单恰好关联一个客户。
- [order_query.rq](order_query.rq) 按订单号读取关联端点。
- [check_order.py](check_order.py) 依次运行校验和查询。结构错误时仍打印查询结果，便于比对两步分别回答了什么。

## 用四单复算交班清单

第 9.8.2 节的 [ticket_list.py](ticket_list.py) 使用书中四张原单的已核对取值。它只依赖 Python 标准库，也可单独复制到练习目录运行：

```text
python -X utf8 ticket_list.py
```

程序打印两行：

```text
T-001 处理中 E-001 甲/T-001
T-003 待派工 E-001 甲/T-003、甲/T-001
```

最后的断言用独立副本将 T-003 改为已完成，应只剩 T-001，断言通过时不会另打印。设备资料、故障单处理结论和两单承接关系仍须沿其各自来源核对。
