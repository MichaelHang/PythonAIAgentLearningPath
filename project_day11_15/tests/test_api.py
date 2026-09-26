"""Day 14：API 集成测试——用 monkeypatch 替换 LLM，不烧一分钱

运行方式：pip install pytest httpx 后，pytest tests/test_api.py -v
核心技巧：把 app.llm.chat 替换成返回固定响应的假函数，
         这样可以测试完整的 路由 → Agent → 响应 链路而不依赖真实 API。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app import agent, llm
from app.main import app

client = TestClient(app)


def fake_llm_response(content="好的，这是 mock 回答。"):
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture
def mock_llm(monkeypatch):
    """把 LLM 替换成固定回答——测试不依赖真实 API"""

    async def _fake_chat(messages, tools=None, max_tokens=None):
        return fake_llm_response()

    monkeypatch.setattr(llm, "chat", _fake_chat)
    # agent.py 里是 from .llm import chat 导入的，还要替换它持有的引用
    monkeypatch.setattr(agent, "chat", _fake_chat)


def test_health(mock_llm):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_正常回答(mock_llm):
    # TODO 7.2：Day 12/14 完成后此测试应变绿
    resp = client.post("/chat", json={"session_id": "test-1", "message": "你好"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["session_id"] == "test-1"


def test_chat_多轮记忆(mock_llm):
    client.post("/chat", json={"session_id": "mem-1", "message": "我叫小明"})
    resp = client.post("/chat", json={"session_id": "mem-1", "message": "你好"})
    assert resp.status_code == 200


def test_chat_空消息被校验拦截():
    resp = client.post("/chat", json={"session_id": "v", "message": ""})
    assert resp.status_code == 422  # Pydantic min_length=1 自动拦截


def test_chat_错误返回结构化JSON():
    # 不打 mock：/chat 内部抛 NotImplementedError 之类 → 应返回 4xx/5xx 而非裸 traceback
    resp = client.post("/chat", json={"session_id": "err", "message": "hi"})
    assert resp.status_code >= 400
    assert "detail" in resp.json()
