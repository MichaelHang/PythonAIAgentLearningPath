"""
Day 6 练习：不依赖框架，纯 Python 手写一个 ReAct Agent 循环
验收标准：
1. 必须实现 ReAct 循环（Reasoning + Acting 交替）
2. 循环必须有 max_steps 上限（防止无限循环）
3. 必须支持工具调用（至少 2 个工具）
4. 必须使用 async/await（异步 LLM 调用）
5. 必须正确解析 LLM 的 Thought/Action/Action Input/Observation 格式
6. 最终输出 Final Answer
"""

import asyncio
import json
import re
import functools
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field


# ==================== 数据结构 ====================

@dataclass
class ToolResult:
    """工具调用结果"""
    tool_name: str
    tool_input: str
    output: str
    success: bool


@dataclass
class AgentStep:
    """Agent 单步执行记录"""
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""
    full_response: str = ""


# ==================== 任务 1：实现工具注册和调用 ====================

# 全局工具注册表
TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str):
    """工具注册装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        TOOLS_REGISTRY[name] = {
            "function": wrapper,
            "description": description,
            "parameters": func.__code__.co_varnames[:func.__code__.co_argcount]
        }
        return wrapper
    return decorator


# TODO 1.1：注册至少 2 个工具
# 提示：参考 Day 2 的写法，定义计算器工具和天气查询工具

@tool("Calculator", "执行四则运算，例如：Calculator[3 + 5 * 2]")
def calculator(expression: str) -> str:
    """计算器工具"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"错误: {e}"


@tool("Weather", "查询城市天气，例如：Weather[北京]")
def weather(city: str) -> str:
    """天气查询工具（模拟）"""
    # 模拟天气数据
    天气数据 = {
        "北京": "晴，25°C",
        "上海": "多云，22°C",
        "深圳": "雨，28°C",
    }
    return 天气数据.get(city, f"{city} 的天气数据未找到")


def get_tools_description() -> str:
    """生成工具描述文本（放入 System Prompt）"""
    # TODO 1.2：实现工具描述生成
    # 格式：
    # Calculator[参数]: 描述
    # Weather[参数]: 描述
    pass


def execute_tool(tool_name: str, tool_input: str) -> ToolResult:
    """执行工具调用"""
    # TODO 1.3：实现工具执行逻辑
    # 1. 从 TOOLS_REGISTRY 查找工具
    # 2. 调用工具的 "function"
    # 3. 返回 ToolResult
    pass


# ==================== 任务 2：实现 ReAct Prompt 构建 ====================

def build_react_prompt(user_input: str, steps: List[AgentStep]) -> str:
    """
    构建 ReAct 格式的 Prompt
    
    ReAct 格式：
    Question: [用户问题]
    
    Thought: [推理过程]
    Action: [工具名]
    Action Input: [工具输入]
    Observation: [工具返回结果]
    
    ...（可重复多轮）
    
    Thought: [最终推理]
    Final Answer: [最终答案]
    """
    # TODO 2.1：实现 ReAct Prompt 构建
    # 提示：
    # 1. System Prompt 包含工具描述和 ReAct 格式说明
    # 2. 把历史 steps 格式化为 Thought/Action/Observation 序列
    # 3. 最后加上当前问题
    pass


# ==================== 任务 3：实现 ReAct 格式解析 ====================

def parse_react_response(response: str) -> Tuple[str, str, str]:
    """
    解析 LLM 返回的 ReAct 格式文本
    
    返回：(thought, action, action_input)
    - 如果包含 "Final Answer:"，说明是最终回答，action 为空
    - 否则解析 Action 和 Action Input
    
    示例响应：
    Thought: 我需要计算 3 + 5 的值
    Action: Calculator
    Action Input: 3 + 5 * 2
    """
    # TODO 3.1：实现 ReAct 响应解析
    # 提示：
    # 1. 用正则或字符串查找提取 Thought、Action、Action Input
    # 2. 检查是否包含 "Final Answer"（区分大小写）
    # 3. 返回 (thought, action, action_input)
    #    如果 action 为空，说明是最终回答，此时 action_input 存最终答案
    pass


