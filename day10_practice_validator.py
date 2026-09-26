"""
Day 10 练习项目验收脚本（行为级验收）
多工具 Agent 综合实战（阶段二收尾）

运行方式：
    python day10_practice_validator.py                  # 验收默认模板文件
    python day10_practice_validator.py --file 你的练习.py

验收方式：
    检查工具注册数量、带重试的工具执行、错误恢复（成功/失败两条路径），
    并用一个"间谍函数"拦截 calculator 调用——验证你的 Agent 是否真的执行了工具。
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

DEFAULT_FILE = "day10_practice_template.py"
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
    spec = importlib.util.spec_from_file_location("学生练习_day10", 文件路径)
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
            得分, 消息 = 0, "❌ 检查超时——Agent 可能没有终止条件"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 辅助：模拟 Day 9 记忆接口 ====================

class 简易短期记忆:
    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append(type("M", (), {"role": role, "content": content})())

    def to_api_format(self):
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_recent(self, n=None):
        return self.messages[-n:] if n else self.messages


class 简易RAG:
    def retrieve(self, query, top_k=3):
        return ""


class 简易记忆:
    """提供 Day 9 接口的最小记忆桩：short_memory + rag"""

    def __init__(self):
        self.short_memory = 简易短期记忆()
        self.rag = 简易RAG()


# ==================== 各项检查 ====================

def 检查_工具数量(模块):
    registry = getattr(模块, "TOOLS_REGISTRY", None)
    assert isinstance(registry, dict), "没有找到 TOOLS_REGISTRY"
    assert len(registry) >= 4, (
        f"验收标准要求至少 4 个工具（TODO 2.1/2.2），实际注册了 {len(registry)} 个：{list(registry)}"
    )
    return 20, f"✅ 注册了 {len(registry)} 个工具：{list(registry)}"


async def 检查_工具可调用(模块):
    fn = 模块.TOOLS_REGISTRY.get("calculator", {}).get("function")
    assert fn is not None, "calculator 工具不在注册表中"
    结果 = await asyncio.wait_for(fn(expression="1 + 1"), timeout=15)
    assert "2" in str(结果), f"calculator(1 + 1) 应得 2，实际 {结果!r}"
    return 10, "✅ 工具经注册表包装器（超时+重试）可正常异步调用"


async def 检查_恢复_成功(模块):
    recover = getattr(模块, "execute_tool_with_recovery", None)
    assert callable(recover), "没有找到 execute_tool_with_recovery 函数（TODO 5.1）"
    r = await asyncio.wait_for(
        recover("calculator", {"expression": "3 + 5 * 2"}), timeout=30
    )
    assert r is not None, "成功路径返回 None——TODO 5.1 还没实现"
    assert bool(getattr(r, "success", True)), f"成功路径 success 应为 True，实际 {r!r}"
    assert "13" in str(getattr(r, "output", r)), (
        f"calculator(3 + 5 * 2) 的输出应包含 13，实际 {getattr(r, 'output', r)!r}"
    )
    return 15, f"✅ 成功路径：ToolResult(success=True, output 含 13)"


async def 检查_恢复_失败(模块):
    """不存在的工具：不能崩溃，要把错误作为结果返回给 LLM"""
    recover = getattr(模块, "execute_tool_with_recovery", None)
    r = await asyncio.wait_for(
        recover("不存在的工具xyz", {}), timeout=30
    )
    assert r is not None, "失败路径返回 None——错误应作为结果返回，不能崩溃也不能返回空"
    成功标志 = getattr(r, "success", None)
    if 成功标志 is None and isinstance(r, dict):
        成功标志 = r.get("success")
    if 成功标志 is None and isinstance(r, str):
        # 宽松：返回了包含错误说明的字符串也算"没崩溃"
        assert ("失败" in r or "错误" in r), f"失败路径应返回错误说明，实际 {r!r}"
        return 15, "✅ 失败路径：返回了错误说明（未崩溃）"
    assert 成功标志 is False, (
        f"失败路径 success 应为 False（让 LLM 自行纠正），实际 {r!r}"
    )
    return 15, "✅ 失败路径：不崩溃，返回 success=False 的结果"


async def 检查_Agent回答(模块):
    agent = getattr(模块, "react_agent_with_memory", None)
    assert callable(agent), "没有找到 react_agent_with_memory 函数（TODO 3.1）"
    memory = 简易记忆()
    tools = list(模块.TOOLS_REGISTRY.values())
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        回答 = await asyncio.wait_for(
            agent("帮我计算 3 + 5 * 2", tools, memory, max_steps=6, stream=False),
            timeout=50,
        )
    assert isinstance(回答, str) and 回答.strip(), f"应返回字符串回答，实际 {回答!r}"
    assert 回答.strip() != "最终回答", (
        "返回的还是模板占位符'最终回答'——TODO 3.1 主循环还没实现"
    )
    return 10, f"✅ Agent 返回了真实回答：{回答[:50]!r}"


async def 检查_Agent真调工具(模块):
    """用间谍函数拦截 calculator：验证 Agent 的回答真的来自工具执行"""
    agent = getattr(模块, "react_agent_with_memory", None)
    原包装 = 模块.TOOLS_REGISTRY["calculator"]["function"]
    调用记录 = {"n": 0}

    async def 间谍(*args, **kwargs):
        调用记录["n"] += 1
        return await 原包装(*args, **kwargs)

    模块.TOOLS_REGISTRY["calculator"]["function"] = 间谍
    try:
        memory = 简易记忆()
        tools = list(模块.TOOLS_REGISTRY.values())
        缓冲 = io.StringIO()
        with redirect_stdout(缓冲):
            await asyncio.wait_for(
                agent("帮我计算 3 + 5 * 2", tools, memory, max_steps=6, stream=False),
                timeout=50,
            )
    finally:
        模块.TOOLS_REGISTRY["calculator"]["function"] = 原包装

    assert 调用记录["n"] >= 1, (
        f"Agent 没有通过工具注册表执行 calculator（拦截到 {调用记录['n']} 次调用）。"
        "工具执行必须走 TOOLS_REGISTRY 里包装好的函数，而不是绕过它"
    )
    return 20, f"✅ 间谍函数拦截到 calculator 被真实执行了 {调用记录['n']} 次"


def 检查_类型注解(文件路径):
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    函数们 = [n for n in ast.walk(树) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    有注解 = [f for f in 函数们 if f.returns is not None]
    assert len(有注解) >= 4, f"至少 4 个函数应有返回值类型注解，目前 {len(有注解)}/{len(函数们)}"
    return 5, f"✅ {len(有注解)}/{len(函数们)} 个函数有返回值注解"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("工具系统：至少 4 个工具", 20, 检查_工具数量, 模块)
    await 验收员.检查("工具包装器：可异步调用", 10, 检查_工具可调用, 模块)
    await 验收员.检查("错误恢复：成功路径", 15, 检查_恢复_成功, 模块)
    await 验收员.检查("错误恢复：失败路径不崩溃", 15, 检查_恢复_失败, 模块)
    await 验收员.检查("Agent：返回真实回答", 10, 检查_Agent回答, 模块)
    await 验收员.检查("Agent：真的执行了工具（间谍拦截）", 20, 检查_Agent真调工具, 模块)
    await 验收员.检查("类型注解", 5, 检查_类型注解, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 10 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 10 练习验收 —— 多工具 Agent 综合实战")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day10_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！阶段二正式毕业！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
