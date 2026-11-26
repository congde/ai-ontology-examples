# 第 1 章 从设备告警到维修工单

本例使用 Python 3.11 或更高版本，只依赖标准库。将 [repair_agent.py](repair_agent.py) 复制到有写权限的空目录，在该目录打开终端。脚本会建立本地数据库 `repair_demo.sqlite3`。同一轮的命令应在同一目录运行，另起一轮时换一个空目录。

若 `python --version` 未指向 Python 3.11 或更高版本，改用本机适用的启动命令，例如 Windows 上的 `py -3.12`。

## 离线复做

```text
python -X utf8 repair_agent.py propose
python -X utf8 repair_agent.py receipt R-001
python -X utf8 repair_agent.py approve R-001
python -X utf8 repair_agent.py receipt R-001
python -X utf8 repair_agent.py approve R-001
```

第一步形成待审批申请 R-001，第一次反查提示尚无工单回执。模拟批准后能够查到工单 W-001，重复审批仍回到同一工单。

```json
{"request_id":"R-001","work_order_id":"W-001",
 "status":"待派工","result":"已创建"}
```

```text
python -X utf8 repair_agent.py receipt R-999
python -X utf8 repair_agent.py approve R-999
```

第一行提示未找到请求，第二行提示先准备草案并退出。两条命令都不会为 R-999 创建工单。正文第 1.1.2 节用这些回执推导两份不同的交班话。

## 可选的模型调用

用获准的 Chat Completions 兼容接口替换本地重放步骤。远程地址使用 HTTPS，本机端点可用 HTTP。服务要求 API 密钥时，按组织要求在当前终端或密钥管理服务中设置 `MODEL_API_KEY`。如需看到批准前的状态，在另一个空目录复制同一脚本。

Windows PowerShell：

```powershell
$env:MODEL_CHAT_URL = '替换为服务方给出的完整请求地址'
$env:MODEL_NAME = '替换为模型名'
python -X utf8 repair_agent.py propose --live
```

Bash：

```sh
export MODEL_CHAT_URL='替换为服务方给出的完整请求地址'
export MODEL_NAME='替换为模型名'
python -X utf8 repair_agent.py propose --live
```

成功时模式显示“模型接口”。模型只收到教学任务和输出约定。应用继续校验工具名及告警号，才允许读取；业务数据、模拟审批和工单回执仍由本地程序保管。若接口、响应格式或工具提议不符合约定，先核对错误提示，再用本地重放结果对照。工程接入需要身份核验、受控审批及真实系统权限。