# ==================== 任务 4：实现 ReAct Agent 主循环 ====================

async def react_agent(
    user_input: str,
    max_steps: int = 10,
    verbose: bool = True,
) -> str:
    """
    纯 Python 实现的 ReAct Agent 主循环
    
    流程：
    1. 初始化 steps = []
    2. for step in range(max_steps):
    3.   构建 prompt（build_react_prompt）
    4.   调用 LLM（模拟或真实 API）
    5.   解析响应（parse_react_response）
    6.   如果是 Final Answer → 返回结果，结束
    7.   否则执行工具（execute_tool）
    8.   把结果加入 steps，继续循环
    9. 如果超过 max_steps → 返回错误信息
    """
    steps: List[AgentStep] = []
    
    # TODO 4.1：实现 ReAct Agent 主循环
    # 提示：这里是整个 Agent 的核心！
    # 注意：LLM 调用可以用模拟函数（见下方 mock_llm_call）
    
    pass


# ==================== 模拟 LLM（用于测试，不依赖真实 API） ====================

async def mock_llm_call(prompt: str) -> str:
    """
    模拟 LLM 调用（用于本地测试，不消耗 API 额度）
    
    根据 prompt 的内容，返回一个符合 ReAct 格式的模拟响应
    用于测试 ReAct 循环逻辑是否正确
    """
    # 检测是否包含计算相关问题
    if "计算" in prompt or "加" in prompt or "减" in prompt or "+" in prompt:
        return """Thought: 我需要计算这个表达式的结果
Action: Calculator
Action Input: 3 + 5 * 2"""
    
    if "天气" in prompt:
        return """Thought: 我需要查询北京的天气
Action: Weather
Action Input: 北京"""
    
    # 默认最终回答
    return """Thought: 我已经通过工具调用获得了所需信息
Final Answer: 根据查询结果，答案是 13。"""


# ==================== 任务 5：用真实 LLM API 替换 mock ====================
# （可选，有 API key 再做；先用 mock 把逻辑跑通）

async def real_llm_call(prompt: str, api_key: str = "") -> str:
    """
    真实 LLM API 调用（OpenAI 兼容格式）
    
    支持：DeepSeek、Qwen、Moonshot 等
    """
    # TODO 5.1：实现真实 LLM 调用
    # 提示：
    # 1. 用 aiohttp 或 httpx 发送异步 HTTP 请求
    # 2. API 格式兼容 OpenAI：
    #    POST https://api.deepseek.com/chat/completions
    #    Headers: {"Authorization": f"Bearer {api_key}"}
    #    Body: {"model": "...", "messages": [{"role": "user", "content": prompt}]}
    # 3. 返回 response.json()["choices"][0]["message"]["content"]
    pass


# ==================== 主函数：测试 Agent ====================

async def main():
    print("=" * 60)
    print("Day 6 练习：纯 Python 手写 ReAct Agent")
    print("=" * 60)
    
    # 测试用例 1：计算问题
    print("\n📝 测试 1：计算问题")
    print("用户：帮我计算 3 + 5 * 2 等于多少？")
    
    答案 = await react_agent(
        user_input="帮我计算 3 + 5 * 2 等于多少？",
        max_steps=5,
        verbose=True,
    )
    print(f"\n✅ Agent 最终回答：{答案}")
    
    # 测试用例 2：天气问题
    print("\n\n📝 测试 2：天气查询")
    print("用户：北京今天天气怎么样？")
    
    答案 = await react_agent(
        user_input="北京今天天气怎么样？",
        max_steps=5,
        verbose=True,
    )
    print(f"\n✅ Agent 最终回答：{答案}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！现在运行 python day06_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
