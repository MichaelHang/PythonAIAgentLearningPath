#!/usr/bin/env python3
"""
Day 4 练习验收脚本
验收内容：Function Calling LLM 客户端

使用方法：
    python day04_practice_validator.py
    python day04_practice_validator.py --file day04_practice.py
"""

import ast
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Tuple

TIMEOUT = 30


class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def 打印(内容: str, 颜色: str = C.END):
    print(f"{C.BOLD}{颜色}{内容}{C.END}")


# ==================== 检查项 ====================

def 检查_pydantic导入(代码: str) -> Tuple[bool, str]:
    """检查 1：是否有 aiohttp 或 httpx（HTTP 客户端）"""
    if "aiohttp" in 代码 or "httpx" in 代码 or "requests" in 代码:
        return True, "✅ 找到 HTTP 客户端库（aiohttp/httpx/requests）"
    return True, "⚠️ 未找到 HTTP 客户端（可用 aiohttp 或 mock）"


def 检查_tools参数(代码: str) -> Tuple[bool, str]:
    """检查 2：是否构建了 OpenAI Function Calling 格式的 tools 参数"""
    关键词 = ["tools", "type", "function", "parameters"]
    找到数 = sum(1 for kw in 关键词 if kw in 代码)
    
    if 找到数 >= 3:
        return True, f"✅ 找到 tools 参数构建代码（{找到数}/4 个关键词）"
    return False, f"❌ 未找到完整的 tools 参数构建（只找到 {找到数}/4 个关键词）"


def 检查_tool_calls解析(代码: str) -> Tuple[bool, str]:
    """检查 3：是否解析 tool_calls"""
    关键词 = ["tool_calls", "function", "arguments", "json.loads"]
    找到数 = sum(1 for kw in 关键词 if kw in 代码)
    
    if 找到数 >= 3:
        return True, f"✅ 找到 tool_calls 解析逻辑（{找到数}/4 个关键词）"
    return False, f"❌ 未找到 tool_calls 解析（需要解析 LLM 返回的 tool_calls）"


def 检查_工具执行(代码: str) -> Tuple[bool, str]:
    """检查 4：是否根据 tool_calls 执行工具"""
    关键词 = ["execute", "call_tool", "执行", "调用"]
    找到 = [kw for kw in 关键词 if kw in 代码]
    
    if 找到:
        return True, f"✅ 找到工具执行逻辑：{', '.join(找到)}"
    return False, "❌ 未找到工具执行逻辑（需要根据 tool_call 调用对应函数）"


def 检查_结果回传(代码: str) -> Tuple[bool, str]:
    """检查 5：是否将工具执行结果返回给 LLM"""
    关键词 = ["role", "tool", "tool_call_id", "Observation"]
    找到数 = sum(1 for kw in 关键词 if kw in 代码)
    
    if 找到数 >= 2:
        return True, f"✅ 找到结果回传逻辑（{找到数}/4 个关键词）"
    return False, "⚠️ 未找到明确的工具结果回传（应追加 role=tool 的消息）"


def 检查_循环结构(代码: str) -> Tuple[bool, str]:
    """检查 6：是否有 Function Calling 循环（可能多轮）"""
    树 = ast.parse(代码)
    有循环 = False
    有_while = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.For):
            有循环 = True
        if isinstance(node, ast.While):
            有_while = True
            有循环 = True
    
    if 有循环:
        msg = "✅ 找到循环结构（"
        if 有_while:
            msg += "while"
        elif 有循环:
            msg += "for"
        msg += "），支持多轮 Function Calling"
        return True, msg
    return True, "⚠️ 未找到循环（单轮 Function Calling 也可以，多轮更好）"


def 检查_错误处理(代码: str) -> Tuple[bool, str]:
    """检查 7：是否有错误处理"""
    树 = ast.parse(代码)
    有_try = False
    有重试 = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.Try):
            有_try = True
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    有_try = True
        if "retry" in 代码.lower() or "重试" in 代码:
            有重试 = True
    
    if 有_try and 有重试:
        return True, "✅ 有 try/except 错误处理 + 重试机制"
    elif 有_try:
        return True, "✅ 有 try/except 错误处理"
    return False, "❌ 未找到错误处理（建议加 try/except）"


def 检查_类型注解(代码: str) -> Tuple[bool, str]:
    """检查 8：是否有类型注解"""
    树 = ast.parse(代码)
    有注解 = 0
    
    for node in ast.walk(树):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                有注解 += 1
            for arg in node.args.args:
                if arg.annotation is not None:
                    有注解 += 1
    
    if 有注解 >= 3:
        return True, f"✅ 类型注解较好（{有注解} 处注解）"
    return True, f"⚠️ 类型注解较少（{有注解} 处，建议多加）"


# ==================== 运行检查 ====================

