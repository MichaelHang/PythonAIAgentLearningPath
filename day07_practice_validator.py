"""
Day 7 练习项目验收脚本（行为级验收）
用 LangGraph 实现带条件分支的 ReAct Agent

运行方式：
    python day07_practice_validator.py                  # 验收默认模板文件
    python day07_practice_validator.py --file 你的练习.py

验收方式：
    直接构造 state 调用你的 Node/Router 函数、跑通你的 Agent，
    检查真实行为（State 字段、消息流转、条件路由、端到端回答）。
    没安装 langgraph 也能验收（run_agent 允许降级用模拟器）。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。
"""

import argparse
import asyncio
import importlib.util
import inspect
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day07_practice_template.py"
满分 = 100
通过线 = 60
优秀线 = 80

TOOL_CALL = {
    "id": "call_001",
    "type": "function",
    "function": {"name": "calculator", "arguments": json.dumps({"expression": "3 + 5 * 2"})},
}


class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    END = "\033[0m"


def 打印(文本, 颜色=None):
    print(f"{颜色}{文本}{C.END}" if 颜色 else 文本)


def 加载学生模块(文件路径: Path):
    spec = importlib.util.spec_from_file_location("学生练习_day07", 文件路径)
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
                得分, 消息 = await asyncio.wait_for(函数(*参数), timeout=40)
            else:
                得分, 消息 = 函数(*参数)
        except asyncio.TimeoutError:
            得分, 消息 = 0, "❌ 检查超时——Agent 可能没有终止条件"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_State(模块):
    State = getattr(模块, "AgentState", None)
    assert State is not None, "没有找到 AgentState（TODO 1.1）"
    注解 = getattr(State, "__annotations__", {})
    assert "messages" in 注解, f"AgentState 应定义 messages 字段，实际 {list(注解)}"
    assert "step_count" in 注解, f"AgentState 应定义 step_count 字段，实际 {list(注解)}"
    return 10, f"✅ AgentState 字段：{list(注解)}"


def 检查_工具列表(模块):
    get_tools = getattr(模块, "get_tools_for_api", None)
    assert callable(get_tools), "没有找到 get_tools_for_api 函数（TODO 2.2）"
    tools = get_tools()
    assert isinstance(tools, list) and len(tools) >= 2, f"应返回至少 2 个工具，实际 {tools!r}"
    for item in tools:
        fn = (item or {}).get("function") or {}
        assert item.get("type") == "function" and fn.get("name"), f"工具格式错误：{item!r}"
    return 10, f"✅ {len(tools)} 个工具格式正确"


def 检查_执行工具(模块):
    execute = getattr(模块, "execute_tool", None)
    assert callable(execute), "没有找到 execute_tool 函数（TODO 2.3）"
    结果 = execute("calculator", {"expression": "3 + 5 * 2"})
    assert 结果 is not None and "13" in str(结果), f"应返回计算结果 13，实际 {结果!r}"
    return 10, f"✅ 工具执行正确：{结果!r}"


async def 检查_模型节点(模块):
    state = {
        "messages": [
            {"role": "system", "content": "你是 AI 助手"},
            {"role": "user", "content": "帮我计算 3 + 5 * 2"},
        ],
        "step_count": 0,
    }
    out = 模块.node_call_model(state)
    assert isinstance(out, dict), f"node 应返回 dict，实际 {type(out).__name__}（TODO 4.1）"
    msgs = out.get("messages") or []
    # 兼容两种返回：完整消息列表，或只返回新增消息（LangGraph 风格的部分更新）
    if len(msgs) == 1:
        新消息 = msgs[-1]
    else:
        assert len(msgs) == len(state["messages"]) + 1, (
            f"messages 应新增 1 条，实际 {len(msgs)} 条（输入 {len(state['messages'])} 条）"
        )
        新消息 = msgs[-1]
    assert 新消息.get("role") == "assistant", f"新增消息应为 assistant，实际 {新消息!r}"
    assert out.get("step_count") == 1, f"step_count 应从 0 变 1，实际 {out.get('step_count')!r}"
    return 15, "✅ call_model 正确调用 LLM（mock）并追加 assistant 消息"


async def 检查_工具节点(模块):
    state = {
        "messages": [
            {"role": "user", "content": "帮我计算 3 + 5 * 2"},
            {"role": "assistant", "content": None, "tool_calls": [TOOL_CALL]},
        ],
        "step_count": 1,
    }
    out = 模块.node_call_tool(state)
    assert isinstance(out, dict), f"node 应返回 dict，实际 {type(out).__name__}（TODO 4.2）"
    msgs = out.get("messages") or []
    工具消息 = next((m for m in reversed(msgs) if m.get("role") == "tool"), None)
    assert 工具消息, f"应追加 role='tool' 的消息，实际最后两条：{msgs[-2:]!r}"
    assert "13" in str(工具消息.get("content", "")), (
        f"工具结果应包含 13（说明真的执行了 calculator），实际 {工具消息.get('content')!r}"
    )
    return 15, "✅ call_tool 执行计算器并追加 tool 消息"


def 检查_路由器(模块):
    router = getattr(模块, "router_should_continue", None)
    assert callable(router), "没有找到 router_should_continue 函数（TODO 5.1）"
    带工具 = {"messages": [{"role": "assistant", "content": None, "tool_calls": [TOOL_CALL]}], "step_count": 1}
    无工具 = {"messages": [{"role": "assistant", "content": "已完成"}], "step_count": 2}
    r1 = str(router(带工具)).strip().lower()
    r2 = str(router(无工具)).strip().lower().lstrip("_")
    assert r1 == "call_tool", f"有 tool_calls 时应返回 'call_tool'，实际 {r1!r}"
    assert r2 in ("end", "stop", "finish"), f"无 tool_calls 时应返回 'end'/'__end__'，实际 {r2!r}"
    return 15, "✅ 条件路由：有工具调用 → call_tool；无 → 结束"


async def 检查_端到端(模块):
    run = getattr(模块, "run_agent", None)
    assert callable(run), "没有找到 run_agent 函数（TODO 7.1）"
    with redirect_stdout(io.StringIO()):
        回答 = await asyncio.wait_for(run("帮我计算 3 + 5 * 2"), timeout=30)
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串回答，实际 {回答!r}"
    assert "最大步数" not in 回答 and "最大轮数" not in 回答, f"Agent 没能正常终止：{回答[:60]!r}"
    assert "13" in 回答, (
        f"最终回答应包含工具算出的 13（说明工具真的执行了），实际：{回答[:80]!r}"
    )
    return 20, f"✅ Agent 完整跑通：{回答[:50]!r}"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块):
    await 验收员.检查("AgentState 定义", 10, 检查_State, 模块)
    await 验收员.检查("tools 参数：OpenAI 格式", 10, 检查_工具列表, 模块)
    await 验收员.检查("执行工具", 10, 检查_执行工具, 模块)
    await 验收员.检查("call_model 节点", 15, 检查_模型节点, 模块)
    await 验收员.检查("call_tool 节点", 15, 检查_工具节点, 模块)
    await 验收员.检查("条件路由 router", 15, 检查_路由器, 模块)
    await 验收员.检查("Agent 端到端", 20, 检查_端到端, 模块)


def main():
    parser = argparse.ArgumentParser(description="Day 7 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 7 练习验收 —— LangGraph ReAct Agent")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day07_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        asyncio.run(运行验收(验收员, 模块))

    总分 = 验收员.总分
    打印("\n" + "=" * 60)
    if 总分 >= 优秀线:
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你用图的方式重构了 ReAct Agent！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
