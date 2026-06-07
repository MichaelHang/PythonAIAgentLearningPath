#!/usr/bin/env python3
"""
Day 6 练习验收脚本
验收内容：纯 Python 手写 ReAct Agent 循环

使用方法：
    python day06_practice_validator.py
    python day06_practice_validator.py --file day06_practice.py
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

def 检查_react循环(代码: str) -> Tuple[bool, str]:
    """检查 1：是否实现了 ReAct 主循环（for/while + max_steps）"""
    树 = ast.parse(代码)
    找到了循环 = False
    找到了上限 = False
    详情 = []
    
    for node in ast.walk(树):
        # 检查 for 或 while 循环
        if isinstance(node, (ast.For, ast.While)):
            找到了循环 = True
            详情.append(f"✅ 找到循环：{type(node).__name__}")
            
            # 检查是否有 max_steps 或类似上限
            for child in ast.walk(node):
                if isinstance(child, ast.Constant):
                    if isinstance(child.value, int) and child.value <= 20:
                        找到了上限 = True
                        详情.append(f"   └─ 疑似步数上限：{child.value}")
    
    if 找到了循环 and 找到了上限:
        return True, "\n".join(详情)
    elif 找到了循环:
        return True, "\n".join(详情) + "\n⚠️ 未找到明确的 max_steps 上限"
    return False, "❌ 未找到 ReAct 主循环（需要 for/while 循环）"


def 检查_async_await(代码: str) -> Tuple[bool, str]:
    """检查 2：是否使用了 async/await"""
    树 = ast.parse(代码)
    有_async = False
    有_await = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.AsyncFunctionDef):
            有_async = True
            详情.append(f"✅ 找到异步函数：{node.name}")
        if isinstance(node, ast.Await):
            有_await = True
    
    if 有_async and 有_await:
        return True, "\n".join(详情) + "\n✅ 找到 await 表达式"
    elif 有_async:
        return True, "\n".join(详情) + "\n⚠️ 找到 async 函数但未找到 await"
    return False, "❌ 未找到 async/await（ReAct Agent 应该用异步）"


def 检查_工具注册(代码: str) -> Tuple[bool, str]:
    """检查 3：是否有工具注册机制"""
    树 = ast.parse(代码)
    找到了 = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    找到了 = True
                    详情.append("✅ 找到工具注册逻辑（字典下标赋值）")
    
    if not 找到了:
        # 再检查是否有 TOOLS/registry 变量
        for node in ast.walk(树):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and ("tool" in target.id.lower() or "registry" in target.id.lower()):
                        找到了 = True
                        详情.append(f"✅ 找到工具变量：{target.id}")
    
    if 找到了:
        return True, "\n".join(详情)
    return False, "❌ 未找到工具注册机制"


def 检查_react格式解析(代码: str) -> Tuple[bool, str]:
    """检查 4：是否解析 ReAct 格式（Thought/Action/Observation）"""
    关键词 = ["Thought", "Action", "Action Input", "Observation", "Final Answer"]
    找到了 = []
    for kw in 关键词:
        if kw in 代码:
            找到了.append(kw)
    
    if len(找到了) >= 3:
        return True, f"✅ 找到 ReAct 格式关键词：{', '.join(找到了)}"
    elif len(找到了) > 0:
        return True, f"⚠️ 只找到部分关键词：{', '.join(找到了)}（建议包含 Thought/Action/Observation/Final Answer）"
    return False, "❌ 未找到 ReAct 格式解析（需要解析 Thought/Action 等）"


def 检查_正则或字符串解析(代码: str) -> Tuple[bool, str]:
    """检查 5：是否用正则或字符串方法解析响应"""
    树 = ast.parse(代码)
    找到了 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.Attribute):
            if node.attr in ("search", "findall", "match", "find", "split", "index"):
                找到了.append(node.attr)
    
    if "search" in 找到了 or "findall" in 找到了:
        return True, f"✅ 找到正则解析（{', '.join(set(找到了))}）"
    elif 找到了:
        return True, f"✅ 找到字符串解析（{', '.join(set(找到了))}）"
    return True, "⚠️ 未找到明确的解析逻辑（可用正则或字符串方法）"


def 检查_工具执行(代码: str) -> Tuple[bool, str]:
    """检查 6：是否有工具执行逻辑"""
    关键词 = ["execute_tool", "call_tool", "执行工具", "调用工具"]
    找到了 = []
    for kw in 关键词:
        if kw in 代码:
            找到了.append(kw)
    
    if 找到了:
        return True, f"✅ 找到工具执行函数：{', '.join(找到了)}"
    return True, "⚠️ 未找到明确的工具执行函数（建议命名为 execute_tool）"


def 检查_步骤记录(代码: str) -> Tuple[bool, str]:
    """检查 7：是否记录了执行步骤（用于调试和上下文）"""
    关键词 = ["steps", "history", "messages", "步骤", "历史"]
    找到了 = []
    for kw in 关键词:
        if kw in 代码:
            找到了.append(kw)
    
    if len(找到了) >= 1:
        return True, f"✅ 找到步骤记录变量：{', '.join(找到了)}"
    return True, "⚠️ 未找到步骤记录（建议用 list 记录每步的 Thought/Action/Observation）"


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
    elif 有注解 > 0:
        return True, f"⚠️ 类型注解较少（{有注解} 处注解，建议多加）"
    return False, "❌ 未找到类型注解（建议加上）"


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
        # 检查输出是否包含 Agent 回答
        if "最终回答" in 输出 or "Answer" in 输出 or "答案" in 输出:
            return True, f"✅ 代码运行成功，Agent 有输出（耗时 {耗时:.2f} 秒）"
        return True, f"✅ 代码运行成功（耗时 {耗时:.2f} 秒）\n   输出预览：\n{输出[:300]}"
    return False, f"❌ 代码运行失败：\n{输出[:500]}"


# ==================== 主逻辑 ====================

def 验收(文件路径: Path) -> int:
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 6 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        打印(f"   请创建 {文件路径.name}，或指定正确路径", C.YELLOW)
        return 0
    
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    检查项 = [
        ("ReAct 主循环（for/while + max_steps）", 检查_react循环),
        ("async/await 使用", 检查_async_await),
        ("工具注册机制", 检查_工具注册),
        ("ReAct 格式解析（Thought/Action/...）", 检查_react格式解析),
        ("正则/字符串解析逻辑", 检查_正则或字符串解析),
        ("工具执行函数", 检查_工具执行),
        ("步骤记录（上下文管理）", 检查_步骤记录),
        ("类型注解", 检查_类型注解),
    ]
    
    分数 = 0
    满分 = len(检查项) * 10 + 20
    
    for 名称, 检查函数 in 检查项:
        通过, 消息 = 检查函数(代码)
        打印(f"  [{名称}]", C.BLUE)
        if 通过 and "⚠️" not in 消息:
            打印(f"  {消息}", C.GREEN)
            分数 += 10
        elif "⚠️" in 消息:
            打印(f"  {消息}", C.YELLOW)
            分数 += 5
        else:
            打印(f"  {消息}", C.RED)
    
    # 运行检查
    打印(f"\n  [代码可运行 + Agent 有输出]", C.BLUE)
    通过, 消息 = 检查_代码可运行(文件路径)
    打印(f"  {消息}", C.GREEN if 通过 else C.RED)
    if 通过:
        分数 += 20
    
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    
    if 分数 >= 80:
        打印(f"  🎉 验收通过！你成功手写了 ReAct Agent！", C.GREEN)
    elif 分数 >= 60:
        打印(f"  ⚠️ 基本通过，建议改进后再继续", C.YELLOW)
    else:
        打印(f"  ❌ 还需努力，参考上面提示改进", C.RED)
    
    打印(f"{'='*60}\n", C.CYAN)
    
    if 分数 < 80:
        打印("📋 改进建议：", C.YELLOW)
        if not 检查_react循环(代码)[0]:
            打印("  • 实现 ReAct 主循环：for step in range(max_steps):", C.YELLOW)
        if not 检查_async_await(代码)[0]:
            打印("  • 用 async def 定义 Agent，内部用 await 调用 LLM", C.YELLOW)
        if not 检查_react格式解析(代码)[0]:
            打印("  • 解析 LLM 响应中的 Thought/Action/Action Input/Observation", C.YELLOW)
        if not 检查_工具执行(代码)[0]:
            打印("  • 实现 execute_tool() 函数，根据 Action 调用对应工具", C.YELLOW)
        print()
    
    return 分数


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 6 练习验收脚本")
    parser.add_argument("--file", default="day06_practice_template.py", help="练习文件路径")
    args = parser.parse_args()
    文件路径 = Path(args.file)
    验收(文件路径)


if __name__ == "__main__":
    main()