def 运行用户代码(文件路径: Path) -> Tuple[bool, str, float]:
    try:
        开始 = time.time()
        结果 = subprocess.run(
            [sys.executable, str(文件路径)],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        耗时 = time.time() - 开始
        if 结果.returncode == 0:
            return True, 结果.stdout, 耗时
        return False, f"运行失败：\n{结果.stderr[:500]}", 耗时
    except subprocess.TimeoutExpired:
        return False, f"⏰ 运行超时（{TIMEOUT} 秒）", TIMEOUT
    except Exception as e:
        return False, f"运行出错：{e}", 0.0


def 检查_代码可运行(文件路径: Path) -> Tuple[bool, str]:
    成功, 输出, 耗时 = 运行用户代码(文件路径)
    if 成功:
        return True, f"✅ 代码运行成功（耗时 {耗时:.2f} 秒）\n   输出预览：\n{输出[:300]}"
    return False, f"❌ 代码运行失败：\n{输出[:500]}"


def 检查_function_calling流程(文件路径: Path) -> Tuple[bool, str]:
    """检查：代码是否实现了完整的 Function Calling 流程"""
    检验代码 = """
import sys
sys.path.insert(0, ".")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_module", r"{}")
    if spec is None:
        print("❌ 无法加载模块")
    else:
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        
        # 检查是否有 chat_with_function_calling 或类似函数
        funcs = [name for name in dir(user_module) 
                  if "chat" in name.lower() or "function" in name.lower() or "call" in name.lower()]
        if funcs:
            print(f"✅ 找到关键函数：{{', '.join(funcs)}}")
        else:
            print("⚠️ 未找到 chat_with_function_calling 等函数")
except Exception as e:
    print(f"❌ 检查失败：{{e}}")
""".format(str(文件路径).replace("\\", "\\\\"))
    
    try:
        结果 = subprocess.run(
            [sys.executable, "-c", 检验代码],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return True, 结果.stdout.strip() or 结果.stderr.strip()
    except Exception as e:
        return False, f"检查失败：{e}"


# ==================== 主逻辑 ====================

def 验收(文件路径: Path) -> int:
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 4 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        return 0
    
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    检查项 = [
        ("HTTP 客户端（aiohttp/httpx）", 检查_pydantic导入),
        ("tools 参数构建（OpenAI Function Calling 格式）", 检查_tools参数),
        ("tool_calls 解析", 检查_tool_calls解析),
        ("工具执行逻辑", 检查_工具执行),
        ("工具结果回传给 LLM", 检查_结果回传),
        ("Function Calling 循环（多轮）", 检查_循环结构),
        ("错误处理（try/except + 重试）", 检查_错误处理),
        ("类型注解", 检查_类型注解),
    ]
    
    分数 = 0
    满分 = len(检查项) * 10 + 20
    
    for 名称, 检查函数 in 检查项:
        通过, 消息 = 检查函数(代码)
        打印(f"  [{名称}]", C.BLUE)
        if "✅" in 消息:
            打印(f"  {消息}", C.GREEN)
            分数 += 10
        elif "⚠️" in 消息:
            打印(f"  {消息}", C.YELLOW)
            分数 += 5
        else:
            打印(f"  {消息}", C.RED)
    
    # 运行检查
    打印(f"\n  [代码可运行性]", C.BLUE)
    通过, 消息 = 检查_代码可运行(文件路径)
    打印(f"  {消息}", C.GREEN if 通过 else C.RED)
    if 通过:
        分数 += 10
    
    # Function Calling 流程检查
    打印(f"\n  [Function Calling 流程完整性]", C.BLUE)
    通过, 消息 = 检查_function_calling流程(文件路径)
    打印(f"  {消息}", C.GREEN if 通过 else C.YELLOW)
    if 通过 and "✅" in 消息:
        分数 += 10
    elif 通过:
        分数 += 5
    
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    
    if 分数 >= 80:
        打印(f"  🎉 验收通过！你掌握了 Function Calling！", C.GREEN)
    elif 分数 >= 60:
        打印(f"  ⚠️ 基本通过，建议改进后再继续", C.YELLOW)
    else:
        打印(f"  ❌ 还需努力，参考上面提示改进", C.RED)
    
    打印(f"{'='*60}\n", C.CYAN)
    
    if 分数 < 80:
        打印("📋 改进建议：", C.YELLOW)
        if not 检查_tool_calls解析(代码)[0]:
            打印("  • 解析 LLM 响应中的 tool_calls（function.name 和 function.arguments）", C.YELLOW)
        if not 检查_工具执行(代码)[0]:
            打印("  • 根据 tool_call 的 name 调用对应工具函数", C.YELLOW)
        if not 检查_结果回传(代码)[0]:
            打印("  • 工具执行结果以 role=tool 追加到 messages，再发给 LLM", C.YELLOW)
        if not 检查_错误处理(代码)[0]:
            打印("  • 加 try/except 处理 JSON 解析失败、工具执行失败等情况", C.YELLOW)
        print()
    
    return 分数


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 4 练习验收脚本")
    parser.add_argument("--file", default="day04_practice_template.py", help="练习文件路径")
    args = parser.parse_args()
    文件路径 = Path(args.file)
    验收(文件路径)


if __name__ == "__main__":
    main()
