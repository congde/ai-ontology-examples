# 《让AI管理业务》随书示例

对应《让AI管理业务：本体驱动的智能体落地实践》四篇十六章 v2026.11.26 版。

从 [v2026.11.26 下载页](https://github.com/congde/ai-ontology-examples/releases/tag/v2026.11.26) 下载 Assets 下的随书示例 ZIP。解压后，打开[配套练习目录](examples/README.md)，按纸书章号查找说明、程序、教学数据和预期结果。无需 GitHub 账号、Git 或模型账号即可下载并复做离线练习。建议使用 Python 3.12。图查询和附录 D 首次安装依赖需要能够访问 Python 软件包源，安装完成后在本地运行。

## 从主案例开始

在解压目录用 Python 运行设备维修工单系统。首次运行请使用新的数据库文件名。

```text
python -X utf8 -m repair_system --db demo.sqlite3 demo
```

按原申请 R-001 查回的工单应为 W-001，状态为“待派工”。做完可在[系统操作指南](repair_system/README.md)中查找分岗位的办理步骤与反例，或在[配套练习目录](examples/README.md)中按章节复做。

示例使用教学数据。软件使用 [MIT 许可证](LICENSE)。
