#!/usr/bin/env python3
"""
Day 3 练习验收脚本
验收内容：生成器、异步生成器、上下文管理器

使用方法：
    python day03_practice_validator.py
    python day03_practice_validator.py --file day03_practice.py
"""

import ast
import inspect
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

def 检查_同步生成器(代码: str) -> Tuple[bool, str]:
    """检查 1：是否有同步生成器（def + yield）"""
    树 = ast.parse(代码)
    找到了 = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Yield) or isinstance(child, ast.YieldFrom):
                    找到了 = True
                    详情.append(f"✅ 找到同步生成器：{node.name}（包含 yield）")
                    break
    
    if 找到了:
        return True, "\n".join(详情)
    return False, "❌ 未找到同步生成器（需要用 def + yield）"


def 检查_异步生成器(代码: str) -> Tuple[bool, str]:
    """检查 2：是否有异步生成器（async def + yield）"""
    树 = ast.parse(代码)
    找到了 = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Yield) or isinstance(child, ast.YieldFrom):
                    找到了 = True
                    详情.append(f"✅ 找到异步生成器：{node.name}（async def + yield）")
                    break
    
    if 找到了:
        return True, "\n".join(详情)
    return False, "❌ 未找到异步生成器（需要用 async def + yield）"


def 检查_async_for(代码: str) -> Tuple[bool, str]:
    """检查 3：是否使用了 async for 迭代异步生成器"""
    树 = ast.parse(代码)
    找到了 = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.AsyncFor):
            找到了 = True
            break
    
    if 找到了:
        return True, "✅ 找到 async for（正确迭代异步生成器）"
    return True, "⚠️ 未找到 async for（建议用 async for 迭代异步生成器，也可以用其他方式）"


def 检查_上下文管理器类(代码: str) -> Tuple[bool, str]:
    """检查 4：是否实现了 __enter__/__exit__ 上下文管理器"""
    树 = ast.parse(代码)
    找到了 = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.ClassDef):
           方法列表 = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
            if "__enter__" in 方法列表 and "__exit__" in 方法列表:
                找到了 = True
                详情.append(f"✅ 找到类上下文管理器：{node.name}（有 __enter__/__exit__）")
    
    if 找到了:
        return True, "\n".join(详情)
    return False, "❌ 未找到类上下文管理器（需要实现 __enter__/__exit__）"


def 检查_contextmanager装饰器(代码: str) -> Tuple[bool, str]:
    """检查 5：是否使用了 @contextmanager"""
    树 = ast.parse(代码)
    找到了 = False
    
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Name) and decorator.id == "contextmanager") or \
                   (isinstance(decorator, ast.Attribute) and decorator.attr == "contextmanager"):
                    找到了 = True
                    break
    
    if 找到了:
        return True, "✅ 找到 @contextmanager 装饰器（简洁的上下文管理器实现）"
    return True, "⚠️ 未找到 @contextmanager（可以用类实现，也可以用 @contextmanager）"


def 检查_异步上下文管理器(代码: str) -> Tuple[bool, str]:
    """检查 6：是否有异步上下文管理器（__aenter__/__aexit__ 或 @asynccontextmanager）"""
    树 = ast.parse(代码)
    找到了类 = False
    找到了装饰器 = False
    详情 = []
    
    for node in ast.walk(树):
        # 检查类实现
        if isinstance(node, ast.ClassDef):
            方法列表 = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if "__aenter__" in 方法列表 and "__aexit__" in 方法列表:
                找到了类 = True
                详情.append(f"✅ 找到异步上下文管理器类：{node.name}")
        # 检查 @asynccontextmanager
        if isinstance(node, ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Name) and "async" in decorator.id.lower()) or \
                   (isinstance(decorator, ast.Attribute) and "async" in decorator.attr.lower()):
                    找到了装饰器 = True
                    详情.append(f"✅ 找到 @asynccontextmanager 装饰器")
                    break
    
    if 找到了类 or 找到了装饰器:
        return True, "\n".join(详情)
    return False, "❌ 未找到异步上下文管理器（需要 __aenter__/__aexit__ 或 @asynccontextmanager）"


