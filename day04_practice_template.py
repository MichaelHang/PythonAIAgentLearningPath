"""
Day 4 练习：实现支持 Function Calling 的 LLM 客户端
验收标准：
1. 能调用 LLM API（OpenAI 兼容格式）
2. 请求中包含 tools 参数（Function Calling 格式）
3. 能解析 LLM 返回的 tool_calls
4. 能根据 tool_calls 执行对应函数
5. 能将函数执行结果返回给 LLM（追加 tool role 消息）
6. 有错误处理和重试机制
7. 代码有类型注解
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass


# ==================== 数据结构 ====================

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


# ==================== 任务 1：实现工具注册表 ====================

# 全局工具注册表
TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, parameters: Optional[Dict] = None):
    """工具注册装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 注册工具
        TOOLS_REGISTRY[name] = {
            "function": wrapper,
            "description": description,
            "parameters": parameters or {},
        }
        return wrapper
    return decorator


# TODO 1.1：注册至少 2 个工具
# 提示：参考 Day 2 的写法

@tool(
    name="get_weather",
    description="获取指定城市的天气信息",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称，如：北京"}
        },
        "required": ["city"]
    }
)
def get_weather(city: str) -> str:
    """获取天气"""
    天气数据 = {"北京": "晴 25°C", "上海": "多云 22°C"}
    return 天气数据.get(city, f"{city} 天气未知")


@tool(
    name="calculator",
    description="执行四则运算",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "运算表达式"}
        },
        "required": ["expression"]
    }
)
def calculator(expression: str) -> str:
    """计算器"""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


def get_tools_for_api() -> List[Dict]:
    """生成 OpenAI Function Calling 格式的 tools 参数"""
    # TODO 1.2：实现 tools 格式转换
    # 提示：返回格式
    # [
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "...",
    #             "description": "...",
    #             "parameters": {...}
    #         }
    #     }
    # ]
    pass


# ==================== 任务 2：实现 LLM API 调用 ====================

async def call_llm(
    messages: List[Dict],
    tools: Optional[List[Dict]] = None,
    api_key: str = "fake_key",
    base_url: str = "https://api.deepseek.com",
    model: str = "deepseek-chat",
) -> Dict:
    """
    调用 LLM API（OpenAI 兼容格式）
    
    需求：
    1. 用 aiohttp 发送 POST 请求
    2. 请求体包含 model、messages、tools（如果有）
    3. 返回响应 JSON
    
    提示：如果没有 aiohttp，可以用模拟响应（见下方 mock）
    """
    # TODO 2.1：实现 LLM API 调用
    # 提示：
    # import aiohttp
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(
    #         f"{base_url}/chat/completions",
    #         headers={"Authorization": f"Bearer {api_key}"},
    #         json={"model": model, "messages": messages, "tools": tools}
    #     ) as resp:
    #         return await resp.json()
    
    # 如果没有 aiohttp，返回模拟响应
    return mock_llm_response(messages, tools)


def mock_llm_response(messages: List[Dict], tools: Optional[List]) -> Dict:
    """模拟 LLM 响应（用于测试）"""
    user_msg = ""
    for msg in messages:
        if msg["role"] == "user":
            user_msg = msg["content"]
    
    # 检测是否包含工具调用
    if tools and ("天气" in user_msg or "计算" in user_msg or "加" in user_msg):
        # 模拟 tool_calls 响应
        tool_name = "get_weather" if "天气" in user_msg else "calculator"
        tool_input = {"city": "北京"} if tool_name == "get_weather" else {"expression": "3+5*2"}
        
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_001",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_input, ensure_ascii=False)
                                }
                            }
                        ]
                    }
                }
            ]
        }
    
    # 模拟普通文本响应
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "根据查询结果，答案是 13。"
                }
            }
        ]
    }


# ==================== 任务 3：实现 tool_calls 解析和执行 ====================

def parse_tool_calls(response: Dict) -> List[Dict]:
    """
    解析 LLM 响应中的 tool_calls
    
    返回：
    [
        {
            "id": "call_001",
            "name": "get_weather",
            "arguments": {"city": "北京"}
        }
    ]
    """
    # TODO 3.1：实现 tool_calls 解析
    # 提示：
    # 1. 从 response["choices"][0]["message"]["tool_calls"] 获取
    # 2. 每个 tool_call 的 function.arguments 是 JSON 字符串，需要 json.loads()
    # 3. 返回解析后的列表
    pass


def execute_tool_call(tool_call: Dict) -> Any:
    """
    执行单个 tool_call
    
    需求：
    1. 从 TOOLS_REGISTRY 查找工具函数
    2. 调用函数，传入解析后的参数
    3. 返回执行结果
    """
    # TODO 3.2：实现工具执行
    # 提示：
    # 1. tool_name = tool_call["name"]
    # 2. func = TOOLS_REGISTRY[tool_name]["function"]
    # 3. result = func(**arguments)
    # 4. return result
    pass


# ==================== 任务 4：实现完整的 Function Calling 循环 ====================

async def chat_with_function_calling(
    user_message: str,
    max_rounds: int = 5,
    verbose: bool = True,
) -> str:
    """
    完整的 Function Calling 对话循环
    
    流程：
    1. 构建 messages（system + user）
    2. 调用 LLM（带 tools）
    3. 如果响应有 tool_calls：
       a. 解析 tool_calls
       b. 执行每个工具调用
       c. 将结果作为 tool role 消息追加到 messages
       d. 再次调用 LLM（不带 tools，或继续带）
       e. 重复直到没有 tool_calls 或达到最大轮数
    4. 返回最终回答
    """
    # TODO 4.1：实现完整的 Function Calling 循环
    # 提示：这是核心函数！
    pass


# ==================== 任务 5：用真实 API 测试（可选） ====================

async def chat_with_real_api(
    user_message: str,
    api_key: str,
    base_url: str = "https://api.deepseek.com",
) -> str:
    """用真实 API 测试（需要 API Key）"""
    # TODO 5.1：实现真实 API 调用
    # 提示：先确保 mock 版本能跑通，再换成真实 API
    pass


# ==================== 主函数：测试 ====================

async def main():
    print("=" * 60)
    print("Day 4 练习：Function Calling LLM 客户端")
    print("=" * 60)
    
    # 测试 1：查看注册的工具
    print("\n📝 测试 1：查看注册的工具")
    tools = get_tools_for_api()
    print(f"注册了 {len(tools)} 个工具：")
    for t in tools:
        print(f"  - {t['function']['name']}: {t['function']['description']}")
    
    # 测试 2：完整对话（使用 mock）
    print("\n📝 测试 2：Function Calling 对话")
    print("用户：北京今天天气怎么样？")
    
    回答 = await chat_with_function_calling(
        user_message="北京今天天气怎么样？",
        verbose=True,
    )
    print(f"\n✅ 最终回答：{回答}")
    
    # 测试 3：计算问题
    print("\n📝 测试 3：计算问题")
    print("用户：帮我计算 3 + 5 * 2")
    
    回答 = await chat_with_function_calling(
        user_message="帮我计算 3 + 5 * 2",
        verbose=True,
    )
    print(f"\n✅ 最终回答：{回答}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！现在运行 python day04_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
