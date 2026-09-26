"""
Day 4 练习项目验收脚本（行为级验收）
实现支持 Function Calling 的 LLM 客户端

运行方式：
    python day04_practice_validator.py                  # 验收默认模板文件
    python day04_practice_validator.py --file 你的练习.py

验收方式：
    用构造好的 LLM 响应直接调用你的解析/执行/主循环函数，
    检查真实行为（tools 格式、tool_calls 解析、工具执行、完整对话闭环）。
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

DEFAULT_FILE = "day04_practice_template.py"
满分 = 100
通过线 = 60
优秀线 = 80

# 构造一个带 tool_calls 的 LLM 响应（OpenAI 格式）
SAMPLE_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_001",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "北京"}',
                        },
                    }
                ],
            }
        }
    ]
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
    spec = importlib.util.spec_from_file_location("学生练习_day04", 文件路径)
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
            得分, 消息 = 0, "❌ 检查超时——主循环可能没有终止条件"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_工具列表(模块):
    get_tools = getattr(模块, "get_tools_for_api", None)
    assert callable(get_tools), "没有找到 get_tools_for_api 函数（TODO 1.2）"
    tools = get_tools()
    assert isinstance(tools, list), f"应返回列表，实际 {type(tools).__name__}"
    assert len(tools) >= 2, f"应至少有 2 个工具，实际 {len(tools)} 个"
    for item in tools:
        assert item.get("type") == "function", f"每项的 type 应为 'function'，实际 {item!r}"
        fn = item.get("function") or {}
        assert fn.get("name") and fn.get("description"), f"工具 {fn.get('name')!r} 缺少 name/description"
        assert isinstance(fn.get("parameters"), dict), f"工具 {fn.get('name')!r} 缺少 parameters"
    return 15, f"✅ {len(tools)} 个工具均为 OpenAI Function Calling 格式"


def 检查_解析tool_calls(模块):
    parse = getattr(模块, "parse_tool_calls", None)
    assert callable(parse), "没有找到 parse_tool_calls 函数（TODO 3.1）"
    结果 = parse(SAMPLE_RESPONSE)
    assert isinstance(结果, list) and len(结果) == 1, f"应解析出 1 个 tool_call，实际 {结果!r}"
    tc = 结果[0]
    assert tc.get("id") == "call_001", f"id 应为 'call_001'，实际 {tc.get('id')!r}"
    assert tc.get("name") == "get_weather", f"name 应为 'get_weather'，实际 {tc.get('name')!r}"
    assert tc.get("arguments") == {"city": "北京"}, (
        f"arguments 应解析成 dict {{'city': '北京'}}（记得 json.loads），实际 {tc.get('arguments')!r}"
    )
    return 20, "✅ tool_calls 解析正确（id/name/arguments 字典）"


def 检查_执行工具(模块):
    execute = getattr(模块, "execute_tool_call", None)
    assert callable(execute), "没有找到 execute_tool_call 函数（TODO 3.2）"
    结果 = execute({"id": "call_002", "name": "calculator", "arguments": {"expression": "3 + 5 * 2"}})
    assert 结果 is not None, f"执行结果不应为 None（注册表里已有 calculator 工具），实际 {结果!r}"
    assert "13" in str(结果), f"3 + 5 * 2 的执行结果应包含 13，实际 {结果!r}"
    return 20, f"✅ 工具执行正确：calculator → {结果!r}"


async def 检查_对话闭环(模块, 用户消息, 分值说明):
    chat = getattr(模块, "chat_with_function_calling", None)
    assert callable(chat), "没有找到 chat_with_function_calling 函数（TODO 4.1）"
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        回答 = await asyncio.wait_for(chat(用户消息, verbose=False), timeout=30)
    assert isinstance(回答, str) and 回答.strip(), (
        f"应返回非空字符串回答，实际 {回答!r}。"
        "提示：把工具结果以 role=tool 消息回传后再次调用 LLM，返回 content"
    )
    return 回答


async def 检查_对话_天气(模块):
    回答 = await 检查_对话闭环(模块, "北京今天天气怎么样？", "")
    return 15, f"✅ 天气问题闭环成功：{回答[:40]}"


async def 检查_对话_计算(模块):
    回答 = await 检查_对话闭环(模块, "帮我计算 3 + 5 * 2", "")
    return 15, f"✅ 计算问题闭环成功：{回答[:40]}"


def 检查_错误处理(文件路径):
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    目标 = {"parse_tool_calls", "execute_tool_call", "chat_with_function_calling"}
    for 节点 in ast.walk(树):
        if isinstance(节点, (ast.FunctionDef, ast.AsyncFunctionDef)) and 节点.name in 目标:
            for 子 in ast.walk(节点):
                if isinstance(子, ast.Try):
                    return 10, f"✅ {节点.name} 中有 try/except 错误处理"
    return 0, "❌ 核心函数中没有 try/except——JSON 解析失败/工具出错时必须容错，不能裸奔"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("tools 参数：OpenAI 格式", 15, 检查_工具列表, 模块)
    await 验收员.检查("解析 tool_calls", 20, 检查_解析tool_calls, 模块)
    await 验收员.检查("执行工具", 20, 检查_执行工具, 模块)
    await 验收员.检查("对话闭环：天气问题", 15, 检查_对话_天气, 模块)
    await 验收员.检查("对话闭环：计算问题", 15, 检查_对话_计算, 模块)
    await 验收员.检查("错误处理", 10, 检查_错误处理, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 4 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 4 练习验收 —— Function Calling LLM 客户端")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day04_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你掌握了 Function Calling 全流程！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
