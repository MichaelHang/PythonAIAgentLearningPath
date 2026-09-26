"""Agent 核心循环：Day 4 Function Calling + Day 6 ReAct + Day 9 记忆 的服务化组装"""

import json
from typing import Any, Dict, List

from . import config
from .llm import chat, 取回答
from .memory import MEMORY
from .tools import execute_tool, get_tool_list

MAX_TOOL_ROUNDS = 5
SYSTEM_PROMPT = "你是智能开发助手。可以调用工具完成计算和文件操作，回答要简洁准确。"


async def run_agent(session_id: str, user_input: str) -> Dict[str, Any]:
    """处理一次用户输入，返回 {"answer": ..., "tool_calls": [...]}（见 schemas.ChatResponse）

    完整流程（TODO 4.1，按伪代码实现）：
    1. memory = MEMORY.get(session_id)；memory.add("user", user_input)
    2. messages = [system] + memory.to_api_format()
    3. for 轮 in range(MAX_TOOL_ROUNDS):
         resp = await chat(messages, tools=get_tool_list())
         message = resp["choices"][0]["message"]
         如果没有 tool_calls → 最终回答：
             memory.add("assistant", 回答)；返回 {"answer": 回答, "tool_calls": tool_records}
         否则：
             messages.append(message)
             对每个 tool_call：execute_tool 执行 → 结果以 role=tool 消息回填 messages
             （同时把 (工具名, 参数, 结果) 记进 tool_records——前端要用）
    4. 循环耗尽 → 返回"达到最大工具调用轮数"（Day 4 同款保护）

    错误处理约定（TODO 4.2）：
    - llm.LLMError 不在本层捕获——上抛给 main.py 统一转 HTTP 错误
    - 工具执行失败不崩溃——execute_tool 已保证返回错误字符串
    """
    memory = MEMORY.get(session_id)
    memory.add("user", user_input)
    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *memory.to_api_format(),
    ]

    tool_records: List[Dict] = []

    # TODO 4.1：实现上面的循环（删除下面两行）
    raise NotImplementedError("TODO 4.1：实现 Agent 核心循环")
