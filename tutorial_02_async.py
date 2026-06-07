"""
============================================================
Python 异步编程 零基础实战教程
============================================================
目标：从"完全不理解 async/await"到"能写并发 AI Agent 工具调用"

运行方式：python tutorial_02_async.py
学习方式：从上到下逐步阅读，每步都输出结果

核心理解（一句话）：
  同步 = 排队办事，一件一件来
  异步 = 同时拿号，谁先办完告诉我
============================================================
"""
import asyncio
import time
import random

print("=" * 60)
print("第 1 步：同步 vs 异步 —— 直观感受差异")
print("=" * 60)

def 同步烧水():
    """同步函数：一个做完才能做下一个"""
    print("  同步：开始烧水（等3秒）...")
    time.sleep(3)
    print("  同步：水烧好了")
    return "开水"

def 同步切菜():
    print("  同步：开始切菜（等2秒）...")
    time.sleep(2)
    print("  同步：菜切好了")
    return "菜"

async def 异步烧水():
    """异步函数：发出指令后不等，去做别的事"""
    print("  异步：开始烧水...")
    await asyncio.sleep(3)  # 注意：这里是 asyncio.sleep，不阻塞
    print("  异步：水烧好了！")
    return "开水"

async def 异步切菜():
    print("  异步：开始切菜...")
    await asyncio.sleep(2)
    print("  异步：菜切好了！")
    return "菜"

print("\n【同步模式】一件一件来：")
开始 = time.time()
同步烧水()
同步切菜()
同步耗时 = time.time() - 开始
print(f"  同步总耗时：{同步耗时:.1f}秒（3+2=5秒）\n")

print("【异步模式】同时进行：")

async def 异步做饭():
    """同时开始烧水和切菜！"""
    任务1 = asyncio.create_task(异步烧水())
    任务2 = asyncio.create_task(异步切菜())
    水, 菜 = await 任务1, await 任务2
    return 水, 菜

开始 = time.time()
asyncio.run(异步做饭())
异步耗时 = time.time() - 开始
print(f"  异步总耗时：{异步耗时:.1f}秒（只花了最长的3秒！）")
print()
print("👉 关键差异：同步 5 秒，异步 3 秒！因为烧水时切菜也在进行")
print()

print("=" * 60)
print("第 2 步：三个核心关键字 —— async / await / asyncio.run()")
print("=" * 60)

# async def：定义一个异步函数（协程函数）
# await：等待一个异步操作完成，但不阻塞整个程序
# asyncio.run()：启动事件循环，运行异步函数

async def 简单异步函数():
    print("  步骤一：开始")
    await asyncio.sleep(1)   # 模拟等待，释放控制权
    print("  步骤二：1秒后")
    await asyncio.sleep(0.5)
    print("  步骤三：又过了0.5秒")
    return "完成"

print("运行异步函数：")
结果 = asyncio.run(简单异步函数())
print(f"  返回结果：{结果}")
print()

print("=" * 60)
print("第 3 步：asyncio.gather() —— 并发执行多个任务")
print("=" * 60)

async def 下载文件(文件名, 用时):
    print(f"  开始下载 {文件名}（预计{用时}秒）...")
    await asyncio.sleep(用时)
    print(f"  {文件名} 下载完成！")
    return f"{文件名} 的内容"

async def 并发下载():
    """gather：同时启动所有下载，等全部完成"""
    开始 = time.time()
    结果们 = await asyncio.gather(
        下载文件("A.txt", 3),
        下载文件("B.txt", 2),
        下载文件("C.txt", 1),
    )
    耗时 = time.time() - 开始
    print(f"  三个文件下载完成，总耗时：{耗时:.1f}秒")
    return 结果们

asyncio.run(并发下载())
print("👉 gather() 并发执行，耗时取最长的那个（3秒），不是 3+2+1=6秒")
print()

print("=" * 60)
print("第 4 步：asyncio.create_task() —— 更灵活的任务管理")
print("=" * 60)

async def 灵活下载():
    """create_task：启动任务后可以先做别的事"""
    开始 = time.time()

    # 先启动大文件下载（不等待）
    大文件任务 = asyncio.create_task(下载文件("大文件.zip", 4))

    # 趁大文件下载时，快速下载小文件
    print("  先下载一个配置文件...")
    配置 = await 下载文件("config.json", 1)
    print(f"  配置下载完毕：{配置}")
    print("  再去下载一个图片...")
    图片 = await 下载文件("logo.png", 1)

    # 现在等大文件
    print("  等待大文件完成...")
    大文件 = await 大文件任务

    耗时 = time.time() - 开始
    print(f"  全部完成，总耗时：{耗时:.1f}秒")
    return 配置, 图片, 大文件

asyncio.run(灵活下载())
print()

print("=" * 60)
print("第 5 步：常见错误 —— 在 async 里用 time.sleep()")
print("=" * 60)

async def 错误示范():
    print("  错误：在 async 里用 time.sleep()")
    time.sleep(2)  # ❌ 这会阻塞整个事件循环！
    print("  整个程序被卡住了2秒")
    return "错误"

async def 正确示范():
    print("  正确：用 asyncio.sleep()")
    await asyncio.sleep(2)  # ✅ 不阻塞，其他任务可以跑
    print("  程序没有卡住")
    return "正确"

print("运行错误示范（你看会卡住）：")
asyncio.run(错误示范())
print()
print("运行正确示范：")
asyncio.run(正确示范())
print()
print("👉 黄金法则：async 函数里永远不用 time.sleep()，用 await asyncio.sleep()")
print()

print("=" * 60)
print("第 6 步：asyncio.Queue —— 生产者消费者模式")
print("=" * 60)

