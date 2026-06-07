#!/usr/bin/env python3
"""
Day 5 练习验收脚本
验收内容：命令行 AI 助手综合实战

使用方法：
    python day05_practice_validator.py
    python day05_practice_validator.py --file day05_practice.py
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

def 检查_pydantic模型(代码: str) -> Tuple[bool, str]:
    """检查 1：是否用 Pydantic 定义了数据结构"""
    树 = ast.parse(代码)
    找到模型 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if (isinstance(base, ast.Attribute) and base.attr == "BaseModel") or \
                   (isinstance(base, ast.Name) and base.id == "BaseModel"):
                    找到模型.append(node.name)
    
    if 找到模型:
        return True, f"✅ 找到 {len(找到模型)} 个 Pydantic 模型：{', '.join(找到模型)}"
    return False, "❌ 未找到 Pydantic 模型（需要定义 ChatMessage、AgentConfig 等）"


def 检查_工具注册(代码: str) -> Tuple[bool, str]:
    """检查 2：是否有工具注册和调用"""
    关键词 = ["TOOLS_REGISTRY", "工具注册", "tool", "execute_tool"]
    找到 = sum(1 for kw in 关键词 if kw.lower() in 代码.lower())
    
    if 找到 >= 3:
        return True, f"✅ 找到工具系统相关代码（{找到}/4 个关键词）"
    return False, f"❌ 工具系统不完整（{找到}/4 个关键词）"


def 检查_async_await(代码: str) -> Tuple[bool, str]:
    """检查 3：是否使用了 async/await"""
    树 = ast.parse(代码)
    有_async = False
    有_await = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.AsyncFunctionDef):
            有_async = True
        if isinstance(node, ast.Await):
            有_await = True
    
    if 有_async and 有_await:
        return True, "✅ 使用了 async/await（异步调用）"
    return False, "❌ 未使用 async/await（Agent 应该用异步）"


def 检查_流式输出(代码: str) -> Tuple[bool, str]:
    """检查 4：是否有流式输出（yield / AsyncGenerator）"""
    树 = ast.parse(代码)
    有_yield = False
    有_AsyncGenerator = False
    
    for node in ast.walk(树):
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            有_yield = True
        if isinstance(node, ast.AsyncFunctionDef):
            if node.returns:
                注解 = ast.unparse(node.returns) if hasattr(ast, 'unparse') else ""
                if "AsyncGenerator" in 注解 or "Generator" in 注解:
                    有_AsyncGenerator = True
    
    if 有_yield:
        return True, "✅ 找到流式输出（yield 逐 chunk 产出）"
    return True, "⚠️ 未找到流式输出（建议用 async def + yield 实现流式）"


def 检查_function_calling(代码: str) -> Tuple[bool, str]:
    """检查 5：是否有 Function Calling 流程"""
    关键词 = ["tool_calls", "get_tools_for_api", "function", "choices", "role"]
    找到 = sum(1 for kw in 关键词 if kw in 代码)
    
    if 找到 >= 4:
        return True, f"✅ Function Calling 流程较完整（{找到}/5 个关键词）"
    elif 找到 >= 2:
        return True, f"⚠️ Function Calling 流程不完整（{找到}/5 个关键词）"
    return False, "❌ 未找到 Function Calling 流程"


def 检查_CLI交互(代码: str) -> Tuple[bool, str]:
    """检查 6：是否有命令行交互界面"""
    关键词 = ["input(", "input", "exit", "quit", "print("]
    找到 = sum(1 for kw in 关键词 if kw in 代码)
    
    if 找到 >= 2:
        return True, f"✅ 找到命令行交互代码（{找到}/5 个关键词）"
    return True, "⚠️ 命令行交互部分不完整"


def 检查_错误处理(代码: str) -> Tuple[bool, str]:
    """检查 7：是否有错误处理"""
    树 = ast.parse(代码)
    有_try = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.Try):
            有_try = True
    
    if 有_try:
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
    
    if 有注解 >= 5:
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


# ==================== 主逻辑 ====================

def 验收(文件路径: Path) -> int:
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 5 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        return 0
    
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    检查项 = [
        ("Pydantic 数据模型定义", 检查_pydantic模型),
        ("工具注册和调用系统", 检查_工具注册),
        ("async/await 使用", 检查_async_await),
        ("流式输出（yield）", 检查_流式输出),
        ("Function Calling 流程", 检查_function_calling),
        ("命令行交互界面", 检查_CLI交互),
        ("错误处理（try/except）", 检查_错误处理),
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
        分数 += 20
    
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    
    if 分数 >= 80:
        打印(f"  🎉 验收通过！你成功构建了命令行 AI 助手！", C.GREEN)
    elif 分数 >= 60:
        打印(f"  ⚠️ 基本通过，建议改进后再继续", C.YELLOW)
    else:
        打印(f"  ❌ 还需努力，参考上面提示改进", C.RED)
    
    打印(f"{'='*60}\n", C.CYAN)
    return 分数


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 5 练习验收脚本")
    parser.add_argument("--file", default="day05_practice_template.py", help="练习文件路径")
    args = parser.parse_args()
    文件路径 = Path(args.file)
    验收(文件路径)


if __name__ == "__main__":
    main()
