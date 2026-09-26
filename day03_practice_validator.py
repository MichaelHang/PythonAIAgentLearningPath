"""
Day 3 练习项目验收脚本（行为级验收）
实现流式 LLM 响应的异步生成器包装器

运行方式：
    python day03_practice_validator.py                  # 验收默认模板文件
    python day03_practice_validator.py --file 你的练习.py

验收方式：
    直接迭代你写的生成器、进入你写的上下文管理器、调用你的流式客户端，
    检查真实行为（是否真的逐块 yield、__enter__ 是否返回 self 等）。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。
"""

import argparse
import asyncio
import importlib.util
import inspect
import io
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

os.system("")  # 让 Windows 终端支持 ANSI 颜色

DEFAULT_FILE = "day03_practice_template.py"
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
    spec = importlib.util.spec_from_file_location("学生练习_day03", 文件路径)
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
                得分, 消息 = await asyncio.wait_for(函数(*参数), timeout=30)
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

def 检查_同步生成器(模块):
    生成器 = 模块.模拟_llm_流式输出_同步("你好世界", 延迟秒=0)
    chunks = list(生成器)
    assert len(chunks) >= 3, f"应逐块 yield 至少 3 个 chunk，实际 {len(chunks)} 个：{chunks!r}"
    assert all(isinstance(c, str) for c in chunks), "每个 chunk 都应是字符串"
    return 15, f"✅ 同步生成器逐块产出 {len(chunks)} 个 chunk"


async def 检查_异步生成器(模块):
    chunks = []
    async for c in 模块.模拟_llm_流式输出_异步("你好世界", 延迟秒=0):
        chunks.append(c)
    assert len(chunks) >= 3, (
        f"应逐块 yield 至少 3 个 chunk，实际 {len(chunks)} 个。"
        "注意：必须是 async def + yield（缺 yield 就不是异步生成器，无法 async for）"
    )
    assert all(isinstance(c, str) for c in chunks), "每个 chunk 都应是字符串"
    return 15, f"✅ 异步生成器逐块产出 {len(chunks)} 个 chunk"


def 检查_同步计时器类(模块):
    计时器 = 模块.LLM请求计时器()
    返回值 = 计时器.__enter__()
    assert 返回值 is 计时器, f"__enter__ 应返回 self，实际返回 {返回值!r}"
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        with 模块.LLM请求计时器():
            time.sleep(0.05)
    assert 缓冲.getvalue().strip(), "__exit__ 应打印耗时信息"
    return 10, "✅ __enter__ 返回 self，with 结束后打印耗时"


def 检查_contextmanager版本(模块):
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        with 模块.llm请求计时器_装饰器版本("验收测试"):
            time.sleep(0.05)
    assert 缓冲.getvalue().strip(), "yield 之后应打印耗时（没有 yield 会报 RuntimeError）"
    return 10, "✅ @contextmanager 版本可用（yield 前/后逻辑正确）"


async def 检查_异步计时器类(模块):
    计时器 = 模块.异步LLM请求计时器()
    返回值 = await 计时器.__aenter__()
    assert 返回值 is 计时器, f"__aenter__ 应返回 self，实际返回 {返回值!r}"
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        async with 模块.异步LLM请求计时器():
            await asyncio.sleep(0.05)
    assert 缓冲.getvalue().strip(), "__aexit__ 应打印耗时信息"
    return 10, "✅ __aenter__ 返回 self，async with 结束后打印耗时"


async def 检查_asynccontextmanager版本(模块):
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        async with 模块.异步请求计时器("验收测试"):
            await asyncio.sleep(0.05)
    assert 缓冲.getvalue().strip(), "yield 之后应打印耗时"
    return 10, "✅ @asynccontextmanager 版本可用"


async def 检查_流式客户端(模块):
    客户端 = 模块.流式LLM客户端(模型名称="deepseek-chat")
    生成器 = 客户端.chat("请介绍一下你自己")
    assert hasattr(生成器, "__aiter__"), (
        f"chat() 应返回异步生成器（async def + yield），实际返回 {type(生成器).__name__}"
    )
    chunks = []
    缓冲 = io.StringIO()
    with redirect_stdout(缓冲):
        async for c in 生成器:
            chunks.append(c)
    assert len(chunks) >= 3, f"应逐块 yield 多个 chunk，实际 {len(chunks)} 个"
    assert all(isinstance(c, str) for c in chunks), "每个 chunk 都应是字符串"
    assert 缓冲.getvalue().strip() or True  # 计时输出可有可无，不强制
    return 25, f"✅ 流式客户端 chat() 逐块产出 {len(chunks)} 个 chunk"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块):
    await 验收员.检查("同步生成器：逐块 yield", 15, 检查_同步生成器, 模块)
    await 验收员.检查("异步生成器：逐块 yield", 15, 检查_异步生成器, 模块)
    await 验收员.检查("同步计时器类：__enter__/__exit__", 10, 检查_同步计时器类, 模块)
    await 验收员.检查("@contextmanager 版本", 10, 检查_contextmanager版本, 模块)
    await 验收员.检查("异步计时器类：__aenter__/__aexit__", 10, 检查_异步计时器类, 模块)
    await 验收员.检查("@asynccontextmanager 版本", 10, 检查_asynccontextmanager版本, 模块)
    await 验收员.检查("流式 LLM 客户端：chat() 异步流式", 25, 检查_流式客户端, 模块)


def main():
    parser = argparse.ArgumentParser(description="Day 3 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 3 练习验收 —— 流式 LLM 响应的异步生成器包装器")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day03_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        asyncio.run(运行验收(验收员, 模块))

    总分 = 验收员.总分
    打印("\n" + "=" * 60)
    if 总分 >= 优秀线:
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！生成器 + 上下文管理器都掌握了！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
