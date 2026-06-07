"""
Day 8 练习：实现一个 MCP Server + 在 Agent 中集成 MCP 工具
验收标准：
1. 使用 mcp Python SDK 创建 MCP Server
2. 定义了至少 2 个 Tool
3. Tool 有清晰的 name、description、inputSchema
4. Agent 能连接 MCP Server 并列出工具
5. Agent 能调用 MCP 工具并获取结果
6. 工具函数有超时控制

安装依赖：
    pip install mcp
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional


# ==================== 任务 1：用 MCP SDK 定义工具 ====================

# TODO 1.1：安装 mcp 库
# pip install mcp

# 如果你已经安装了 mcp，可以用 mcp SDK 的方式定义工具：

"""
from mcp.server import Server
from mcp.types import Tool, TextContent

# 创建 MCP Server 实例
mcp_server = Server("my-agent-tools")

@mcp_server.tool()
async def calculator(expression: str) -> str:
    \"\"\"执行四则运算\"\"\"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"

@mcp_server.tool()
async def read_file(path: str) -> str:
    \"\"\"读取文件内容\"\"\"
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

@mcp_server.tool()
async def write_file(path: str, content: str) -> str:
    \"\"\"写入文件\"\"\"
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"文件已写入: {path}"
    except Exception as e:
        return f"写入文件失败: {e}"
"""


# ==================== 任务 2：模拟 MCP Server（不依赖 SDK） ====================

class MockMCPServer:
    """模拟 MCP Server（用于学习和测试，不依赖 mcp SDK）"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Dict] = {}
    
    def tool(self, name: str, description: str):
        """注册工具的装饰器（模拟 MCP SDK 的 @server.tool()）"""
        def decorator(func):
            import functools
            
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 超时控制
                try:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs) if asyncio.iscoroutine(func(*args, **kwargs))
                        else asyncio.to_thread(func, *args, **kwargs),
                        timeout=30
                    )
                    return result
                except asyncio.TimeoutError:
                    return "工具执行超时"
                except Exception as e:
                    return f"工具执行错误: {e}"
            
            # 注册到工具表
            self.tools[name] = {
                "name": name,
                "description": description,
                "function": wrapper,
            }
            return wrapper
        return decorator
    
    def get_tool_list(self) -> List[Dict]:
        """获取工具列表（OpenAI Function Calling 格式）"""
        # TODO 2.1：实现工具列表生成
        pass
    
    async def call_tool(self, name: str, arguments: Dict) -> str:
        """调用工具"""
        # TODO 2.2：实现工具调用
        pass


# TODO 2.3：创建 MCP Server 并注册工具
# 提示：
# server = MockMCPServer("my-tools")
# @server.tool("calculator", "执行四则运算")
# async def calculator(expression: str):
#     ...

mcp_server = MockMCPServer("my-agent-tools")


# ==================== 任务 3：实现 MCP 客户端 ====================

class MCPClient:
    """MCP 客户端：连接 MCP Server 并调用工具"""
    
    def __init__(self):
        self.server = mcp_server  # 模拟连接
        self.tools_cache: List[Dict] = []
    
    async def connect(self):
        """连接 MCP Server"""
        # TODO 3.1：实现连接逻辑
        # 真实场景：通过 stdio 或 HTTP 连接
        # 模拟场景：直接引用本地 server 对象
        pass
    
    async def list_tools(self) -> List[Dict]:
        """列出所有可用的工具"""
        # TODO 3.2：实现工具列表获取
        pass
    
    async def call_tool(self, name: str, arguments: Dict) -> str:
        """调用指定工具"""
        # TODO 3.3：实现工具调用
        pass


# ==================== 任务 4：Agent 集成 MCP 工具 ====================

async def agent_with_mcp(user_input: str, mcp_client: MCPClient):
    """
    集成 MCP 工具的 Agent
    
    流程：
    1. 从 MCP Client 获取可用工具列表
    2. 将工具列表转换为 Function Calling 格式
    3. 执行 ReAct 循环（和 Day 4/5 类似）
    4. 当需要工具时，通过 MCP Client 调用
    """
    # TODO 4.1：获取工具列表
    tools = await mcp_client.list_tools()
    print(f"📋 可用工具: {[t['name'] for t in tools]}")
    
    # TODO 4.2：模拟 ReAct 循环 + MCP 调用
    # 提示：这是 Day 6 的 ReAct + Day 4 的 Function Calling + MCP Client
    pass


# ==================== 主函数 ====================

# TODO 5.1：注册工具到 MCP Server
# 提示：参考任务 2

@mcp_server.tool("calculator", "执行四则运算")
async def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


@mcp_server.tool("read_note", "读取笔记文件")
async def read_note(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取失败: {e}"


async def main():
    print("=" * 60)
    print("Day 8 练习：MCP Server")
    print("=" * 60)
    
    # 测试 1：查看 MCP Server 中的工具
    print("\n📝 测试 1：查看注册的工具")
    tool_list = mcp_server.get_tool_list()
    print(f"注册了 {len(tool_list)} 个工具：")
    for t in tool_list:
        print(f"  🔧 {t['name']}: {t.get('description', '无描述')}")
    
    # 测试 2：调用 MCP 工具
    print("\n📝 测试 2：调用 MCP 工具")
    result = await mcp_server.call_tool("calculator", {"expression": "3+5*2"})
    print(f"  calculator(3+5*2) = {result}")
    
    # 测试 3：Agent 集成
    print("\n📝 测试 3：Agent 集成 MCP")
    client = MCPClient()
    
    # 模拟问题
    result = await agent_with_mcp("帮我计算 10 + 20", client)
    print(f"  Agent 回答: {result}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！现在运行 python day08_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