async def 生产者(queue, 数据列表):
    """不断往队列里放任务"""
    for i, 数据 in enumerate(数据列表):
        await asyncio.sleep(random.uniform(0.1, 0.5))  # 模拟生产间隔
        await queue.put(f"任务{i+1}: {数据}")
        print(f"  生产 → 任务{i+1}: {数据}")
    await queue.put(None)  # 结束信号

async def 消费者(queue, 编号):
    """不断从队列取任务并处理"""
    while True:
        任务 = await queue.get()
        if 任务 is None:
            await queue.put(None)  # 传给其他消费者
            break
        print(f"       消费者{编号} 处理 ← {任务}")
        await asyncio.sleep(random.uniform(0.3, 0.8))  # 模拟处理耗时

async def 生产消费示例():
    queue = asyncio.Queue()
    任务列表 = ["下载图片", "发送邮件", "生成报告", "备份数据", "清理缓存"]

    # 一个生产者 + 三个消费者并发
    await asyncio.gather(
        生产者(queue, 任务列表),
        消费者(queue, 1),
        消费者(queue, 2),
        消费者(queue, 3),
    )

print("生产者-消费者模式演示：")
asyncio.run(生产消费示例())
print("👉 这个模式是 Agent 并发处理多个工具调用的基础")
print()

print("=" * 60)
print("第 7 步：asyncio.timeout() —— 超时控制（AI Agent 必备）")
print("=" * 60)

async def 可能超时的API调用(api名称, 延时):
    await asyncio.sleep(延时)
    return f"{api名称} 返回数据"

async def 带超时的调用():
    print("  调用 API-1（1秒，正常）...")
    try:
        async with asyncio.timeout(3):
            结果 = await 可能超时的API调用("API-1", 1)
            print(f"  ✅ {结果}")
    except TimeoutError:
        print("  ❌ API-1 超时（3秒）")

    print("  调用 API-2（5秒，会超时）...")
    try:
        async with asyncio.timeout(2):
            结果 = await 可能超时的API调用("API-2", 5)
            print(f"  ✅ {结果}")
    except TimeoutError:
        print("  ❌ API-2 超时（2秒）")
    print("  👉 超时后程序继续运行，不会卡死")

asyncio.run(带超时的调用())
print()

print("=" * 60)
print("第 8 步：AI Agent 实战 —— 并发调用多个 LLM 工具")
print("=" * 60)
print("模拟 Agent 同时调用：计算器、查天气、搜文件、翻译")
print()

# 模拟 API 调用延迟
async def 调用LLM工具(工具名, 输入, 延迟=None):
    if 延迟 is None:
        延迟 = random.uniform(0.5, 2.0)
    await asyncio.sleep(延迟)
    return {
        "工具": 工具名,
        "输入": 输入,
        "耗时": f"{延迟:.2f}s",
        "结果": f"[{工具名}] 模拟结果：处理「{输入}」成功"
    }

async def Agent并发调用():
    """Agent 发现需要同时调用 4 个工具"""
    开始 = time.time()
    print("  Agent 思考：需要同时调用多个工具...")

    # 并发调用所有工具
    结果们 = await asyncio.gather(
        调用LLM工具("计算器", "3 + 5 * 2"),
        调用LLM工具("天气查询", "北京"),
        调用LLM工具("文件搜索", "config.py"),
        调用LLM工具("翻译", "Hello World → 中文"),
    )

    耗时 = time.time() - 开始
    print(f"\n  全部工具调用完成，总耗时：{耗时:.2f}秒\n")
    print("  📊 工具返回结果：")
    for r in 结果们:
        print(f"    🔧 {r['工具']}（{r['耗时']}）：{r['结果']}")
    print()
    print("  Agent思考：汇总结果后生成最终回复...")
    print(f"  👉 并发调用优势：4个工具只花了 {耗时:.2f}秒，逐个调用需要 4-8 秒")

asyncio.run(Agent并发调用())
print()

print("=" * 60)
print("第 9 步：异步上下文管理器（with 语句的异步版）")
print("=" * 60)

class 异步资源:
    """模拟需要异步打开/关闭的资源（如数据库连接）"""
    async def __aenter__(self):
        print("    正在连接数据库...")
        await asyncio.sleep(0.5)
        print("    数据库已连接")
        return self

    async def __aexit__(self, *args):
        print("    正在关闭数据库连接...")
        await asyncio.sleep(0.3)
        print("    数据库已关闭")

    async def 查询(self, sql):
        await asyncio.sleep(0.2)
        return f"执行 SQL：{sql} → 结果集"

async def 使用异步资源():
    async with 异步资源() as db:
        结果 = await db.查询("SELECT * FROM users")
        print(f"    {结果}")

print("异步上下文管理器演示：")
asyncio.run(使用异步资源())
print("👉 aiohttp、asyncpg 等库都基于这个机制")
print()

print("=" * 60)
print("总结：异步编程核心要点")
print("=" * 60)
print("""
1. async def 定义协程函数，await 等待异步操作（第1-2步）
2. asyncio.run() 启动事件循环，是入口（第2步）
3. asyncio.gather() 并发执行，等全部完成（第3步）
4. asyncio.create_task() 后台启动任务，灵活控制（第4步）
5. 永远不要在 async 里用 time.sleep()（第5步）
6. asyncio.Queue 实现生产者消费者（第6步）
7. asyncio.timeout() 超时控制，Agent 工具调用必备（第7步）
8. 并发工具调用是 Agent 性能关键（第8步）
9. async with 用于异步资源管理（第9步）

对比记忆：
  def    → async def    （定义）
  调用()  → await 调用()  （执行）
  with   → async with   （上下文）
  for    → async for    （迭代，后面会学）
  time.sleep() → await asyncio.sleep()  （等待，绝不混用！）
""")
