#!/usr/bin/env python3
"""
Day 7 练习验收脚本
验收内容：LangGraph ReAct Agent

使用方法：
    python day07_practice_validator.py
    python day07_practice_validator.py --file day07_practice.py
"""

import ast
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Tuple

TIMEOUT = 30

class C:
    GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; BLUE = "\033[94m"; CYAN = "\033[96m"; BOLD = "\033[1m"; END = "\033[0m"

def 打印(内容: str, 颜色: str = C.END):
    print(f"{C.BOLD}{颜色}{内容}{C.END}")

def 检查_state定义(代码: str) -> Tuple[bool, str]:
    树 = ast.parse(代码)
    for node in ast.walk(树):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if (isinstance(base, ast.Attribute) and base.attr == "TypedDict") or \
                   (isinstance(base, ast.Name) and base.id == "TypedDict"):
                    return True, f"✅ 找到 AgentState（TypedDict）：{node.name}"
                if (isinstance(base, ast.Attribute) and base.attr == "BaseModel") or \
                   (isinstance(base, ast.Name) and base.id == "BaseModel"):
                    return True, f"✅ 找到 AgentState（Pydantic BaseModel）：{node.name}"
    return False, "❌ 未找到 AgentState 类型定义（需要 TypedDict 或 BaseModel）"

def 检查_node定义(代码: str) -> Tuple[bool, str]:
    树 = ast.parse(代码)
    节点 = []
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            if "node_" in node.name or "call_model" in node.name or "call_tool" in node.name:
                节点.append(node.name)
    if len(节点) >= 2:
        return True, f"✅ 找到 {len(节点)} 个 Node 函数：{', '.join(节点)}"
    elif 节点:
        return True, f"⚠️ 只找到 {len(节点)} 个 Node：{', '.join(节点)}（建议至少有 call_model 和 call_tool）"
    return False, "❌ 未找到 Node 函数定义"

def 检查_路由器(代码: str) -> Tuple[bool, str]:
    关键词 = ["router", "conditional_edges", "should_continue", "路由"]
    找到 = [kw for kw in 关键词 if kw in 代码]
    if 找到:
        return True, f"✅ 找到条件路由：{', '.join(找到)}"
    return True, "⚠️ 未找到条件路由（需要 router_should_continue 或类似函数）"

def 检查_graph构建(代码: str) -> Tuple[bool, str]:
    关键词 = ["StateGraph", "add_node", "add_edge", "compile", "set_entry_point"]
    找到数 = sum(1 for kw in 关键词 if kw in 代码)
    if 找到数 >= 3:
        return True, f"✅ 找到 LangGraph 构建代码（{找到数}/5 个 API）"
    elif 找到数 >= 1:
        return True, f"⚠️ Graph 构建不完整（{找到数}/5 个 API）"
    return True, "⚠️ 未找到 LangGraph API（可能用的是模拟器）"

def 检查_工具执行(代码: str) -> Tuple[bool, str]:
    if "execute_tool" in 代码 or "TOOLS_REGISTRY" in 代码:
        return True, "✅ 找到工具执行系统"
    return False, "❌ 未找到工具执行系统"

def 检查_模拟或真实LLM(代码: str) -> Tuple[bool, str]:
    if "mock_llm" in 代码 or "langchain" in 代码.lower() or "ChatOpenAI" in 代码:
        return True, "✅ 找到 LLM 调用逻辑"
    return True, "⚠️ 未找到 LLM 调用（可以用 mock 测试流程）"

def 检查_错误处理(代码: str) -> Tuple[bool, str]:
    树 = ast.parse(代码)
    for node in ast.walk(树):
        if isinstance(node, ast.Try):
            return True, "✅ 有 try/except 错误处理"
    return False, "❌ 未找到错误处理"

def 检查_类型注解(代码: str) -> Tuple[bool, str]:
    树 = ast.parse(代码)
    有注解 = sum(1 for node in ast.walk(树) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None)
    return (True, f"✅ 类型注解较好（{有注解} 个函数有返回注解）") if 有注解 >= 2 else (True, f"⚠️ 类型注解较少（{有注解} 个）")

def 运行用户代码(文件路径: Path) -> Tuple[bool, str, float]:
    try:
        开始 = time.time()
        结果 = subprocess.run([sys.executable, str(文件路径)], capture_output=True, text=True, timeout=TIMEOUT)
        return (True, 结果.stdout, time.time() - 开始) if 结果.returncode == 0 else (False, f"运行失败：\n{结果.stderr[:500]}", time.time() - 开始)
    except subprocess.TimeoutExpired:
        return False, f"⏰ 运行超时（{TIMEOUT}s）", TIMEOUT
    except Exception as e:
        return False, f"出错：{e}", 0.0

def 检查_代码可运行(文件路径: Path) -> Tuple[bool, str]:
    成功, 输出, 耗时 = 运行用户代码(文件路径)
    if 成功:
        return True, f"✅ 代码运行成功（耗时 {耗时:.2f}s）\n   输出：\n{输出[:300]}"
    return False, f"❌ {输出[:500]}"

def 验收(文件路径: Path) -> int:
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 7 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        return 0
    
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    检查项 = [
        ("AgentState 类型定义", 检查_state定义),
        ("至少 2 个 Node（call_model + call_tool）", 检查_node定义),
        ("条件路由器（router_should_continue）", 检查_路由器),
        ("LangGraph 构建（StateGraph）", 检查_graph构建),
        ("工具执行系统", 检查_工具执行),
        ("LLM 调用逻辑", 检查_模拟或真实LLM),
        ("错误处理（try/except）", 检查_错误处理),
        ("类型注解", 检查_类型注解),
    ]
    
    分数, 满分 = 0, len(检查项) * 10 + 20
    
    for 名称, 检查 in 检查项:
        通过, 消息 = 检查(代码)
        打印(f"  [{名称}]", C.BLUE)
        c = C.GREEN if "✅" in 消息 else (C.YELLOW if "⚠️" in 消息 else C.RED)
        pts = 10 if "✅" in 消息 else (5 if "⚠️" in 消息 else 0)
        打印(f"  {消息}", c)
        分数 += pts
    
    打印(f"\n  [代码可运行性]", C.BLUE)
    通过, 消息 = 检查_代码可运行(文件路径)
    c = C.GREEN if 通过 else C.RED
    打印(f"  {消息}", c)
    if 通过: 分数 += 20
    
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    if 分数 >= 80: 打印(f"  🎉 验收通过！LangGraph ReAct Agent 流程正确！", C.GREEN)
    elif 分数 >= 60: 打印(f"  ⚠️ 基本通过", C.YELLOW)
    else: 打印(f"  ❌ 还需努力", C.RED)
    打印(f"{'='*60}\n", C.CYAN)
    return 分数

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 7 练习验收脚本")
    parser.add_argument("--file", default="day07_practice_template.py", help="练习文件路径")
    验收(Path(parser.parse_args().file))

if __name__ == "__main__":
    main()
