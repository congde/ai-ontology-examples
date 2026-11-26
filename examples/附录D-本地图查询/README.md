# 附录 D 本地图查询和来源导出

复制本目录到一个可写位置，在终端进入复制后的目录。用 Python 3.12 安装 Semantica 0.7.0 和 Oxigraph 本地图存储组件。首次安装需要访问软件包源，安装后脚本使用本地教学数据，无需模型账号。

输入为 [orders.csv](orders.csv)。三个脚本按 D.2、D.3、D.4.1 的顺序运行。后两步用同一轮生成的决定文件。

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install 'semantica[tripletstore-oxigraph]==0.7.0'
.\.venv\Scripts\python.exe demo_d2.py
.\.venv\Scripts\python.exe demo_d3.py
.\.venv\Scripts\python.exe demo_d4.py
```

如果没有 `py` 启动器，先用 `python --version` 核对解释器为 3.12，再用 `python -m venv .venv` 创建环境。也可以用已安装的 Python 3.12 可执行文件的完整路径运行 `-m venv .venv`。确认版本与依赖安装成功后再运行脚本。

## macOS 或 Linux Bash

```bash
python3.12 -m venv .venv
.venv/bin/python --version
.venv/bin/python -m pip install 'semantica[tripletstore-oxigraph]==0.7.0'
.venv/bin/python demo_d2.py
.venv/bin/python demo_d3.py
.venv/bin/python demo_d4.py
```

## 核对输出

| 脚本 | 核对的结果 |
| --- | --- |
| [demo_d2.py](demo_d2.py) | 输出 JSON。`customers` 只有 `https://example.org/enterprise/C-001`，`file` 为 `orders.csv`，`source_rows` 有 O-001 的一行，含 C-001、教学订单清单O-001行和 `v1.1`。 |
| [demo_d3.py](demo_d3.py) | 显示“已记录教学决定”和本轮生成的编号，写出 `ticket-context.json`。文件内编号与终端相同，来源版本为“教学样本v1.1”，结论为“留在未完成清单并请有权人复核”。 |
| [demo_d4.py](demo_d4.py) | 显示 `ticket-source.json` 和同一决定编号。两份 JSON 的 `decision_id` 与 `source_version` 分别相同，导出项的来源位置为“T-001 行”和“E-001 行”，各有 `checksum`。 |

检查错绑反例时，先备份练习目录中的 `orders.csv`，将唯一记录的 C-001 改为 C-002，再运行 `demo_d2.py`。预期报出含有 C-002 的 `AssertionError`，程序在生成 JSON 前停止。恢复原文件后再运行一次，核对重新返回 C-001。实际业务归属应回到原订单审核。

[返回书中配套示例入口](../README.md)
