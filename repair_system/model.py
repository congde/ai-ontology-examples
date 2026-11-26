"""Read-only model proposal adapter for the equipment alarm exercise."""

from contextlib import closing
import http.client
import json
import os
from urllib.parse import urlsplit


TASK = "核查告警 A-001，必要时准备维修工单"


def model_proposal():
    url = urlsplit(os.environ.get("MODEL_CHAT_URL", ""))
    model = os.environ.get("MODEL_NAME", "")
    key = os.environ.get("MODEL_API_KEY")
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not model or not url.hostname or not url.path
            or url.username or url.password or url.fragment
            or (url.scheme != "https" and not (local and url.scheme == "http"))):
        raise ValueError("请配置完整模型地址和模型名，远程地址须使用 HTTPS")

    messages = [
        {"role": "system", "content": '只可提议只读工具。仅输出单个 JSON 对象，'
         '格式为 {"tool":"read_evidence","alarm_id":"告警编号"}。'},
        {"role": "user", "content": TASK},
    ]
    payload = json.dumps({"model": model, "messages": messages})
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    connect = (http.client.HTTPSConnection if url.scheme == "https"
               else http.client.HTTPConnection)
    target = url.path + ("?" + url.query if url.query else "")
    with closing(connect(url.hostname, url.port, timeout=20)) as conn:
        conn.request("POST", target, payload, headers)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f"模型 HTTP 状态 {response.status}")
        data = json.loads(response.read())
    return json.loads(data["choices"][0]["message"]["content"])
