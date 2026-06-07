"""
Day 5 练习：命令行 AI 助手（阶段一综合实战）
验收标准：
1. 用户在命令行输入自然语言，程序能理解意图
2. 支持至少 2 个工具调用（计算器、天气查询等）
3. 工具调用使用 Function Calling 机制
4. 异步并发处理多个工具调用（asyncio.gather）
5. LLM 响应支持流式输出（yield chunk by chunk）
6. 所有数据结构用 Pydantic 定义
7. 有基本的错误处理
8. 代码有类型注解
"""

import asyncio
import json
import sys
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


# ==================== 任务 1：用 Pydantic 定义所有数据结构 ====================

class ToolCall(BaseModel):
    """工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色：system/user/assistant/tool")
    content: Optional[str] = Field(None, description="消息内容")
    tool_calls: Optional[List[Dict]] = Field(None, description="工具调用（assistant 消息）")
    tool_call_id: Optional[str] = Field(None, description="工具调用 ID（tool 消息）")


class AgentConfig(BaseModel):
    """Agent 配置"""
    model: str = Field("deepseek-chat", description="LLM 模型名称")
    max_tokens: int = Field(4096, description="最大 token 数")
    temperature: float = Field(0.7, description="温度参数")
    max_tool_rounds: int = Field(5, description="最大工具调用轮数")


# TODO 1.1：定义更多 Pydantic 模型
# 提示：可以定义 ToolResult、AgentState 等


# ==================== 任务 2：实现工具系统 ====================

# 全局工具注册表
TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str):
    """工具注册装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        TOOLS_REGISTRY[name] = {
            "function": wrapper,
            "description": description,
        }
        return wrapper
    return decorator


# TODO 2.1：注册至少 2 个工具
# 提示：参考 Day 2 的写法，定义计算器和天气查询工具

@tool("calculator", "执行四则运算，例如：3 + 5 * 2")
def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


@tool("weather", "查询城市天气，例如：北京")
def weather(city: str) -> str:
    天气数据 = {"北京": "晴 25°C", "上海": "多云 22°C", "深圳": "雨 28°C"}
    return 天气数据.get(city, f"{city} 天气未知")


def get_tools_for_api() -> List[Dict]:
    """生成 OpenAI Function Calling 格式的 tools 参数"""
    # TODO 2.2：实现 tools 格式转换
    pass


def execute_tool(tool_name: str, tool_input: Dict) -> str:
    """执行工具调用"""
    # TODO 2.3：实现工具执行
    pass


# ==================== 任务 3：实现流式 LLM 客户端 ====================

