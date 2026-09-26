"""
Day 2 练习项目验收脚本（行为级验收）
用 Pydantic 定义 Tool Schema + 装饰器实现工具注册机制

运行方式：
    python day02_practice_validator.py                  # 验收默认模板文件
    python day02_practice_validator.py --file 你的练习.py

验收方式：
    直接调用你注册的工具、你的调用函数、你的 Schema，
    检查真实行为（注册、计算结果、类型校验、OpenAI 格式）。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。

依赖：pip install pydantic
"""

import argparse
import ast
import asyncio
import importlib.util
import inspect
import os
import sys
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day02_practice_template.py"
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
    spec = importlib.util.spec_from_file_location("学生练习_day02", 文件路径)
    模块 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(模块)
    return 模块


class 验收器:
    def __init__(self):
        self.总分 = 0

    def 检查(self, 名称: str, 分值: int, 函数, *参数):
        """运行单个检查；检查函数返回 (得分, 消息)，抛异常记 0 分"""
        打印(f"\n【{名称}】（{分值}分）", C.CYAN)
        try:
            得分, 消息 = 函数(*参数)
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_wraps(文件路径):
    """AST 检查：@工具 装饰器内部必须使用 functools.wraps"""
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    for 节点 in ast.walk(树):
        if isinstance(节点, (ast.FunctionDef, ast.AsyncFunctionDef)) and 节点.name == "工具":
            for 子 in ast.walk(节点):
                if isinstance(子, ast.Call) and isinstance(子.func, ast.Attribute) and 子.func.attr == "wraps":
                    return 10, "✅ 装饰器中使用了 functools.wraps"
    return 0, "❌ 装饰器中没有 functools.wraps——不加它，被装饰函数的 __name__/__doc__ 会丢失"


def 检查_注册表(模块):
    表 = getattr(模块, "工具注册表", None)
    assert isinstance(表, dict), f"工具注册表应是 dict，实际 {type(表).__name__}"
    assert len(表) >= 3, f"应至少注册 3 个工具（TODO 3.1-3.3），实际注册了 {len(表)} 个"
    assert "计算器" in 表, "注册表中应包含「计算器」"
    for 名称, 信息 in 表.items():
        assert "描述" in 信息 and "函数" in 信息, f"工具「{名称}」的注册信息缺少 描述/函数 字段"
    return 15, f"✅ 注册了 {len(表)} 个工具：{list(表.keys())}"


def 检查_调用工具(模块):
    调用 = getattr(模块, "调用工具", None)
    assert callable(调用), "没有找到 调用工具 函数（TODO 4.1）"
    结果 = 调用("计算器", 表达式="3 + 5 * 2")
    assert 结果 is not None, "调用工具 返回了 None——TODO 4.1 还没实现"
    assert isinstance(结果, dict), f"应返回字典，实际 {type(结果).__name__}"
    值 = 结果.get("结果")
    try:
        数值 = float(str(值))
    except (TypeError, ValueError):
        数值 = None
    assert 数值 == 13, f"3 + 5 * 2 的计算结果应为 13，实际 {值!r}"
    return 20, f"✅ 调用工具('计算器', 表达式='3 + 5 * 2') = {值}"


def 检查_类型校验(模块):
    """错误类型（int 传给 str 字段）必须被 Pydantic 拦截"""
    try:
        结果 = 模块.调用工具("计算器", 表达式=12345)
    except Exception as e:
        return 15, f"✅ 错误类型被拦截（抛出 {type(e).__name__}）"
    if 结果 is None:
        return 0, "❌ 错误类型没有被拦截（返回 None）——TODO 2.2 输入验证未实现"
    if isinstance(结果, dict) and "错误" in str(结果.get("结果", "")):
        return 15, f"✅ 错误类型被拦截（返回错误信息：{结果.get('结果')!r}）"
    return 0, f"❌ 表达式传 int 也能正常执行（{结果!r}），输入验证未生效"


def 检查_工具列表(模块):
    列出 = getattr(模块, "列出所有工具", None)
    assert callable(列出), "没有找到 列出所有工具 函数（TODO 4.2）"
    列表 = 列出()
    assert isinstance(列表, list), f"应返回列表，实际 {type(列表).__name__}"
    assert len(列表) >= 3, f"应返回至少 3 个工具，实际 {len(列表)} 个"
    for item in 列表:
        assert isinstance(item, dict) and item.get("type") == "function", (
            f"每项的 type 应为 'function'，实际 {item!r}"
        )
        fn = item.get("function") or {}
        assert fn.get("name") and fn.get("description"), f"工具 {fn.get('name')!r} 缺少 name/description"
        参数 = fn.get("parameters") or {}
        assert isinstance(参数, dict) and 参数.get("properties"), (
            f"工具 {fn.get('name')!r} 的 parameters 缺少 properties（提示：用 model_json_schema()）"
        )
    return 20, f"✅ {len(列表)} 个工具均为 OpenAI Function Calling 格式"


def 检查_注册函数可直接调用(模块):
    表 = 模块.工具注册表
    函数 = 表["计算器"]["函数"]
    结果 = 函数(表达式="1 + 1")
    assert 结果 is not None, "注册表里的计算器函数调用后返回 None"
    assert 函数.__name__ == "计算", (
        f"functools.wraps 未生效：__name__ 变成了 {函数.__name__!r}（应为 '计算'）"
    )
    return 15, "✅ 注册的函数可直接调用，且保留了原函数名（wraps 生效）"


# ==================== 主流程 ====================

def 运行验收(验收员, 模块, 文件路径):
    验收员.检查("装饰器使用 functools.wraps", 10, 检查_wraps, 文件路径)
    验收员.检查("工具注册表：至少 3 个工具", 15, 检查_注册表, 模块)
    验收员.检查("调用工具：计算器算出 13", 20, 检查_调用工具, 模块)
    验收员.检查("输入验证：错误类型被拦截", 15, 检查_类型校验, 模块)
    验收员.检查("列出所有工具：OpenAI 格式", 20, 检查_工具列表, 模块)
    验收员.检查("注册的函数可直接调用 + wraps 生效", 15, 检查_注册函数可直接调用, 模块)


def main():
    parser = argparse.ArgumentParser(description="Day 2 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 2 练习验收 —— Pydantic Schema + 工具注册装饰器")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day02_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        print("  💡 Day 2 需要 pydantic：pip install pydantic")
    except Exception as e:
        加载分 = 0
        模块 = None
        打印(f"  ❌ 加载失败：{type(e).__name__}: {e}", C.RED)
        print("  💡 请先修复语法/运行错误再验收")

    验收员 = 验收器()
    验收员.总分 += 加载分
    if 模块 is not None:
        运行验收(验收员, 模块, 文件路径)

    总分 = 验收员.总分
    打印("\n" + "=" * 60)
    if 总分 >= 优秀线:
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你掌握了 Pydantic + 装饰器注册工具！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
