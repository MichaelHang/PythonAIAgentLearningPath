"""
Day 10 练习：多工具 Agent 综合实战（阶段二收尾）
验收标准：
1. 集成至少 4 个工具
2. ReAct 循环 + 条件路由
3. 对话记忆（短期 10 轮 + 长期向量存储）
4. 流式输出
5. 错误恢复（工具调用失败自动重试）
6. Token 消耗有记录

这是 Day 1-9 所有知识的综合运用！
"""

import asyncio
import json
import time
import functools
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum


# ==================== 任务 1：定义所有数据结构 ====================

@dataclass
class ToolResult:
    """工具调用结果"""
    tool_name: str
    arguments: Dict
    output: str
    success: bool
    retry_count: int = 0
    latency_ms: float = 0.0


@dataclass
class LLMCallRecord:
    """LLM 调用记录"""
    prompt_tokens: int
    completion_tokens: int
    model: str
    latency_ms: float
    input_snapshot: str = ""  # 简化版，存前 200 字符


@dataclass
class AgentStep:
    """Agent 执行步骤"""
    step_num: int
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""
    tool_results: List[ToolResult] = field(default_factory=list)
    llm_calls: List[LLMCallRecord] = field(default_factory=list)


@dataclass 
class AgentMetrics:
    """Agent 运行指标"""
    total_steps: int = 0
    total_tool_calls: int = 0
    total_tool_errors: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_estimate: float = 0.0  # 估算费用（元）
    start_time: float = 0.0
    end_time: float = 0.0


# ==================== 任务 2：实现工具系统（至少 4 个工具） ====================

TOOLS_REGISTRY: Dict[str, Dict] = {}


def tool(name: str, description: str, max_retries: int = 2):
    """带重试的工具注册装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs),
                        timeout=30
                    )
                    return str(result)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)  # 重试前等待
            return f"工具执行失败（重试{max_retries}次后）: {last_error}"
        
        TOOLS_REGISTRY[name] = {
            "function": wrapper,
            "description": description,
            "max_retries": max_retries,
        }
        return wrapper
    return decorator


# TODO 2.1：注册至少 4 个工具
# 提示：可以注册计算器、天气、文件读写、代码执行等

@tool("calculator", "执行四则运算")
def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


@tool("weather", "查询城市天气")
def weather(city: str) -> str:
    return {"北京": "晴 25°C", "上海": "多云 22°C"}.get(city, f"{city} 未知")


# TODO 2.2：继续注册更多工具
# @tool("read_file", "读取文件内容")
# @tool("search_web", "网页搜索")
# @tool("execute_python", "执行 Python 代码")


# ==================== 任务 3：实现 ReAct 循环 + 条件路由 ====================

async def react_agent_with_memory(
    user_input: str,
    tools: List[Dict],
    memory,
    max_steps: int = 10,
    stream: bool = True,
) -> str:
    """
    ReAct Agent 主循环（集合 Day 1-9 所学）
    
    功能：
    1. async/await 异步调用（Day 1）
    2. 装饰器注册工具（Day 2）
    3. 流式输出（Day 3）
    4. LLM API 调用（Day 4）
    5. ReAct 循环 + 条件路由（Day 6 + Day 7）
    6. 记忆系统集成（Day 9）
    7. 错误恢复（重试）
    8. Token 统计
    """
    # TODO 3.1：实现 Agent 主循环
    # 提示：这是 Day 1-9 的综合，可以逐步组装
    
    metrics = AgentMetrics(start_time=time.time())
    steps: List[AgentStep] = []
    
    # 1. 获取短期记忆
    recent_messages = memory.short_memory.to_api_format()
    
    # 2. 检索相关知识
    # knowledge = memory.rag.retrieve(user_input)
    
    # 3. ReAct 循环
    for step_num in range(max_steps):
        # TODO: 实现每一步
        pass
    
    metrics.end_time = time.time()
    print_metrics(metrics)
    return "最终回答"


# ==================== 任务 4：实现 Token 统计 ====================

def print_metrics(metrics: AgentMetrics):
    """打印 Agent 运行指标"""
    # TODO 4.1：美化打印
    print(f"📊 运行统计：")
    print(f"  ⏱ 耗时：{metrics.end_time - metrics.start_time:.2f} 秒")
    print(f"  🔧 工具调用：{metrics.total_tool_calls} 次（错误 {metrics.total_tool_errors} 次）")
    print(f"  💰 Token：prompt {metrics.total_prompt_tokens} + completion {metrics.total_completion_tokens}")
    print(f"  💰 估算费用：¥{metrics.total_cost_estimate:.4f}")


# ==================== 任务 5：实现错误恢复 ====================

class ErrorRecoveryStrategy(Enum):
    """错误恢复策略"""
    RETRY = "retry"           # 重试
    FALLBACK = "fallback"     # 降级
    SKIP = "skip"            # 跳过
    ABORT = "abort"          # 终止


async def execute_tool_with_recovery(
    tool_name: str,
    arguments: Dict,
    max_retries: int = 2,
) -> ToolResult:
    """
    带错误恢复的工具执行
    
    策略：
    1. 第 1 次失败 → 重试
    2. 第 2 次失败 → 返回错误信息给 LLM（让 LLM 自己修正）
    3. 不会直接崩溃
    """
    # TODO 5.1：实现错误恢复
    pass


# ==================== 主函数 ====================

async def main():
    print("=" * 60)
    print("Day 10 练习：多工具 Agent 综合实战")
    print("=" * 60)
    
    # TODO 6.1：编写完整测试
    print("\n📝 集成测试（自行完成）")
    print("  测试 1：普通对话")
    print("  测试 2：单个工具调用")
    print("  测试 3：多工具并发调用")
    print("  测试 4：多轮对话 + 记忆")
    print("  测试 5：错误恢复")
    print("  测试 6：Token 统计")
    
    print("\n" + "=" * 60)
    print("💡 提示：这是 Day 1-9 的综合练习")
    print("  把之前每个 Day 写的模块拼装起来即可")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