class StreamingLLMClient:
    """流式 LLM 客户端"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.api_key = "fake_key"  # 真实场景从环境变量读取
    
    async def chat(
        self, 
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        聊天（流式输出）
        
        需求：
        1. 发送请求到 LLM API
        2. 逐 chunk 解析响应
        3. 用 yield 产出每个 chunk 的内容
        4. 如果碰到 tool_calls，yield 特殊标记
        
        提示：可以先 mock，后续换成真实 API
        """
        # TODO 3.1：实现流式 chat（先用 mock）
        # 提示：
        # async for chunk in 模拟流式响应():
        #     yield chunk
        pass
    
    async def _mock_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        """模拟流式输出（用于测试）"""
        response = "我需要计算 3 + 5 * 2 的结果。"
        for char in response:
            await asyncio.sleep(0.05)
            yield char
        yield "\n"
        
        # 模拟 tool call
        yield '[TOOL_CALL] calculator: {"expression": "3+5*2"}'
    
    async def _call_real_api(
        self, 
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """真实 API 调用（流式）"""
        # TODO 3.2：实现真实 API 流式调用
        # 提示：
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(..., json={...}) as resp:
        #         async for chunk in resp.content.iter_any():
        #             # 解析 SSE 格式
        #             yield 解析后的内容
        pass


# ==================== 任务 4：实现 Agent 主循环 ====================

class CLI_Agent:
    """命令行 AI 助手 Agent"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = StreamingLLMClient(config)
        self.messages: List[ChatMessage] = []
        
        # 初始化 system message
        self.messages.append(ChatMessage(
            role="system",
            content="你是一个有用的 AI 助手。可以使用工具来回答问题。"
        ))
    
    async def chat(self, user_input: str, stream: bool = True) -> str:
        """
        处理用户输入，返回最终回答
        
        流程：
        1. 添加用户消息到 messages
        2. 调用 LLM（流式）
        3. 如果 LLM 返回 tool_calls：
           a. 解析 tool_calls
           b. 执行每个工具
           c. 将结果作为 tool role 消息添加到 messages
           d. 再次调用 LLM（最多 max_tool_rounds 轮）
        4. 返回最终回答
        """
        # 添加用户消息
        self.messages.append(ChatMessage(role="user", content=user_input))
        
        # TODO 4.1：实现 Agent 主循环
        # 提示：这是综合练习的核心！
        # 需要结合 Day 4 的 Function Calling 循环 和 本 Day 的流式输出
        
        # 伪代码：
        # for round in range(self.config.max_tool_rounds):
        #     full_response = ""
        #     async for chunk in self.client.chat(self.messages, tools=get_tools_for_api()):
        #         if chunk.startswith("[TOOL_CALL]"):
        #             # 解析并执行工具
        #             # 添加 tool 消息，继续循环
        #         else:
        #             full_response += chunk
        #             if stream:
        #                 print(chunk, end="", flush=True)
        #     
        #     if 没有 tool_calls:
        #         return full_response
        # 
        # return "达到最大工具调用轮数"
        
        pass
    
    def clear_history(self):
        """清除对话历史（保留 system message）"""
        self.messages = [self.messages[0]]


# ==================== 任务 5：实现命令行交互界面 ====================

async def run_cli():
    """运行命令行交互界面"""
    config = AgentConfig()
    agent = CLI_Agent(config)
    
    print("=" * 60)
    print("🤖 命令行 AI 助手（Day 5 综合实战）")
    print("=" * 60)
    print("输入 'exit' 或 'quit' 退出")
    print("输入 'clear' 清除对话历史")
    print()
    
    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("exit", "quit", "退出"):
            print("👋 再见！")
            break
        
        if user_input.lower() == "clear":
            agent.clear_history()
            print("🗑️ 对话历史已清除")
            continue
        
        print("助手：", end="")
        try:
            response = await agent.chat(user_input, stream=True)
            if not response:  # 如果已经流式打印了
                print()  # 换行
            else:
                print(response)
        except Exception as e:
            print(f"\n❌ 错误：{e}")
        print()


# ==================== 主函数 ====================

async def main():
    """测试函数（不启动 CLI，直接测试功能）"""
    print("=" * 60)
    print("Day 5 练习：命令行 AI 助手（综合测试）")
    print("=" * 60)
    
    config = AgentConfig()
    agent = CLI_Agent(config)
    
    # 测试 1：普通对话（不需要工具）
    print("\n📝 测试 1：普通对话")
    print("用户：你好！")
    response = await agent.chat("你好！请介绍一下你自己。", stream=True)
    print(f"\n✅ 测试 1 完成")
    agent.clear_history()
    
    # 测试 2：需要工具调用的问题
    print("\n📝 测试 2：工具调用")
    print("用户：帮我计算 3 + 5 * 2")
    response = await agent.chat("帮我计算 3 + 5 * 2", stream=True)
    print(f"\n✅ 测试 2 完成")
    agent.clear_history()
    
    # 测试 3：多轮对话
    print("\n📝 测试 3：多轮对话")
    print("用户：北京今天天气怎么样？")
    response = await agent.chat("北京今天天气怎么样？", stream=True)
    print(f"\n✅ 测试 3 完成")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！现在运行 python day05_practice_validator.py 验收")
    print("=" * 60)
    print("\n提示：要启动交互式 CLI，请运行：")
    print("  asyncio.run(run_cli())")


if __name__ == "__main__":
    # 选择运行模式：
    # 1. 直接运行 main() 做自动化测试
    # 2. 取消下面一行的注释，运行交互式 CLI
    
    # asyncio.run(run_cli())  # ← 取消注释来启动交互式 CLI
    
    asyncio.run(main())  # ← 默认运行自动化测试
