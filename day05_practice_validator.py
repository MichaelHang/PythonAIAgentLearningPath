"""
Day 5 练习项目验收脚本（行为级验收）
命令行 AI 助手（阶段一综合实战）

运行方式：
    python day05_practice_validator.py                  # 验收默认模板文件
    python day05_practice_validator.py --file 你的练习.py

验收方式：
    直接构建你的 Agent 并发起真实对话（走内置 mock 流式响应），
    检查流式输出、工具调用链路、最终回答内容。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。

依赖：pip install pydantic
"""

import argparse
import ast
import asyncio
import importlib.util
import inspect
import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day05_practice_template.py"
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
    spec = importlib.util.spec_from_file_location("学生练习_day05", 文件路径)
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
                得分, 消息 = await asyncio.wait_for(函数(*参数), timeout=60)
            else:
                得分, 消息 = 函数(*参数)
        except asyncio.TimeoutError:
            得分, 消息 = 0, "❌ 检查超时——Agent 主循环可能没有终止条件"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_工具列表(模块):
    get_tools = getattr(模块, "get_tools_for_api", None)
    assert callable(get_tools), "没有找到 get_tools_for_api 函数（TODO 2.2）"
    tools = get_tools()
    assert isinstance(tools, list), f"应返回列表，实际 {type(tools).__name__}"
    assert len(tools) >= 2, f"应至少有 2 个工具（calculator/weather），实际 {len(tools)} 个"
    for item in tools:
        fn = (item or {}).get("function") or {}
        assert item.get("type") == "function" and fn.get("name"), f"工具格式错误：{item!r}"
    return 15, f"✅ {len(tools)} 个工具格式正确：{[t['function']['name'] for t in tools]}"


def 检查_执行工具(模块):
    execute = getattr(模块, "execute_tool", None)
    assert callable(execute), "没有找到 execute_tool 函数（TODO 2.3）"
    结果 = execute("calculator", {"expression": "3 + 5 * 2"})
    assert 结果 is not None, "execute_tool 返回 None——TODO 2.3 还没实现"
    assert "13" in str(结果), f"3 + 5 * 2 的结果应包含 13，实际 {结果!r}"
    return 15, f"✅ 工具执行正确：{结果!r}"


async def 检查_流式chat(模块):
    client = 模块.StreamingLLMClient(模块.AgentConfig())
    messages = [
        模块.ChatMessage(role="system", content="你是一个 AI 助手。"),
        模块.ChatMessage(role="user", content="你好！"),
    ]
    生成器 = client.chat(messages)
    assert hasattr(生成器, "__aiter__"), (
        f"chat 应为异步生成器（async def + yield），实际返回 {type(生成器).__name__}"
    )
    chunks = []
    with redirect_stdout(io.StringIO()):
        async for c in 生成器:
            chunks.append(c)
            if len(chunks) > 300:
                break
    assert len(chunks) >= 5, f"应逐块输出多个 chunk，实际 {len(chunks)} 个"
    assert all(isinstance(c, str) for c in chunks), "每个 chunk 都应是字符串"
    return 20, f"✅ chat 流式输出 {len(chunks)} 个 chunk"


async def 检查_端到端_计算(模块):
    agent = 模块.CLI_Agent(模块.AgentConfig())
    with redirect_stdout(io.StringIO()):
        回答 = await asyncio.wait_for(agent.chat("帮我计算 3 + 5 * 2", stream=False), timeout=45)
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串回答，实际 {回答!r}（TODO 4.1）"
    assert "13" in 回答, (
        f"计算 3 + 5 * 2 的回答应包含结果 13（说明 [TOOL_CALL] 被解析并真正执行了工具），"
        f"实际：{回答[:80]!r}"
    )
    return 20, f"✅ 工具调用链路打通：{回答[:50]!r}"


async def 检查_端到端_天气(模块):
    agent = 模块.CLI_Agent(模块.AgentConfig())
    with redirect_stdout(io.StringIO()):
        回答 = await asyncio.wait_for(agent.chat("北京今天天气怎么样？", stream=False), timeout=45)
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串回答，实际 {回答!r}"
    return 10, f"✅ 天气问答闭环成功：{回答[:50]!r}"


async def 检查_工具消息回传(模块):
    agent = 模块.CLI_Agent(模块.AgentConfig())
    with redirect_stdout(io.StringIO()):
        await asyncio.wait_for(agent.chat("帮我计算 1 + 1", stream=False), timeout=45)
    roles = [m.role for m in agent.messages]
    assert "tool" in roles, (
        f"对话历史中应有 role='tool' 的消息（Function Calling 的工具结果回传），实际 {roles}"
    )
    return 10, "✅ 工具结果以 role=tool 消息回传（Function Calling 机制）"


def 检查_Pydantic模型(文件路径):
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    模型数 = 0
    for 节点 in ast.walk(树):
        if isinstance(节点, ast.ClassDef):
            for base in 节点.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    模型数 += 1
    assert 模型数 >= 3, f"应至少定义 3 个 Pydantic BaseModel 模型，实际 {模型数} 个"
    return 5, f"✅ 定义了 {模型数} 个 Pydantic 模型"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("tools 参数：OpenAI 格式", 15, 检查_工具列表, 模块)
    await 验收员.检查("执行工具", 15, 检查_执行工具, 模块)
    await 验收员.检查("流式 LLM：chat 逐块输出", 20, 检查_流式chat, 模块)
    await 验收员.检查("端到端：计算问题（含工具调用）", 20, 检查_端到端_计算, 模块)
    await 验收员.检查("端到端：天气问答", 10, 检查_端到端_天气, 模块)
    await 验收员.检查("Function Calling：tool 消息回传", 10, 检查_工具消息回传, 模块)
    await 验收员.检查("Pydantic 数据结构", 5, 检查_Pydantic模型, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 5 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 5 练习验收 —— 命令行 AI 助手（阶段一综合）")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day05_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
        sys.exit(1)

    打印("\n【加载练习代码】（5分）", C.CYAN)
    加载分 = 5
    try:
        模块 = 加载学生模块(文件路径)
        打印("  ✅ 代码加载成功，没有语法错误", C.GREEN)
    except ImportError as e:
        加载分 = 0
        模块 = None
        打印(f"  ❌ 缺少依赖：{e}", C.RED)
        print("  💡 Day 5 需要 pydantic：pip install pydantic")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你成功构建了命令行 AI 助手！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