def 检查_流式输出模拟(代码: str) -> Tuple[bool, str]:
    """检查 7：生成器是否逐 chunk 产出（多次 yield，不是一次 return）"""
    树 = ast.parse(代码)
    生成器函数 = []
    
    for node in ast.walk(树):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield_count = sum(1 for child in ast.walk(node) 
                           if isinstance(child, (ast.Yield, ast.YieldFrom)))
            if yield_count >= 2:
                生成器函数.append(f"✅ {node.name} 有 {yield_count} 个 yield（逐 chunk 产出）")
    
    if 生成器函数:
        return True, "\n".join(生成器函数)
    return False, "⚠️ 未找到多次 yield 的生成器（流式输出应该多次 yield）"


def 检查_类型注解(代码: str) -> Tuple[bool, str]:
    """检查 8：是否有类型注解（Generator, AsyncGenerator 等）"""
    树 = ast.parse(代码)
    有注解 = 0
    
    for node in ast.walk(树):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                注解文本 = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                if "Generator" in 注解文本 or "AsyncGenerator" in 注解文本:
                    有注解 += 1
    
    if 有注解 >= 1:
        return True, f"✅ 找到 {有注解} 个带生成器类型注解的函数"
    return True, "⚠️ 未找到 Generator/AsyncGenerator 类型注解（建议加上）"


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
        return False, f"运行失败：\n{结果.stderr}", 耗时
    except subprocess.TimeoutExpired:
        return False, f"⏰ 运行超时（{TIMEOUT} 秒）", TIMEOUT
    except Exception as e:
        return False, f"运行出错：{e}", 0.0


def 检查_代码可运行(文件路径: Path) -> Tuple[bool, str]:
    成功, 输出, 耗时 = 运行用户代码(文件路径)
    if 成功:
        return True, f"✅ 代码运行成功（耗时 {耗时:.2f} 秒）\n   输出预览：\n{输出[:300]}{'...' if len(输出) > 300 else ''}"
    return False, f"❌ 代码运行失败：\n{输出[:500]}"


# ==================== 主逻辑 ====================

def 验收(文件路径: Path) -> int:
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 3 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        打印(f"   请创建 {文件路径.name}，或指定正确路径", C.YELLOW)
        return 0
    
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    检查项 = [
        ("同步生成器（def + yield）", 检查_同步生成器),
        ("异步生成器（async def + yield）", 检查_异步生成器),
        ("async for 使用", 检查_async_for),
        ("类上下文管理器（__enter__/__exit__）", 检查_上下文管理器类),
        ("@contextmanager 装饰器", 检查_contextmanager装饰器),
        ("异步上下文管理器（__aenter__/__aexit__）", 检查_异步上下文管理器),
        ("流式输出（多次 yield）", 检查_流式输出模拟),
        ("类型注解（Generator/AsyncGenerator）", 检查_类型注解),
    ]
    
    分数 = 0
    满分 = len(检查项) * 10 + 20
    
    for 名称, 检查函数 in 检查项:
        通过, 消息 = 检查函数(代码)
        打印(f"  [{名称}]", C.BLUE)
        if 通过:
            打印(f"  {消息}", C.GREEN)
            分数 += 10
        else:
            打印(f"  {消息}", C.RED)
    
    # 运行检查
    打印(f"\n  [代码可运行性]", C.BLUE)
    通过, 消息 = 检查_代码可运行(文件路径)
    if 通过:
        打印(f"  {消息}", C.GREEN)
        分数 += 20
    else:
        打印(f"  {消息}", C.RED)
    
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    
    if 分数 >= 80:
        打印(f"  🎉 验收通过！你对生成器和上下文管理器掌握很好！", C.GREEN)
    elif 分数 >= 60:
        打印(f"  ⚠️ 基本通过，还有改进空间", C.YELLOW)
    else:
        打印(f"  ❌ 还需努力，参考上面提示改进", C.RED)
    
    打印(f"{'='*60}\n", C.CYAN)
    
    if 分数 < 80:
        打印("📋 改进建议：", C.YELLOW)
        if not 检查_异步生成器(代码)[0]:
            打印("  • 异步生成器：async def 函数体里用 yield", C.YELLOW)
        if not 检查_异步上下文管理器(代码)[0]:
            打印("  • 异步上下文管理器：实现 __aenter__/__aexit__ 或用 @asynccontextmanager", C.YELLOW)
        if not 检查_流式输出模拟(代码)[0]:
            打印("  • 流式输出应该多次 yield，每次产出一个 chunk", C.YELLOW)
        print()
    
    return 分数


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 3 练习验收脚本")
    parser.add_argument("--file", default="day03_practice_template.py", help="练习文件路径")
    args = parser.parse_args()
    文件路径 = Path(args.file)
    验收(文件路径)


if __name__ == "__main__":
    main()
