"""
Day 9 练习项目验收脚本（行为级验收）
实现带记忆和 RAG 的 Agent

运行方式：
    python day09_practice_validator.py                  # 验收默认模板文件
    python day09_practice_validator.py --file 你的练习.py

验收方式：
    直接操作你的短期记忆（裁剪/清空/格式转换）、你的向量存储（检索排序）、
    你的 RAG 检索器，并跑两轮对话检查记忆是否真的留存。
    空白模板无法通过验收，只有真正完成 TODO 才能得分。
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

DEFAULT_FILE = "day09_practice_template.py"
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
    spec = importlib.util.spec_from_file_location("学生练习_day09", 文件路径)
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
            得分, 消息 = 0, "❌ 检查超时"
        except Exception as e:
            得分, 消息 = 0, f"❌ {type(e).__name__}: {e}"
        得分 = max(0, min(int(得分), 分值))
        self.总分 += 得分
        颜色 = C.GREEN if 得分 == 分值 else (C.YELLOW if 得分 > 0 else C.RED)
        打印(f"  {消息}  [得分 {得分}/{分值}]", 颜色)


# ==================== 各项检查 ====================

def 检查_添加裁剪(模块):
    m = 模块.ShortTermMemory(max_messages=5)
    assert hasattr(m, "add"), "ShortTermMemory 缺少 add 方法（TODO 1.1）"
    m.add("system", "你是 AI 助手")
    对话 = ["消息一", "消息二", "消息三", "消息四", "消息五"]
    for i, 内容 in enumerate(对话):
        m.add("user" if i % 2 == 0 else "assistant", 内容)
    assert len(m.messages) <= 5, (
        f"max_messages=5 时应自动裁剪到 ≤5 条，实际存了 {len(m.messages)} 条"
    )
    roles = [x.role for x in m.messages]
    assert "system" in roles, "裁剪后 system message 丢失了——人设必须永远保留"
    assert 对话[-1] in [x.content for x in m.messages], "最新消息不应被裁掉"
    assert 对话[0] not in [x.content for x in m.messages], "最旧的非 system 消息应被裁掉"
    return 12, f"✅ 裁剪正确：保留 {len(m.messages)} 条（含 system），最新消息在、最旧的被裁"


def 检查_API格式(模块):
    m = 模块.ShortTermMemory(max_messages=10)
    m.add("system", "你是助手")
    m.add("user", "你好")
    m.add("assistant", "你好！")
    fmt = m.to_api_format()
    assert isinstance(fmt, list), f"to_api_format 应返回列表，实际 {type(fmt).__name__}（TODO 1.3）"
    assert len(fmt) == 3, f"应有 3 条消息，实际 {len(fmt)} 条"
    for item in fmt:
        assert isinstance(item, dict) and "role" in item and "content" in item, (
            f"每条应为含 role/content 的字典，实际 {item!r}"
        )
    assert fmt[0]["role"] == "system" and fmt[1]["content"] == "你好", "消息顺序或内容不对"
    return 8, "✅ to_api_format 转换正确（可直接发给 LLM API）"


def 检查_清空(模块):
    m = 模块.ShortTermMemory(max_messages=10)
    m.add("system", "你是助手")
    m.add("user", "第一条")
    m.add("user", "第二条")
    m.clear()
    assert len(m.messages) == 1, f"clear 后应只剩 system 1 条，实际 {len(m.messages)} 条"
    assert m.messages[0].role == "system", "clear 应保留 system message（TODO 1.4）"
    return 5, "✅ clear 只保留 system，历史被清空"


def 检查_向量存储(模块):
    store = 模块.SimpleVectorStore()
    assert hasattr(store, "add"), "SimpleVectorStore 缺少 add 方法（TODO 2.1）"
    store.add("Python 是 AI 开发的主力语言", {"id": 1})
    store.add("AI Agent 的核心是 ReAct 循环", {"id": 2})
    store.add("今天北京天气晴朗", {"id": 3})
    结果 = store.search("AI Agent 核心", top_k=3)
    assert isinstance(结果, list) and 结果, (
        f"search 应返回非空列表，实际 {结果!r}（TODO 2.2）"
    )
    top = 结果[0]
    文档 = str(top[0])
    得分 = top[-1]
    assert "Agent" in 文档 or "核心" in 文档, (
        f"查询'AI Agent 核心'的最相关文档应是 Agent 那条，实际第一条是 {文档!r}"
    )
    try:
        assert float(得分) > 0, f"最相关文档的相似度应 > 0，实际 {得分!r}"
    except (TypeError, ValueError):
        pass  # 得分格式特殊时不强制
    return 20, f"✅ 检索排序正确：'{文档[:20]}…' 排第一"


def 检查_RAG检索(模块):
    r = 模块.RAGRetriever(模块.SimpleVectorStore())
    assert hasattr(r, "add_knowledge"), "RAGRetriever 缺少 add_knowledge（TODO 3.1）"
    r.add_knowledge("LangGraph 是图工作流框架")
    r.add_knowledge("ChromaDB 是向量数据库")
    retrieve = getattr(r, "retrieve", None)
    assert callable(retrieve), "RAGRetriever 缺少 retrieve（TODO 3.2）"
    out = retrieve("LangGraph 是什么", top_k=2)
    assert isinstance(out, str) and out.strip(), f"retrieve 应返回文本，实际 {out!r}"
    assert "LangGraph" in out, f"检索结果应包含相关资料（LangGraph），实际 {out[:80]!r}"
    return 15, "✅ RAG 检索：问题能命中最相关的知识并格式化输出"


async def 检查_记忆对话(模块):
    agent = 模块.MemoryAgent()
    assert hasattr(agent, "chat"), "MemoryAgent 缺少 chat（TODO 4.1）"
    assert hasattr(agent, "short_memory"), "MemoryAgent 应有 short_memory 属性"

    with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
        await asyncio.wait_for(agent.chat("我叫张三，我喜欢 Python"), timeout=20)
    roles = [(m.role, str(m.content)) for m in agent.short_memory.messages]
    assert any(r == "user" and "张三" in c for r, c in roles), (
        f"第一轮对话后，用户消息应写入短期记忆，实际 {roles!r}"
    )
    return 8, "✅ 第一轮：用户消息已写入短期记忆"

async def 检查_记忆留存(模块):
    agent = 模块.MemoryAgent()
    with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
        await asyncio.wait_for(agent.chat("我叫张三，我喜欢 Python"), timeout=20)
        await asyncio.wait_for(agent.chat("我叫什么名字？"), timeout=20)
    roles = [(m.role, str(m.content)) for m in agent.short_memory.messages]
    assert any(r == "user" and "张三" in c for r, c in roles), "第二轮之后第一轮的记忆丢了！"
    assert any(r == "user" and "名字" in c for r, c in roles), "第二轮的用户消息没有写入记忆"
    return 7, "✅ 第二轮：历史保留且新消息追加（多轮记忆正常）"


def 检查_压缩(模块):
    compress = getattr(模块, "compress_conversation", None)
    assert callable(compress), "没有找到 compress_conversation 函数（TODO 5.1）"
    msgs = [模块.ConversationMessage(role="system", content="你是测试助手")]
    for i in range(8):
        msgs.append(模块.ConversationMessage(
            role="user" if i % 2 == 0 else "assistant",
            content=f"这是第{i}轮对话的消息内容",
        ))
    结果 = compress(msgs, max_tokens=80)
    assert isinstance(结果, list), f"应返回消息列表，实际 {type(结果).__name__}"
    assert len(结果) < len(msgs), f"压缩后应变短：输入 {len(msgs)} 条，输出 {len(结果)} 条"
    assert 结果[0].role == "system", "压缩后 system message 不能丢"
    assert 结果[-1].content == msgs[-1].content, "最新一条消息应被保留"
    return 15, f"✅ 压缩正确：{len(msgs)} 条 → {len(结果)} 条，system 和最新消息都在"


def 检查_类型注解(文件路径):
    树 = ast.parse(文件路径.read_text(encoding="utf-8"))
    函数们 = [n for n in ast.walk(树) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    有注解 = [f for f in 函数们 if f.returns is not None]
    assert len(有注解) >= 4, f"至少 4 个函数应有返回值类型注解，目前 {len(有注解)}/{len(函数们)}"
    return 5, f"✅ {len(有注解)}/{len(函数们)} 个函数有返回值注解"


# ==================== 主流程 ====================

async def 运行验收(验收员, 模块, 文件路径):
    await 验收员.检查("短期记忆：添加 + 裁剪", 12, 检查_添加裁剪, 模块)
    await 验收员.检查("短期记忆：to_api_format", 8, 检查_API格式, 模块)
    await 验收员.检查("短期记忆：clear 保留 system", 5, 检查_清空, 模块)
    await 验收员.检查("向量存储：检索排序", 20, 检查_向量存储, 模块)
    await 验收员.检查("RAG 检索器", 15, 检查_RAG检索, 模块)
    await 验收员.检查("MemoryAgent：第一轮写入记忆", 8, 检查_记忆对话, 模块)
    await 验收员.检查("MemoryAgent：第二轮记忆留存", 7, 检查_记忆留存, 模块)
    await 验收员.检查("上下文压缩", 15, 检查_压缩, 模块)
    await 验收员.检查("类型注解", 5, 检查_类型注解, 文件路径)


def main():
    parser = argparse.ArgumentParser(description="Day 9 练习验收脚本（行为级验收）")
    parser.add_argument("--file", default=DEFAULT_FILE, help="练习文件路径（默认 %(default)s）")
    args = parser.parse_args()
    文件路径 = Path(args.file)

    打印("=" * 60)
    打印("📋 Day 9 练习验收 —— 记忆系统与 RAG")
    打印("=" * 60)
    打印(f"\n📂 验收文件：{文件路径}")

    if not 文件路径.exists():
        打印(f"\n❌ 文件不存在：{文件路径}", C.RED)
        print("请先完成 day09_practice_template.py 中的 TODO，或用 --file 指定你的练习文件")
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
        打印(f"  总分：{总分}/{满分}   🎉 验收通过！Agent 有记忆了！", C.GREEN)
    elif 总分 >= 通过线:
        打印(f"  总分：{总分}/{满分}   ⚠️ 基本通过，建议按上面的提示完善", C.YELLOW)
    else:
        打印(f"  总分：{总分}/{满分}   ❌ 未通过——先完成模板中标红的 TODO 再来验收", C.RED)
    打印("=" * 60)


if __name__ == "__main__":
    main()
