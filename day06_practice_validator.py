"""
Day 6 练习项目验收脚本（行为级验收）
不依赖框架，纯 Python 手写 ReAct Agent 循环

运行方式：
    python day06_practice_validator.py                  # 验收默认模板文件
    python day06_practice_validator.py --file 你的练习.py

验收方式：
    直接调用你的解析函数、执行你的工具、跑通你的 ReAct 主循环，
    检查 Agent 是否真的能"调用工具 → 拿到观察 → 给出最终答案"。
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
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day06_practice_template.py"
满分 = 100
通过线 = 60
优秀线 = 80

# 测试样本：一个 Action 响应，一个 Final Answer 响应
SAMPLE_ACTION = """Thought: 我需要计算这个表达式的结果
Action: Calculator
Action Input: 3 + 5 * 2"""

SAMPLE_FINAL = """Thought: 我已经获得了所需信息
Final Answer: 根据查询结果，答案是 13。"""


class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    END = "\033[0m"


def 打印(文本, 颜色=None):
    print(f"{颜色}{文本}{C.END}" if 颜色 else 文本)


def 加载学生模块(文件路径: Path):
    spec = importlib.util.spec_from_file_location("学生练习_day06", 文件路径)
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
            得分, 消息 = 0, "❌ 检查超时——ReAct 循环可能没有终止（检查 max_steps）"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_工具描述(模块):
    get_desc = getattr(模块, "get_tools_description", None)
    assert callable(get_desc), "没有找到 get_tools_description 函数（TODO 1.2）"
    描述 = get_desc()
    assert isinstance(描述, str) and 描述.strip(), f"应返回非空字符串，实际 {描述!r}"
    assert "Calculator" in 描述, f"工具描述应包含 Calculator，实际：{描述[:80]!r}"
    assert "Weather" in 描述, f"工具描述应包含 Weather，实际：{描述[:80]!r}"
    return 10, "✅ 工具描述包含全部注册工具（将放入 System Prompt）"


def 检查_执行工具(模块):
    execute = getattr(模块, "execute_tool", None)
    assert callable(execute), "没有找到 execute_tool 函数（TODO 1.3）"
    结果 = execute("Calculator", "3 + 5 * 2")
    assert 结果 is not None, "execute_tool 返回 None——TODO 1.3 还没实现"
    if hasattr(结果, "output"):
        输出, 成功 = 结果.output, getattr(结果, "success", True)
    elif isinstance(结果, dict):
        输出, 成功 = 结果.get("output"), 结果.get("success", True)
    else:
        输出, 成功 = str(结果), True
    assert 成功, f"工具应执行成功，实际：{结果!r}"
    assert "13" in str(输出), f"3 + 5 * 2 的输出应包含 13，实际 {输出!r}"
    return 15, f"✅ Calculator 工具执行正确，输出：{输出!r}"


def 检查_解析_Action(模块):
    parse = getattr(模块, "parse_react_response", None)
    assert callable(parse), "没有找到 parse_react_response 函数（TODO 3.1）"
    thought, action, action_input = parse(SAMPLE_ACTION)
    assert action.strip() == "Calculator", f"action 应为 'Calculator'，实际 {action!r}"
    assert action_input.strip() == "3 + 5 * 2", f"action_input 应为 '3 + 5 * 2'，实际 {action_input!r}"
    assert thought.strip(), f"thought 不应为空，实际 {thought!r}"
    return 13, "✅ Action 响应解析正确（Thought/Action/Action Input）"


def 检查_解析_FinalAnswer(模块):
    thought, action, action_input = 模块.parse_react_response(SAMPLE_FINAL)
    assert action.strip() == "", f"Final Answer 响应的 action 应为空字符串，实际 {action!r}"
    assert "13" in action_input, f"最终答案应放在 action_input 中返回，实际 {action_input!r}"
    return 12, "✅ Final Answer 响应解析正确（action 为空，答案在 action_input）"


async def 跑_agent(模块, 问题):
    with redirect_stdout(io.StringIO()):
        回答 = await asyncio.wait_for(
            模块.react_agent(user_input=问题, max_steps=6, verbose=False), timeout=30
        )
    return 回答


async def 检查_Agent_计算(模块):
    回答 = await 跑_agent(模块, "帮我计算 3 + 5 * 2 等于多少？")
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串，实际 {回答!r}（TODO 4.1）"
    assert "最大步数" not in 回答 and "最大轮数" not in 回答, (
        f"Agent 没有正常终止（返回：{回答[:60]!r}）。"
        "提示：把历史 Thought/Action/Observation 拼进 prompt，第 2 轮 mock 会给出 Final Answer"
    )
    assert "13" in 回答, (
        f"最终回答应包含工具算出的 13（说明工具真的执行了），实际：{回答[:80]!r}"
    )
    return 20, f"✅ ReAct 循环完整跑通：{回答[:50]!r}"


async def 检查_Agent_天气(模块):
    回答 = await 跑_agent(模块, "北京今天天气怎么样？")
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串，实际 {回答!r}"
    assert "25" in 回答 or "晴" in 回答, f"天气回答应包含查询结果（25°C/晴），实际：{回答[:80]!r}"
    return 15, f"✅ 天气问题闭环成功：{回答[:50]!r}"


def 检查_循环结构(文件路径):
    """AST 检查：react_agent 必须有 for 循环 + await（异步 LLM 调用）"""
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    for 节点 in ast.walk(树):
        if isinstance(节点, ast.AsyncFunctionDef) and 节点.name == "react_agent":
            有for = any(isinstance(子, ast.For) for 子 in ast.walk(节点))
            有await = any(isinstance(子, ast.Await) for 子 in ast.walk(节点))
            if 有for and 有await:
                return 10, "✅ react_agent 内有 for 循环（步数上限）和 await（异步调用）"
            return 0, "❌ react_agent 内缺少 for 循环或 await——必须有 max_steps 循环和异步 LLM 调用"
    return 0, "❌ 没有找到 react_agent 函数"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("工具描述生成", 10, 检查_工具描述, 模块)
    await 验收员.检查("执行工具", 15, 检查_执行工具, 模块)
    await 验收员.检查("解析：Action 响应", 13, 检查_解析_Action, 模块)
    await 验收员.检查("解析：Final Answer 响应", 12, 检查_解析_FinalAnswer, 模块)
    await 验收员.检查("Agent 端到端：计算问题", 20, 检查_Agent_计算, 模块)
    await 验收员.检查("Agent 端到端：天气问题", 15, 检查_Agent_天气, 模块)
    await 验收员.检查("循环结构：for + await", 10, 检查_循环结构, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 6 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 6 练习验收 —— 纯 Python 手写 ReAct Agent")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day06_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你手写了一个能跑的 ReAct Agent！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
