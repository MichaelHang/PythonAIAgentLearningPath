"""
Day 8 练习项目验收脚本（行为级验收）
实现一个 MCP Server + 在 Agent 中集成 MCP 工具

运行方式：
    python day08_practice_validator.py                  # 验收默认模板文件
    python day08_practice_validator.py --file 你的练习.py

验收方式：
    直接调用你的 MockMCPServer（列工具/调用工具/读文件）、你的 MCPClient、
    以及你的 Agent 集成函数，检查真实行为。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。
"""

import argparse
import ast
import asyncio
import importlib.util
import inspect
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day08_practice_template.py"
满分 = 100
通过线 = 60
优秀线 = 80


class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    END = "\033[0m"


def 打印(文本, 颜色=None):
    print(f"{颜色}{文本}{C.END}" if 颜色 else 文本)


def 加载学生模块(文件路径: Path):
    spec = importlib.util.spec_from_file_location("学生练习_day08", 文件路径)
    模块 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(模块)
    return 模块


class 验收器:
    def __init__(self):
        self.总分 = 0

    async def 检查(self, 名称: str, 分值: int, 函数, *参数):
        """运行单个检查；检查函数返回 (得分, 消息)，抛异常记 0 分"""
        打印(f"\n【{名称}】（{分值}分）", C.CYAN)
        try:
            if inspect.iscoroutinefunction(函数):
                得分, 消息 = await asyncio.wait_for(函数(*参数), timeout=45)
            else:
                得分, 消息 = 函数(*参数)
        except asyncio.TimeoutError:
            得分, 消息 = 0, "❌ 检查超时——可能有死循环或过长的等待"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_工具列表(模块):
    get_list = getattr(模块.mcp_server, "get_tool_list", None)
    assert callable(get_list), "没有找到 MockMCPServer.get_tool_list（TODO 2.1）"
    tools = get_list()
    assert isinstance(tools, list), f"应返回列表，实际 {type(tools).__name__}"
    assert len(tools) >= 2, f"应列出至少 2 个工具（模拟 MCP 的 tools/list），实际 {tools!r}"
    for item in tools:
        assert isinstance(item, dict) and item.get("name"), f"每个工具都应有 name 字段：{item!r}"
        assert item.get("description"), f"工具 {item.get('name')!r} 缺少 description"
    return 15, f"✅ tools/list 正常：{[t['name'] for t in tools]}"


async def 检查_服务器调用(模块):
    call = getattr(模块.mcp_server, "call_tool", None)
    assert callable(call), "没有找到 MockMCPServer.call_tool（TODO 2.2）"
    结果 = await call("calculator", {"expression": "10 + 20"})
    assert 结果 is not None, "call_tool 返回 None——TODO 2.2 还没实现"
    assert "30" in str(结果), f"calculator(10 + 20) 应算出 30，实际 {结果!r}"
    return 15, f"✅ tools/call 正常：calculator → {结果!r}"


def 检查_超时控制(文件路径):
    """AST 检查：工具包装器内有 asyncio.wait_for 超时控制"""
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    for 节点 in ast.walk(树):
        if isinstance(节点, ast.ClassDef) and 节点.name == "MockMCPServer":
            for 子 in ast.walk(节点):
                if isinstance(子, ast.Attribute) and 子.attr == "wait_for":
                    return 10, "✅ 工具包装器带 asyncio.wait_for 超时控制"
    return 0, "❌ 工具包装器缺少超时控制——一个卡死的工具会拖死整个 Agent"


async def 检查_客户端(模块):
    client = 模块.MCPClient()
    connect = getattr(client, "connect", None)
    assert callable(connect), "没有找到 MCPClient.connect（TODO 3.1）"
    await connect()
    list_tools = getattr(client, "list_tools", None)
    assert callable(list_tools), "没有找到 MCPClient.list_tools（TODO 3.2）"
    tools = await list_tools()
    assert isinstance(tools, list) and len(tools) >= 2, (
        f"list_tools 应返回 ≥2 个工具，实际 {tools!r}"
    )
    assert all(isinstance(t, dict) and t.get("name") for t in tools), (
        f"工具项应有 name 字段：{tools!r}"
    )
    return 15, f"✅ MCPClient 连接并列出 {len(tools)} 个工具（模拟 MCP 会话）"


async def 检查_客户端调用(模块):
    client = 模块.MCPClient()
    await client.connect()
    call = getattr(client, "call_tool", None)
    assert callable(call), "没有找到 MCPClient.call_tool（TODO 3.3）"
    结果 = await call("calculator", {"expression": "6 * 7"})
    assert 结果 is not None and "42" in str(结果), (
        f"经客户端调用 calculator(6 * 7) 应得 42，实际 {结果!r}"
    )
    return 10, "✅ 经 MCPClient 调用工具成功（tools/call 链路）"


async def 检查_Agent集成(模块):
    agent = getattr(模块, "agent_with_mcp", None)
    assert callable(agent), "没有找到 agent_with_mcp 函数（TODO 4.x）"
    client = 模块.MCPClient()
    await client.connect()
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        结果 = await asyncio.wait_for(
            agent("帮我计算 10 + 20", client), timeout=30
        )
    输出 = 缓冲.getvalue() + str(结果)
    assert "30" in 输出, (
        f"问'帮我计算 10 + 20'应通过 MCP 工具算出 30，实际回答 {结果!r}、输出 {输出[:100]!r}"
    )
    return 20, "✅ Agent 集成：问题经 MCP 工具调用得到了正确回答"


async def 检查_读文件工具(模块):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("MAPLE_MONO_TEST_42")
        路径 = f.name
    try:
        结果 = await 模块.mcp_server.call_tool("read_note", {"path": 路径})
        assert 结果 is not None, "read_note 返回 None"
        assert "MAPLE_MONO_TEST_42" in str(结果), (
            f"read_note 应读到文件内容，实际 {结果!r}"
        )
        return 10, "✅ read_note 工具能通过 MCP 读取文件内容"
    finally:
        os.unlink(路径)


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("tools/list：MockMCPServer 列出工具", 15, 检查_工具列表, 模块)
    await 验收员.检查("tools/call：calculator 算出 30", 15, 检查_服务器调用, 模块)
    await 验收员.检查("超时控制", 10, 检查_超时控制, 文件路径)
    await 验收员.检查("MCPClient：连接 + 列出工具", 15, 检查_客户端, 模块)
    await 验收员.检查("MCPClient：调用工具", 10, 检查_客户端调用, 模块)
    await 验收员.检查("Agent 集成：端到端问答", 20, 检查_Agent集成, 模块)
    await 验收员.检查("read_note：读取文件", 10, 检查_读文件工具, 模块)


def main():
    parser = argparse.ArgumentParser(description="Day 8 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 8 练习验收 —— MCP Server 与 Agent 集成")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day08_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
        sys.exit(1)

    打印("\n【加载练习代码】（5分）", C.CYAN)
    加载分 = 5
    try:
        模块 = 加载学生模块(文件路径)
        打印("  ✅ 代码加载成功，没有语法错误", C.GREEN)
    except Exception as e:
        加载分 = 0
        模块 = None
        打印(f"  ❌ 加载失败：{type(e).__name__}: {e}", C.RED)
        print("  💡 请先修复语法/运行错误再验收")

    验收员 = 验收器()
    验收员.总分 += 加载分
    if 模块 is not None:
        asyncio.run(运行验收(验收员, 模块, 文件路径))

    总分 = 验收员.总分
    打印("\n" + "=" * 60)
    if 总分 >= 优秀线:
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你打通了 MCP 工具生态！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
