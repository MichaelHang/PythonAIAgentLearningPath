"""
Day 1 练习项目验收脚本（行为级验收）
异步批量调用多个 API（模拟 Agent 多工具并发调用）

运行方式：
    python day01_practice_validator.py                  # 验收默认模板文件
    python day01_practice_validator.py --file 你的练习.py

验收方式：
    直接调用你实现的函数，检查返回结果和真实耗时。
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
import time
import types
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day01_practice_template.py"
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
    """动态加载学生练习文件；失败会抛异常"""
    spec = importlib.util.spec_from_file_location("学生练习_day01", 文件路径)
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
            得分, 消息 = 0, "❌ 检查超时——代码可能存在死循环或过长的 sleep"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_异步请求协程(模块):
    if not inspect.iscoroutinefunction(getattr(模块, "异步请求", None)):
        return 0, "❌ 异步请求 不是协程函数（需要 async def）"
    return 8, "✅ 异步请求 是 async 协程函数"


async def 检查_异步请求结果(模块):
    结果 = await 模块.异步请求("https://test.example.com/users", 延迟秒=0.2)
    assert isinstance(结果, dict), f"应返回字典，实际是 {type(结果).__name__}：{结果!r}"
    for key in ("url", "status", "data"):
        assert key in 结果, f"返回字典缺少字段：{key}（示例：{{'url': ..., 'status': 200, 'data': ...}}）"
    return 12, f"✅ 返回结构正确（status={结果.get('status')}）"


async def 检查_并发请求(模块):
    """并发请求：结果正确 + 真并发（用学生自己的单次耗时做基准）"""
    urls = [
        "https://a.example.com",
        "https://b.example.com",
        "https://c.example.com",
    ]
    开始 = time.time()
    结果 = await 模块.并发请求(urls)
    并发耗时 = time.time() - 开始

    assert isinstance(结果, list) and len(结果) == 3, f"应返回 3 个结果，实际 {结果!r}"
    assert all(isinstance(r, dict) for r in 结果), "每个结果都应是字典"

    单次开始 = time.time()
    await 模块.异步请求("https://single.example.com")
    单次耗时 = time.time() - 单次开始

    assert 并发耗时 < 单次耗时 * 2 + 0.2, (
        f"3 个请求耗时 {并发耗时:.2f}s ≈ 3 × 单次({单次耗时:.2f}s)，"
        "说明是逐个 await 而不是并发。请用 asyncio.gather() 或 create_task()"
    )
    return 25, f"✅ 3 个请求真并发完成：{并发耗时:.2f}s（单次基准 {单次耗时:.2f}s）"


def 检查_同步请求(模块):
    结果 = 模块.同步请求(["https://s1.example.com", "https://s2.example.com"])
    assert isinstance(结果, list) and len(结果) == 2, f"应返回 2 个结果，实际 {结果!r}"
    assert all(isinstance(r, dict) for r in 结果), "每个结果都应是字典"
    return 8, "✅ 同步请求返回 2 个结果（作为性能对比的慢基准）"


async def 检查_性能对比(模块):
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        await 模块.性能对比()
    输出 = 缓冲.getvalue()
    assert "同步" in 输出 and "异步" in 输出, "性能对比应打印同步和异步两种耗时"
    assert "秒" in 输出, "应打印耗时数值（秒）"
    return 12, "✅ 性能对比完成并打印两种耗时（异步应显著快于同步）"


async def 检查_重试机制(模块):
    # 注入假 random：第 1 次"失败"（0.99 > 0.3），之后都成功
    # 如果重试逻辑正确，函数会在重试后拿到成功结果
    序列 = iter([0.99, 0.01, 0.01, 0.01, 0.01])
    模块.random = types.SimpleNamespace(random=lambda: next(序列, 0.01))

    结果 = await asyncio.wait_for(
        模块.异步请求带重试("https://retry.example.com", 最大重试=3), timeout=15
    )
    assert isinstance(结果, dict), f"重试后应返回结果字典，实际 {结果!r}"
    return 20, "✅ 第 1 次模拟失败后成功重试，返回了正常结果"


def 检查_类型注解(文件路径):
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    函数们 = [n for n in ast.walk(树) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    有注解 = [f for f in 函数们 if f.returns is not None]
    assert len(有注解) >= 4, f"至少 4 个函数应有返回值类型注解，目前 {len(有注解)}/{len(函数们)}"
    return 10, f"✅ {len(有注解)}/{len(函数们)} 个函数有返回值注解"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("异步请求：是 async 协程函数", 8, 检查_异步请求协程, 模块)
    await 验收员.检查("异步请求：返回结构正确", 12, 检查_异步请求结果, 模块)
    await 验收员.检查("并发请求：结果正确且真并发", 25, 检查_并发请求, 模块)
    await 验收员.检查("同步请求：作为慢基准可用", 8, 检查_同步请求, 模块)
    await 验收员.检查("性能对比：打印两种耗时", 12, 检查_性能对比, 模块)
    await 验收员.检查("重试机制：失败后能重试", 20, 检查_重试机制, 模块)
    await 验收员.检查("类型注解", 10, 检查_类型注解, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 1 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 1 练习验收 —— 异步批量调用多个 API")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day01_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        print("  💡 安装依赖后重试")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！你掌握了 asyncio 并发！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
