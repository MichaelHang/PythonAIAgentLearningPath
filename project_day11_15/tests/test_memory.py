"""Day 14：单元测试——纯逻辑层，无网络、无 Key 也能跑

运行方式（在 project_day11_15 目录下）：
    pip install pytest
    pytest tests/ -v

说明：这些测试在 Day 12 的 TODO 完成前会失败（红）——
这就是测试驱动的工作方式：完成 TODO → 测试变绿。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 让 tests 能 import app

from app.memory import MemoryStore, SessionMemory


def test_初始带_system消息():
    m = SessionMemory("t1")
    assert m.messages[0].role == "system"


def test_超限裁剪保留system与最新():
    m = SessionMemory("t2", max_messages=4)
    m.add("system", "你是助手")
    for i in range(5):
        m.add("user", f"消息{i}")
    assert len(m.messages) <= 4
    assert m.messages[0].role == "system"
    assert m.messages[-1].content == "消息4"


def test_to_api_format():
    m = SessionMemory("t3")
    m.add("user", "你好")
    fmt = m.to_api_format()
    assert isinstance(fmt, list) and fmt[0]["role"] == "system"
    assert fmt[-1] == {"role": "user", "content": "你好"}


def test_会话隔离():
    store = MemoryStore()
    a = store.get("sess-a")
    b = store.get("sess-b")
    a.add("user", "只属于A的秘密")
    assert all("只属于A的秘密" not in msg.content for msg in b.messages), "两个会话的记忆串了！"


def test_get_同一session返回同一实例():
    store = MemoryStore()
    assert store.get("s") is store.get("s")
