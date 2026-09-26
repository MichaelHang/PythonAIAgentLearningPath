"""会话记忆：session_id → 会话隔离（Day 9 短期记忆的服务化版本）

关键差异：脚本版用全局变量，服务版必须按 session_id 隔离——
不同用户的对话历史绝不能串。
"""

import time
from typing import Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class ConversationMessage:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)


class SessionMemory:
    """单个会话的短期记忆（Day 9 原题，多了 max_messages 上限）"""

    def __init__(self, session_id: str, max_messages: int = 20):
        self.session_id = session_id
        self.max_messages = max_messages
        self.messages: List[ConversationMessage] = [
            ConversationMessage(role="system", content="你是智能开发助手，可以使用工具回答问题。")
        ]

    def add(self, role: str, content: str):
        """TODO 3.1：追加消息 + 超限裁剪（system 永远保留）——Day 9 原题"""
        raise NotImplementedError("TODO 3.1")

    def to_api_format(self) -> List[Dict]:
        """TODO 3.2：转成 [{"role": ..., "content": ...}, ...]"""
        raise NotImplementedError("TODO 3.2")


class MemoryStore:
    """多会话管理：session_id → SessionMemory"""

    def __init__(self):
        self._sessions: Dict[str, SessionMemory] = {}

    def get(self, session_id: str) -> SessionMemory:
        """TODO 3.3：取会话记忆，不存在则创建（注意：不能返回 None）"""
        raise NotImplementedError("TODO 3.3")

    def clear(self, session_id: str):
        """TODO 3.4：清空指定会话（保留该会话的 system 消息）"""
        raise NotImplementedError("TODO 3.4")


# 进程内单例（单进程部署够用；多进程/多实例部署时换成 Redis——面试常问）
MEMORY = MemoryStore()
