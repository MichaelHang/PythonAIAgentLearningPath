#!/usr/bin/env python
"""
学习页生成脚本：生成 day01~day10_lesson.html（每天"学什么、怎么学、怎么做"）

用途：修改本文件中的课程内容后运行 python generate_lessons.py 重新生成。
依赖：pip install pygments（复用 generate_html 提取的页面样式）
"""

import html as htmllib
import sys
from pathlib import Path

from generate_html import 根目录, 构造侧边栏, 提取样式


def esc(文本: str) -> str:
    return htmllib.escape(文本, quote=False)


def code(代码: str) -> str:
    return f'<pre class="code-block"><code>{esc(代码.strip(chr(10)))}</code></pre>'


def 表头列(列名列表, 行列表) -> str:
    thead = "".join(f"<th>{c}</th>" for c in 列名列表)
    trs = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in 行) + "</tr>" for 行 in 行列表
    )
    return (
        f'<table class="styled-table"><thead><tr>{thead}</tr></thead>'
        f"<tbody>{trs}</tbody></table>"
    )


def 链接列表(条目列表) -> str:
    lis = "".join(f"<li>{x}</li>" for x in 条目列表)
    return f"<ul>{lis}</ul>"


# 每天的"本日导航"条：学习页 / 模板 / 验收
def 本日导航(day: int, 有验收: bool) -> str:
    链接 = [f'📝 <a href="day{day:02d}_practice_template.html">练习模板</a>']
    if 有验收:
        链接.append(f'✅ <a href="day{day:02d}_practice_validator.html">验收脚本</a>')
    else:
        链接.append('📋 <a href="ACCEPTANCE_CRITERIA.html">手动验收清单</a>')
    return (
        '<div class="file-info"><div class="info-left">📚 本日资源：'
        + " ｜ ".join(链接)
        + "</div></div>"
    )


# ==================== 每天的课程内容 ====================

def day01() -> str:
    return f"""
<h1>Day 1：异步编程核心</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：今天结束时，你能写出"并发调用 5 个 API、总耗时只等于最慢那一个"的异步代码，
并理解为什么它是 Agent 并发调用工具的基石。</p>
</blockquote>
{本日导航(1, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["40min", "<strong>理论学习</strong>：本页「第一步」+ 跑一遍异步教程", "阅读 + 运行"],
["50min", "<strong>动手实操</strong>：完成练习模板中的 5 个任务", "编码"],
["30min", "<strong>验收巩固</strong>：跑验收脚本，按提示修到 80 分以上", "编码"],
])}

<h2>📖 第一步：理论学习（先看懂，再动手）</h2>

<h3>1. 同步 vs 异步：烧水做饭的比喻</h3>
<p>同步就是"一件做完才做下一件"；异步是"发起后先不等，谁先完成先处理谁"。
烧水要 3 秒、切菜要 2 秒：同步总共 5 秒，异步只需要 3 秒（等水开的同时把菜切了）：</p>
{code("""
import asyncio
import time

# 同步：一件一件来（总耗时 = 所有任务时间之和）
def 同步烧水():
    time.sleep(3)   # ❌ time.sleep 会阻塞整个程序，什么都干不了
    return "开水"

# 异步：等待时把 CPU 让给其他任务（总耗时 ≈ 最慢的那个任务）
async def 异步烧水():
    await asyncio.sleep(3)   # ✅ await 时其他任务可以运行
    return "开水"

async def 异步做饭():
    任务1 = asyncio.create_task(异步烧水())   # 立刻开始烧水
    任务2 = asyncio.create_task(异步切菜())   # 同时开始切菜
    水, 菜 = await 任务1, await 任务2         # 都完成后取结果
    return 水, 菜

# 结果：同步 5 秒，异步 3 秒！
""")}
<h3>2. 必须记住的 6 个 API</h3>
{表头列(["关键字", "作用", "示例"], [
["<code>async def</code>", "定义协程函数", "<code>async def 下载文件():</code>"],
["<code>await</code>", "等待异步操作（不阻塞其他任务）", "<code>result = await asyncio.sleep(1)</code>"],
["<code>asyncio.run()</code>", "启动事件循环（整个程序只调一次）", "<code>asyncio.run(main())</code>"],
["<code>asyncio.gather()</code>", "并发执行多个任务，等全部完成", "<code>await asyncio.gather(t1, t2)</code>"],
["<code>asyncio.create_task()</code>", "把协程包装成后台任务立刻调度", "<code>task = asyncio.create_task(下载())</code>"],
["<code>asyncio.timeout()</code>", "超时控制（Python 3.11+）", "<code>async with asyncio.timeout(5):</code>"],
])}
<h3>3. gather 和 create_task 的区别（面试常问）</h3>
<ul>
<li><code>gather(t1, t2)</code>：<strong>等着这批一起完成</strong>，按顺序返回结果列表 —— 适合"同时发 N 个请求然后汇总"。</li>
<li><code>create_task(协程)</code>：<strong>扔到后台立刻跑</strong>，返回 task 对象，你可以先干别的再 await 它 —— 适合"边等下载边响应用户"。</li>
</ul>
<h3>4. Agent 视角：为什么 Agent 离不开异步</h3>
<p>Agent 一次经常要并发调用多个工具（查天气 + 算数 + 搜文件）。逐个 await 是 4 倍耗时，gather 只要最长的那个：</p>
{code("""
async def Agent并发调用():
    结果们 = await asyncio.gather(
        调用工具("计算器", "3 + 5 * 2"),
        调用工具("天气查询", "北京"),
        调用工具("文件搜索", "config.py"),
        调用工具("翻译", "Hello World"),
    )   # 4 个工具只花了最长的那个的时间（不是 4 倍！）
""")}
<h2>🛠 第二步：动手实操（核心环节）</h2>
<ol>
<li><strong>跑教程</strong>：运行 <code>python tutorial_02_async.py</code>，跟着 9 步输出逐步理解（第 5 步故意演示 time.sleep 陷阱，别跳过）。</li>
<li><strong>打开模板</strong>：<a href="day01_practice_template.html">day01_practice_template.py</a>，共 5 个 TODO，函数体全部留空等你实现：</li>
</ol>
{表头列(["任务", "要做什么", "提示"], [
["任务 1", "实现 <code>异步请求(url)</code>", "<code>await asyncio.sleep(延迟秒)</code> 后返回含 url/status/data 的字典"],
["任务 2", "实现 <code>并发请求(urls)</code>", "用 <code>asyncio.gather(*tasks)</code>，不要在循环里逐个 await"],
["任务 3", "实现 <code>同步请求</code> 和 <code>性能对比</code>", "同步用 <code>time.sleep(1)</code>（故意慢），对比后断言异步快一倍以上"],
["任务 4", "实现 <code>异步请求带重试</code>", "for 循环 + try/except + <code>random.random() &lt; 0.3</code> 模拟失败"],
])}
<ol start="3">
<li><strong>运行自测</strong>：<code>python day01_practice_template.py</code>，确认 4 个任务都打印出结果。</li>
<li><strong>验收</strong>：运行 <code>python day01_practice_validator.py</code>。验收脚本会真的计时你的并发实现——逐个 await 的伪并发会被抓出来，80 分以上才算通过。</li>
</ol>
<h2>⚠️ 避坑（今天就会遇到的）</h2>
{链接列表([
"❌ 在 async 函数里用 <code>time.sleep()</code> —— 整个事件循环被卡死，并发变串行；永远用 <code>await asyncio.sleep()</code>",
"❌ <code>asyncio.run()</code> 在一个程序里调用多次或嵌套调用 —— 它只能由主线程调用一次",
"✅ 批量并发优先用 <code>asyncio.gather()</code>，而不是先 await 一个再 await 下一个",
"💡 验收提示里的 <code>random.random()</code> 需要 <code>import random</code>——模板已帮你加好",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://realpython.com/async-io-python/">Real Python: Async IO in Python</a>（最经典的入门长文）',
'<a href="https://docs.python.org/3/library/asyncio.html">Python 官方 asyncio 文档</a>',
])}
"""


def day02() -> str:
    return f"""
<h1>Day 2：类型系统与装饰器进阶</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：能用 Pydantic v2 定义"Agent 工具的输入/输出 Schema"，并写一个带参数的装饰器把任意函数自动注册为 Agent 工具——这是后面所有天的工具系统底座。</p>
</blockquote>
{本日导航(2, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["30min", "<strong>理论学习</strong>：Pydantic 数据验证 + 装饰器三层嵌套", "阅读"],
["30min", "<strong>跑教程</strong>：装饰器 8 步教程", "运行 + 修改"],
["60min", "<strong>动手实操</strong>：完成练习模板 13 个 TODO", "编码"],
])}

<h2>📖 第一步：理论学习</h2>

<h3>1. 为什么 Agent 需要数据验证</h3>
<p>LLM 返回的内容<strong>不可信</strong>：你要它给数字，它可能给字符串；你要它给城市名，它可能幻觉出不存在的东西。
Pydantic 的作用：定义好"数据长什么样"，不符合就当场报错，而不是让错误数据流进你的工具。</p>
{code("""
from pydantic import BaseModel, Field, ValidationError

class 计算器输入(BaseModel):
    表达式: str = Field(..., description="四则运算表达式")

# ✅ 合法输入：通过
参数 = 计算器输入(表达式="3 + 5 * 2")

# ❌ 非法输入：当场拦截（表达式应为 str，传了 int）
try:
    计算器输入(表达式=12345)
except ValidationError as e:
    print("拦截成功:", e.errors()[0]["msg"])

# 生成 JSON Schema（给 LLM 看的参数说明就靠它）
print(计算器输入.model_json_schema())
""")}
<p>注意：<strong>Pydantic 只做类型校验，不做安全过滤</strong>。"import os; os.system(...)" 是合法的 str，类型校验拦不住它——
拦截危险内容要在工具内部自己做（白名单、沙箱）。两层防护缺一不可。</p>

<h3>2. dataclass vs Pydantic（怎么选）</h3>
{表头列(["", "dataclass", "Pydantic v2"], [
["用途", "纯内存数据结构", "需要校验/序列化的边界数据（API 输入输出、LLM 返回）"],
["校验", "无", "自动类型转换 + 校验 + 报错"],
["性能", "快", "v2 用 Rust 核心，也很快"],
["Agent 中", "内部状态（如 AgentStep）", "工具 Schema、消息模型、配置"],
])}

<h3>3. 装饰器：三步从入门到工具注册</h3>
<p><strong>本质</strong>：装饰器 = 接受一个函数，返回一个新函数（给手机套壳，壳能在原功能外加点行为）。</p>
{code("""
import functools

def 计时装饰器(原函数):
    @functools.wraps(原函数)      # ✅ 必须加！保留原函数的 __name__/__doc__
    def 包装函数(*args, **kwargs):
        开始 = time.time()
        结果 = 原函数(*args, **kwargs)
        print(f"⏱ {原函数.__name__} 耗时 {time.time()-开始:.4f}s")
        return 结果
    return 包装函数

@计时装饰器
def 慢速加法(a, b):
    time.sleep(1)
    return a + b

慢速加法(3, 5)   # 自动打印耗时
""")}
<p><strong>致命陷阱</strong>：不加 <code>@functools.wraps</code>，被装饰函数的 <code>__name__</code> 会变成"包装"，
<code>__doc__</code> 变 None——Agent 靠函数名和 docstring 选工具，丢了就全乱。</p>
<p><strong>带参数的装饰器 = 三层嵌套</strong>（多包一层"参数层"）：</p>
{code("""
def 重试(最大次数=3):                 # 第 1 层：收参数
    def 装饰器(原函数):               # 第 2 层：收函数
        @functools.wraps(原函数)
        def 包装(*args, **kwargs):   # 第 3 层：真正执行
            for i in range(最大次数):
                try:
                    return 原函数(*args, **kwargs)
                except Exception as e:
                    if i == 最大次数 - 1:
                        raise
                    time.sleep(0.5)
        return 包装
    return 装饰器

@重试(最大次数=3)
def 不稳定的网络请求(): ...
""")}
<p><strong>Agent 实战：工具注册装饰器</strong>（今天练习的核心模式，LangChain 的 @tool 就是它）：</p>
{code("""
工具注册表 = {}

def 工具(名称, 描述):
    def 装饰器(func):
        @functools.wraps(func)
        def 包装(*args, **kwargs):
            return func(*args, **kwargs)
        工具注册表[名称] = {"函数": 包装, "描述": 描述}
        return 包装
    return 装饰器

@工具("计算器", "执行四则运算")
def 计算(表达式): return eval(表达式)

# 之后 Agent 只需遍历 工具注册表 就知道"我有哪些工具可用"
""")}
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>跑教程</strong>：<code>python tutorial_01_decorators.py</code>，8 步从"一等公民"到"类装饰器"。</li>
<li><strong>打开模板</strong>：<a href="day02_practice_template.html">day02_practice_template.py</a>，13 个 TODO 分四组：
  <ul>
  <li>TODO 1.2-1.3：为天气查询、文件搜索定义输入/输出 Schema（照抄计算器的写法）</li>
  <li>TODO 2.1-2.5：实现装饰器三层嵌套（输入验证 → 调用原函数 → 输出验证 → 注册进注册表）</li>
  <li>TODO 3.2-3.3：用 @工具 注册至少 3 个工具</li>
  <li>TODO 4.1-4.2：<code>调用工具</code>（查注册表并调用）和 <code>列出所有工具</code>（转成 OpenAI Function Calling 格式，用 <code>model_json_schema()</code>）</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day02_practice_template.py</code>，4 个测试全部 ✅（测试 2 应显示拦截了类型错误）。</li>
<li><strong>验收</strong>：<code>python day02_practice_validator.py</code>（需要 <code>pip install pydantic</code>）。验收会真的调用你注册的计算器、传错误类型试探你的验证逻辑、检查 OpenAI 格式。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ Pydantic v1 和 v2 API 不兼容（<code>.schema()</code> 已改名 <code>model_json_schema()</code>），确认装的是 v2",
"❌ 忘写 <code>@functools.wraps(func)</code> —— 验收脚本会专门检查这一点",
"✅ 类型注解本身不做运行时检查，Pydantic 模型才做；两者配合使用",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://docs.pydantic.dev/latest/">Pydantic V2 官方文档</a>',
'<a href="https://mypy.readthedocs.io/">mypy 官方文档</a>（静态类型检查）',
])}
"""


def day03() -> str:
    return f"""
<h1>Day 3：生成器、异步生成器与上下文管理器</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：实现一个"逐字吐出回复"的流式 LLM 客户端。你平时看到的 ChatGPT 打字机效果、
Agent 流式输出，底层就是一个异步生成器。</p>
</blockquote>
{本日导航(3, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["30min", "<strong>理论学习</strong>：yield 的暂停/恢复机制 + 上下文管理器", "阅读"],
["30min", "<strong>编码理解</strong>：同步/异步生成器各写一遍", "编码"],
["60min", "<strong>动手实操</strong>：完成练习模板 11 个 TODO", "编码"],
])}

<h2>📖 第一步：理论学习</h2>

<h3>1. 生成器：能暂停的函数</h3>
<p>普通函数 return 后就结束了；带 <code>yield</code> 的函数每次吐出一个值就<strong>暂停</strong>，
下次迭代从暂停处继续。好处：不一次性把所有数据放进内存，要多少吐多少。</p>
{code("""
def 计数器(上限):
    n = 0
    while n < 上限:
        yield n      # 吐出 n 并暂停，下次从这里继续
        n += 1

for i in 计数器(3):   # 0 1 2 —— 一次只存在一个值
    print(i)
""")}
<p>两个关键性质：<strong>① 只能遍历一次</strong>（ exhausted 就没了，需要重复用就转 <code>list()</code>）；
<strong>② 惰性求值</strong>（没人要就不计算——处理大文件/长流式响应不爆内存的根本原因）。</p>

<h3>2. 异步生成器 = async def + yield（LLM 流式输出的原理）</h3>
<p>LLM API 是一个 token 一个 token 返回的。客户端用异步生成器逐块接收，界面就能打字机式刷新：</p>
{code("""
import asyncio
from typing import AsyncGenerator

async def 流式响应(提示词: str) -> AsyncGenerator[str, None]:
    # 注意：async def 里必须有 yield，才是"异步生成器"
    for chunk in [提示词[:i+1] for i in range(len(提示词))]:
        await asyncio.sleep(0.1)   # 模拟网络到达一个 chunk
        yield chunk

async def main():
    async for chunk in 流式响应("你好世界"):   # 用 async for 消费
        print(chunk, end="", flush=True)
""")}
<p class="note-block">⚠️ 高频错误：<code>async def</code> 函数体里<strong>没有 yield</strong>，它就不是异步生成器，
而是普通协程——用 <code>async for</code> 迭代它会直接 TypeError。练习模板里特意留了这个坑给你踩。</p>

<h3>3. 上下文管理器：自动收尾的资源管家</h3>
<p><code>with</code> 语句的底层。四种写法按需选择：</p>
{code("""
from contextlib import contextmanager, asynccontextmanager
import time

# 写法 1：类实现（最完整，能保存状态）
class 计时器:
    def __enter__(self):
        self.开始 = time.time()
        return self                      # 约定：返回 self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"耗时 {time.time()-self.开始:.3f}s")
        return False                     # False = 异常继续往外抛

# 写法 2：@contextmanager（简单的场景两行搞定）
@contextmanager
def 计时器简版(名称):
    开始 = time.time()
    yield                                # ← yield 前是 __enter__，后是 __exit__
    print(f"{名称} 耗时 {time.time()-开始:.3f}s")

with 计时器简版("查询"):        # 用法和写法 1 完全一样
    time.sleep(0.5)

# 异步版：__aenter__/__aexit__ 或 @asynccontextmanager（把 time.sleep 换成 await asyncio.sleep）
""")}
<h3>4. 组合技：今天的终极目标</h3>
<p>把「异步生成器（流式）」+「异步上下文管理器（自动计时）」组合成一个
<code>流式LLM客户端</code>——<code>async with</code> 计时，<code>async for</code> 逐块 yield。这就是 Day 5/10 里 Agent 流式输出的雏形。</p>
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day03_practice_template.html">day03_practice_template.py</a>，11 个 TODO：
  <ul>
  <li>任务 1/2：同步、异步流式生成器（照本页示例写，注意异步版函数体里必须有 yield）</li>
  <li>任务 3/4：四种上下文管理器（类版 <code>__enter__</code> 要 return self）</li>
  <li>任务 5：<code>流式LLM客户端.chat()</code> —— 签名已经是 <code>async def</code>，你要在方法体里加 yield 并用 <code>async with</code> 包计时器</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day03_practice_template.py</code>，能看到逐块打字机输出。</li>
<li><strong>验收</strong>：<code>python day03_practice_validator.py</code> —— 验收会真的迭代你的生成器数 chunk 数、
真的进入你的 with 块检查 <code>__enter__</code> 是否返回 self。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 生成器只能遍历一次，第二次遍历是空的；要重复使用先转 list",
"❌ <code>async def</code> 忘写 yield → 不是异步生成器，<code>async for</code> 报 TypeError",
"❌ @contextmanager 版本忘写 yield → <code>RuntimeError: generator didn't yield</code>",
"✅ 大文件/流式数据必须用生成器，一次性读进内存会爆",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://realpython.com/introduction-to-python-generators/">Real Python: Generators</a>',
'<a href="https://docs.python.org/3/library/itertools.html">itertools 官方文档</a>（生成器工具箱）',
])}
"""


def day04() -> str:
    return f"""
<h1>Day 4：LLM API 调用与 Function Calling</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：跑通 Function Calling 完整闭环——让 LLM 自己决定调用哪个 Python 函数、
你执行它、把结果喂回去、LLM 给出最终回答。这是"Agent 会用工具"的本质，今天用 mock 就能练，不需要 API Key。</p>
</blockquote>
{本日导航(4, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["30min", "<strong>理论学习</strong>：API 结构 + Function Calling 时序", "阅读"],
["40min", "<strong>Prompt 实验</strong>：System Prompt / Few-shot / ReAct 格式", "编码实验"],
["50min", "<strong>动手实操</strong>：完成练习模板 7 个 TODO", "编码"],
])}

<h2>📖 第一步：理论学习</h2>

<h3>1. OpenAI 兼容 API 的请求结构</h3>
<p>DeepSeek / Qwen / Moonshot 都兼容这套格式。一次对话 = POST 一个 JSON：</p>
{code("""
POST https://api.deepseek.com/chat/completions
Authorization: Bearer 你的KEY

{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system",    "content": "你是一个有用的助手"},   # 设定人设，放最前
    {"role": "user",      "content": "北京今天天气怎么样？"},
    {"role": "assistant", "content": null,
      "tool_calls": [ ... ]},                                # LLM 请求调工具
    {"role": "tool",      "content": "晴 25°C", "tool_call_id": "call_001"}  # 工具结果回传
  ],
  "tools": [ ... ]     # 告诉 LLM 有哪些工具可用
}
""")}
<h3>2. tools 参数：给 LLM 的"工具说明书"</h3>
{code("""
[
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "获取指定城市的天气信息",     # ← LLM 靠这句话决定选不选这个工具！
      "parameters": {                            # ← JSON Schema，Day 2 的 Pydantic 可以自动生成
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名称"}},
        "required": ["city"]
      }
    }
  }
]
""")}
<h3>3. Function Calling 完整时序（今天的核心）</h3>
{code("""
用户提问
   │
   ▼
① 带 tools 调 LLM ──────────────► LLM 不直接回答，返回 tool_calls：
   │                                {"name": "get_weather", "arguments": '{"city":"北京"}'}
   ▼                                 注意：arguments 是 JSON 字符串，要 json.loads！
② 你解析并执行真正的 Python 函数，得到结果 "晴 25°C"
   │
   ▼
③ 把结果作为 role="tool" 消息追加进 messages（带上 tool_call_id）
   │
   ▼
④ 再次调用 LLM ─────────────────► LLM 综合工具结果，给出最终回答
   │
   ▼
⑤ 循环：如果第 ④ 步又返回 tool_calls，回到 ②，直到给出最终回答
   （所以必须有 max_rounds 上限，防止无限烧钱）
""")}
<h3>4. Prompt 工程三原则（今天顺手练）</h3>
{表头列(["原则", "做法"], [
["System Prompt 精简", "只放人设 + 工具使用规则；太长 LLM 会忽略后面的"],
["Few-shot", "在 prompt 里给 1-2 个输入→输出示例，格式遵循度大幅提升"],
["格式约束", "让 LLM 按固定格式输出（如 ReAct 的 Thought/Action），后面才好解析"],
])}
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day04_practice_template.html">day04_practice_template.py</a>。两个工具已注册好，
mock LLM 也写好了（不需要 Key），你实现 4 个核心函数：
  <ul>
  <li>TODO 1.2：<code>get_tools_for_api()</code> —— 把注册表转成上面的 tools 格式</li>
  <li>TODO 3.1：<code>parse_tool_calls()</code> —— 从响应里取 tool_calls，<code>json.loads</code> 解析 arguments</li>
  <li>TODO 3.2：<code>execute_tool_call()</code> —— 查注册表、执行、返回结果</li>
  <li>TODO 4.1：<code>chat_with_function_calling()</code> —— 按上面的 ①→⑤ 时序写主循环（最有价值的一题）</li>
  <li>TODO 5.1（可选）：有 DeepSeek Key 的话把 mock 换成真实 API</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day04_practice_template.py</code>，两个问题都应打出最终回答。</li>
<li><strong>验收</strong>：<code>python day04_practice_validator.py</code> —— 验收用构造好的 LLM 响应直接喂你的解析函数，
并跑通你的完整闭环。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ <code>arguments</code> 是 JSON <strong>字符串</strong>不是字典——忘 json.loads 是新手第一坑",
"❌ 工具结果忘以 <code>role=\"tool\"</code> 回传 → LLM 不知道工具说了什么，永远循环",
"❌ 主循环没有轮数上限 → LLM 反复要求调工具，token 烧个不停",
"✅ 真实 API 的 JSON 可能格式错误：json.loads 必须套 try/except + 重试",
"✅ 国内直连用 DeepSeek / Qwen / Moonshot，都有免费额度",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://platform.openai.com/docs/guides/function-calling">OpenAI Function Calling 指南</a>',
'<a href="https://api-docs.deepseek.com/">DeepSeek API 文档</a>（免费额度）',
'<a href="https://www.promptingguide.ai/zh">Prompt Engineering Guide（中文）</a>',
])}
"""


def day05() -> str:
    return f"""
<h1>Day 5：阶段一综合实战——命令行 AI 助手</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：把 Day 2-4 的三块积木（Pydantic 模型、工具注册、流式输出 + Function Calling）
拼装成一个完整程序。今天几乎没有新知识，考的是<strong>组装能力</strong>——这正是"能跑 demo"和"能写项目"的分水岭。</p>
</blockquote>
{本日导航(5, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["15min", "<strong>架构梳理</strong>：看懂组件关系图", "阅读"],
["90min", "<strong>动手实操</strong>：完成 7 个 TODO，拼出完整 Agent", "编码"],
["15min", "<strong>验收 + 交互测试</strong>：跑验收脚本，玩一下自己的 CLI", "验收"],
])}

<h2>📖 第一步：看懂架构（今天的"理论"就这一张图）</h2>
{code("""
┌─────────────────────────── CLI_Agent ───────────────────────────┐
│                                                                  │
│  messages: List[ChatMessage]   ← 全部状态都在这（Pydantic 模型）  │
│                                                                  │
│  chat(user_input):                                               │
│    1. messages.append(user 消息)                                 │
│    2. for round in range(max_tool_rounds):        ← 有上限！     │
│         async for chunk in client.chat(messages, tools):         │
│              │                        ← StreamingLLMClient      │
│              ├─ chunk 是 [TOOL_CALL] 标记？                       │
│              │     └─ 解析 → execute_tool() → 追加 tool 消息     │
│              └─ 普通文本 → 累积 + （可选）实时打印                │
│         有工具调用 → continue 下一轮（LLM 会引用工具结果）        │
│         没有工具调用 → return 最终回答                            │
└──────────────────────────────────────────────────────────────────┘
""")}
<p>数据流向：<strong>用户输入 → LLM（流式）→ [TOOL_CALL] → 执行工具 → tool 消息回传 → LLM 再流式 → 最终回答</strong>。
今天 mock 的流式客户端会在第一轮流式输出文字 + 一个 <code>[TOOL_CALL] 工具名: {{参数JSON}}</code> 标记，
在第二轮（messages 里已有 tool 消息时）输出引用工具结果的最终回答——你的主循环要正确处理这两个阶段。</p>
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day05_practice_template.html">day05_practice_template.py</a>，7 个 TODO：
  <ul>
  <li>TODO 1.1：可以补充 ToolResult 等 Pydantic 模型（Day 2 功底）</li>
  <li>TODO 2.2：<code>get_tools_for_api()</code>（Day 4 原题）</li>
  <li>TODO 2.3：<code>execute_tool()</code>（Day 4 原题）</li>
  <li>TODO 3.1：<code>StreamingLLMClient.chat()</code> 改造成异步生成器（Day 3 功底：async def + yield）</li>
  <li>TODO 4.1：<code>CLI_Agent.chat()</code> 主循环（核心，按架构图写）</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day05_practice_template.py</code>，3 个测试应看到流式输出和工具调用链。</li>
<li><strong>玩自己的 Agent</strong>：把文件末尾 <code>asyncio.run(run_cli())</code> 的注释打开，和它对话：
  输入"帮我计算 3 + 5 * 2"、"北京天气"、"你好"（不走工具）、"clear"（清历史）、"exit"。</li>
<li><strong>验收</strong>：<code>python day05_practice_validator.py</code> —— 验收会构建你的 Agent 发起真实对话，
检查回答里是否包含工具算出的 <strong>13</strong>（工具没真的执行是混不过去的），并检查 messages 里有没有 role=tool 的回传消息。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 解析 <code>[TOOL_CALL]</code> 后忘记把工具结果追加成 <code>role=tool</code> 消息 → 下一轮 LLM 拿不到结果",
"❌ 主循环没有轮数上限 / 没有终止条件 → 验收直接超时判 0 分",
"❌ 在 async 循环里直接用 <code>input()</code> 阻塞事件循环（模板 run_cli 已示范 <code>asyncio.to_thread</code> 的正确写法）",
"✅ stream=False 时不要打印 chunk，返回完整字符串——验收就是这么调你的",
])}
<h2>✅ 阶段一结业标准</h2>
<p>完成今天后你应该能不查资料手写：Pydantic Schema、工具注册装饰器、异步生成器、Function Calling 主循环。
明天开始进入真正的 Agent 架构。</p>
"""


def day06() -> str:
    return f"""
<h1>Day 6：Agent 架构原理——纯 Python 手写 ReAct</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：不依赖任何框架，手写一个 ReAct Agent 循环。写完你会发现：
LangChain/AutoGen 这些框架的核心，就是一个几十行的循环 + 一段格式约定。</p>
</blockquote>
{本日导航(6, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["60min", "<strong>理论学习</strong>：Agent 四大模块 + ReAct 循环", "阅读 + 手推"],
["60min", "<strong>动手实操</strong>：完成 5 个任务，跑通 ReAct", "编码"],
])}

<h2>📖 第一步：理论学习</h2>

<h3>1. Agent 到底是什么（四大模块）</h3>
{表头列(["模块", "职责", "本项目对应"], [
["规划 Planning", "把目标拆成步骤，决定下一步做什么", "ReAct 循环里的 Thought"],
["记忆 Memory", "记住对话历史和长期知识", "Day 9 实现"],
["工具 Tools", "调用计算器/搜索/文件等扩展能力", "TOOLS_REGISTRY"],
["执行 Action", "真正去做（调 API、执行代码）", "execute_tool"],
])}
<p>LLM 本身只会生成文本。Agent = <strong>LLM + 循环 + 工具</strong>：让 LLM 的"文本输出"能触发真实的函数执行，再把执行结果喂回去。</p>

<h3>2. ReAct：Reasoning + Acting 交替</h3>
<p>核心格式约定——LLM 按这个格式输出，你的程序按这个格式解析：</p>
{code("""
Thought: 我需要先算出 3 + 5 * 2 的结果        ← LLM 推理"下一步干什么"
Action: Calculator                            ← 选择哪个工具
Action Input: 3 + 5 * 2                       ← 工具参数
Observation: 13                               ← 【你的程序】执行工具后填回去
Thought: 我已经拿到结果了
Final Answer: 3 + 5 * 2 = 13                  ← 循环出口
""")}
<p>一轮完整流程：<strong>构建 prompt（含工具清单 + 历史步骤）→ LLM 输出 → 解析 →
是 Final Answer 就结束，否则执行工具 → 把 Action/Observation 追加进历史 → 再来一轮</strong>。</p>

<h3>3. 手写循环（伪代码，练习就照这个骨架写）</h3>
{code("""
async def react_agent(user_input, tools, max_steps=10):
    steps = []
    for step in range(max_steps):            # ← 必须有上限，防死循环
        prompt = build_prompt(user_input, steps)   # 工具清单 + 历史 Thought/Action/Observation
        response = await llm_call(prompt)
        thought, action, action_input = parse(response)

        if action 为空:                      # LLM 给了 Final Answer
            return action_input              # ← 循环唯一正常出口

        result = execute_tool(action, action_input)
        steps.append(AgentStep(thought, action, action_input, observation=result))

    return "达到最大步数限制"                 # 防御性兜底
""")}
<p>模板内置的 mock LLM 规则：<strong>prompt 里最后一个 Action 后面还没有 Observation → 返回工具调用；
已经有了 → 返回 Final Answer（引用工具结果）</strong>。所以只要你的循环正确把历史拼进 prompt，
第 2 轮就会拿到最终答案。</p>
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day06_practice_template.html">day06_practice_template.py</a>，5 个任务：
  <ul>
  <li>TODO 1.2：<code>get_tools_description()</code> —— 生成放进 prompt 的工具清单</li>
  <li>TODO 1.3：<code>execute_tool()</code> —— 返回 ToolResult（成功/失败都要兜住）</li>
  <li>TODO 2.1：<code>build_react_prompt()</code> —— 系统说明 + 工具清单 + 历史 steps + Question</li>
  <li>TODO 3.1：<code>parse_react_response()</code> —— 正则提取 Thought/Action/Action Input；有 Final Answer 时 action 返回空串、答案放 action_input</li>
  <li>TODO 4.1：<code>react_agent()</code> 主循环（按伪代码骨架写）</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day06_practice_template.py</code>，两个测试都应打出最终回答而不是"达到最大步数"。</li>
<li><strong>验收</strong>：<code>python day06_practice_validator.py</code> —— 验收会真跑你的 Agent：计算题答案里必须有 13、
天气题必须有查询结果，Agent 卡死循环会被直接判负。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 不设 <code>max_steps</code> → LLM 反复要求调工具，无限循环烧钱",
"❌ 历史步骤（Action/Observation）不拼回 prompt → LLM 看不到自己做过什么，永远重复第一步",
"❌ 只解析成功路径 → 工具报错时 Agent 崩溃；把错误信息作为 Observation 喂回去，LLM 会自我纠正",
"✅ 每步记录 token 消耗（Day 10 会做），成本要可见",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://arxiv.org/abs/2210.03629">ReAct 原始论文</a>',
'<a href="https://lilianweng.github.io/posts/2023-06-23-agent/">Lilian Weng: LLM Powered Autonomous Agents</a>（Agent 领域总纲）',
])}
"""


def day07() -> str:
    return f"""
<h1>Day 7：LangGraph 入门——把 ReAct 循环装进"图"里</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：理解为什么生产级 Agent 都用"图"来组织：状态显式、路由可控、可持久化。
用 LangGraph 的 StateGraph 重写 Day 6 的 Agent（没装库也有模拟器先跑通逻辑）。</p>
</blockquote>
{本日导航(7, True)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["40min", "<strong>理论学习</strong>：图的核心概念 + 与手写循环的对应", "阅读"],
["50min", "<strong>动手实操</strong>：State / Nodes / Router / run_agent", "编码"],
["30min", "<strong>升级真实库</strong>：装 langgraph 重写 build_agent_graph", "编码"],
])}

<h2>📖 第一步：理论学习</h2>

<h3>1. 为什么 Day 6 的 while 循环不够用</h3>
<p>手写循环 hardcode 了"调 LLM → 执行工具"这一种流转。真实 Agent 需要：
多 Agent 切换、人工审批节点、失败重试分支、断点恢复……全塞进 for 循环就是面条地狱。
<strong>图（Graph）</strong>把"有哪些步骤"和"步骤间怎么流转"显式声明出来，框架负责执行流转。</p>

<h3>2. LangGraph 四个核心概念</h3>
{表头列(["概念", "是什么", "对应 Day 6 的"], [
["State（状态）", "一个 TypedDict，所有节点共享读写", "你手写的 steps 列表 + messages"],
["Node（节点）", "一个函数：读 state → 干活 → 返回 state 更新", "react_agent 循环体里的一段"],
["Edge（边）", "固定流转：A 完了必到 B", "循环体里的先后顺序"],
["Conditional Edge（条件边）", "路由函数决定下一步去哪", "if 有 tool_calls: 执行工具 else: 结束"],
])}
{code("""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

class AgentState(TypedDict):        # ① 状态
    messages: List[Dict]
    step_count: int

def node_call_model(state):         # ② 节点：调 LLM
    response = mock_llm_response(state["messages"])
    return {"messages": state["messages"] + [response],
             "step_count": state["step_count"] + 1}

def node_call_tool(state):          # ② 节点：执行工具
    ...把每个 tool_call 的结果以 role=tool 追加进 messages...

def router(state):                  # ③ 路由函数
    if state["messages"][-1].get("tool_calls"):
        return "call_tool"          # 还有工具要执行
    return "end"                    # 没有了 → 结束

graph = StateGraph(AgentState)      # ④ 组装
graph.add_node("call_model", node_call_model)
graph.add_node("call_tool", node_call_tool)
graph.set_entry_point("call_model")
graph.add_conditional_edges("call_model", router,
    {"call_tool": "call_tool", "end": END})
graph.add_edge("call_tool", "call_model")   # 执行完工具 → 回到模型
app = graph.compile()
""")}
<h3>3. 手写循环 vs 图（一一对应，帮助理解）</h3>
{code("""
Day 6:  for step in range(max_steps):      Day 7:  图的自动流转
        prompt = build(...)                        node_call_model
        response = llm(prompt)                       │
        if 有 tool_calls:                    router ─┤ call_tool → 回 call_model
            execute + 回传                           └ end → END
        else: return 最终回答
""")}
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>先跑模拟器</strong>：模板内置 <code>simulate_langgraph_loop()</code>，不需要装库。
完成 TODO 让它正确执行工具并给出最终回答。</li>
<li><strong>打开模板</strong>：<a href="day07_practice_template.html">day07_practice_template.py</a>：
  <ul>
  <li>TODO 1.1：AgentState 加 messages / step_count 字段</li>
  <li>TODO 2.2 / 2.3：工具列表转换 + 执行（Day 4 原题）</li>
  <li>TODO 4.1 / 4.2：<code>node_call_model</code> / <code>node_call_tool</code>（读 state → 返回更新）</li>
  <li>TODO 5.1：<code>router_should_continue</code>（有 tool_calls → "call_tool"，否则 "end"）</li>
  <li>TODO 7.1：<code>run_agent()</code> —— 装了 langgraph 就 graph.invoke(state)，没装降级调模拟器</li>
  </ul></li>
<li><strong>升级真实库</strong>（推荐）：<code>pip install langgraph</code>，把 <code>build_agent_graph()</code> 里的注释展开成真实实现——
组件函数你都已经写好，组装只需 8 行。</li>
<li><strong>验收</strong>：<code>python day07_practice_validator.py</code> —— 验收会构造 state 逐个调用你的节点函数、
试探你的路由、并端到端跑一遍（回答里必须真的包含工具结果）。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ LangChain 系版本更新快（0.1→0.2→0.3），看文档先对版本；本练习核心是图思想，API 细节随时查",
"❌ 节点函数直接改传入的 state（原地修改）—— 正确姿势是<strong>返回更新字段</strong>，由框架合并",
"❌ 路由返回值和 add_conditional_edges 的映射表对不上 → 图编译完一跑就报错",
"✅ 先用 mock/模拟器把流转跑对，再换真实 LLM——排查问题时能省一半时间",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://langchain-ai.github.io/langgraph/tutorials/">LangGraph 官方教程</a>',
'<a href="https://python.langchain.com/docs/">LangChain 文档</a>',
])}
"""


def day08() -> str:
    return f"""
<h1>Day 8：工具系统设计与 MCP 协议</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：掌握"好工具"的设计标准，理解 MCP（Model Context Protocol）——
让 Agent 和工具之间有了 USB 接口式的行业标准。用 Mock Server 完整走一遍 MCP 的工具发现与调用流程。</p>
</blockquote>
{本日导航(8, False)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["30min", "<strong>理论学习</strong>：工具设计四原则 + MCP 架构", "阅读"],
["40min", "<strong>MCP 原理</strong>：协议流程 + SDK 对照", "阅读"],
["50min", "<strong>动手实操</strong>：MockMCPServer + 客户端 + Agent 集成", "编码"],
])}

<h2>📖 第一步：好工具的四条标准</h2>
{表头列(["原则", "为什么", "怎么做"], [
["单一职责", "一个工具干一件事，LLM 选择正确率高", "read_file 和 write_file 分开，不要一个 file_ops"],
["描述精确", "docstring/description 直接决定 LLM 选不选它", "写清做什么、参数含义、给个例子"],
["有超时", "一个工具卡死会拖死整个 Agent", "所有工具包 <code>asyncio.wait_for(..., 30)</code>"],
["结构化返回", "LLM 要能读懂结果并继续推理", "返回 JSON/明确文本；出错时返回可读的错误信息而非 traceback"],
])}
<h2>📖 第二步：MCP 是什么</h2>
<p>没有 MCP 的世界：M 个 Agent × N 个工具 = M×N 套私有对接代码。MCP 把它变成 <strong>M+N</strong>：
工具方实现一次 MCP Server，任何支持 MCP 的 Agent（Claude Desktop、Cursor、你的 Agent）都能即插即用。</p>
{code("""
┌──────────────┐   stdio / HTTP    ┌──────────────────┐
│  MCP Host     │                  │  MCP Server       │
│ (你的 Agent)  │ ◄──────────────► │ (文件/计算/搜索…) │
│  MCP Client   │   JSON-RPC 2.0   │  tools + 资源     │
└──────────────┘                  └──────────────────┘

一次完整会话：
① initialize          客户端连接服务器，协商能力
② tools/list          发现：服务器上报"我有哪些工具、参数 Schema 是什么"
③ tools/call          调用：客户端发 name + arguments，服务器执行并返回结果
""")}
<p>对应到本练习：<code>MCPClient.list_tools()</code> 就是 ②，<code>MCPClient.call_tool()</code> 就是 ③，
<code>MockMCPServer</code> 用装饰器注册工具（和 Day 2 的模式一模一样，只是"注册"从进程内字典变成了可发现的协议接口）。
模板注释里附了 <code>mcp</code> 官方 SDK 的等价写法，跑通 mock 后对照看一眼即可。</p>
<h2>🛠 第三步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day08_practice_template.html">day08_practice_template.py</a>：
  <ul>
  <li>TODO 2.1：<code>get_tool_list()</code> —— 把注册的工具转成 Function Calling 格式（含超时包装）</li>
  <li>TODO 2.2：<code>call_tool()</code> —— 查表、调用、错误兜底</li>
  <li>TODO 3.1-3.3：<code>MCPClient</code> 的 connect / list_tools / call_tool</li>
  <li>TODO 4.1-4.2：<code>agent_with_mcp()</code> —— 获取工具列表 → 走一遍简化 ReAct（Day 6 功底）</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day08_practice_template.py</code>（TODO 未完成时会有友好提示，不会裸崩）。</li>
<li><strong>验收</strong>：本天没有自动脚本，按 <a href="ACCEPTANCE_CRITERIA.html">验收标准文档</a> Day 8 清单逐项自查：
工具描述清晰吗？超时控制在哪？错误返回的是可读信息还是 traceback？</li>
<li><strong>进阶（可选）</strong>：<code>pip install mcp</code>，用官方 SDK 把 calculator + read_note 实现成真 MCP Server，
用 <code>mcp dev</code> 起服务后接进 Claude Desktop / Cursor 玩一圈。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 工具描述写成 <code>def calc(e): ...</code> 一个词——LLM 选工具全靠描述，描述差 = 工具白写",
"❌ 工具抛出原始 traceback 就返回——LLM 看不懂也纠不了错，要返回 <code>{'错误': '表达式不合法'}</code> 这种",
"✅ 每个工具都该有超时（模板的 wrapper 已示范），防止一个慢工具卡死整个 Agent",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://modelcontextprotocol.io/">MCP 官方文档</a>',
'<a href="https://github.com/modelcontextprotocol/python-sdk">MCP Python SDK</a>',
])}
"""


def day09() -> str:
    return f"""
<h1>Day 9：记忆系统与 RAG</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：让 Agent "记住"该记的东西——短期记忆管对话历史（带裁剪），
长期记忆/RAG 管知识检索。理解了今天的内容，你就理解了 ChatGPT 的"记忆"和"知识库问答"的全部原理。</p>
</blockquote>
{本日导航(9, False)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["40min", "<strong>理论学习</strong>：三种记忆 + RAG 五步", "阅读 + 编码"],
["40min", "<strong>RAG 实战</strong>：向量检索 + 检索器", "编码"],
["40min", "<strong>动手实操</strong>：带记忆的 Agent + 上下文裁剪", "编码"],
])}

<h2>📖 第一步：Agent 的三种记忆</h2>
{表头列(["类型", "存什么", "实现方式", "生命周期"], [
["短期记忆", "当前对话的消息历史", "消息列表 + 滑动窗口裁剪", "本次会话"],
["长期记忆", "用户偏好、事实、文档知识", "向量库检索（RAG）", "跨会话持久"],
["工作记忆", "当前任务的草稿/中间结果", "scratchpad / state 字段", "本次任务"],
])}
<p>为什么短期记忆要裁剪：模型上下文窗口有限（且越长越贵），10 轮对话后历史可能已超限——
所以要滑动窗口（只留最近 N 条）或摘要压缩（把旧历史总结成一段话）。</p>
{code("""
class ShortTermMemory:
    def add(self, role, content):
        self.messages.append(ConversationMessage(role, content))
        if len(self.messages) > self.max_messages:
            # 裁剪最旧的非 system 消息（system 是人设，必须永远保留）
            for i, m in enumerate(self.messages):
                if m.role != "system":
                    del self.messages[i]
                    break
""")}
<h2>📖 第二步：RAG（检索增强生成）五步流程</h2>
{code("""
① 知识入库    文档 → 切块(chunk) → 每块算 embedding → 存进向量库
                                        │
用户提问 ──► ② 问题也算 embedding ──────┤
              ③ 相似度检索：找出最相关的 top_k 块
              ④ 把检索到的知识拼进 Prompt：
                  "请参考以下资料回答：\\n{检索结果}\\n\\n问题：{用户问题}"
              ⑤ LLM 生成 —— 答案基于真实资料，不再靠幻觉
""")}
<p>本练习用<strong>关键词重合度</strong>代替 embedding（纯标准库能跑）；原理完全一致——
正式项目把 <code>SimpleVectorStore</code> 换成 ChromaDB/FAISS + embedding 模型即可，接口不变。
注意：英文按空格分词，<strong>中文没有空格</strong>，要按字/bigram 或 jieba 分词，否则检索直接失效（模板已处理）。</p>
<h2>🛠 第三步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day09_practice_template.html">day09_practice_template.py</a>：
  <ul>
  <li>TODO 1.1-1.4：<code>ShortTermMemory</code> 添加/裁剪/格式转换/清空</li>
  <li>TODO 2.1-2.2：<code>SimpleVectorStore</code> 添加与检索（关键词重合度打分即可）</li>
  <li>TODO 3.1-3.2：<code>RAGRetriever</code> 知识入库 + 检索并格式化成可拼接的文本</li>
  <li>TODO 4.1：<code>MemoryAgent.chat()</code> —— 先检索相关知识注入 prompt，再走对话，回答写回短期记忆</li>
  <li>TODO 5.1：<code>compress_conversation()</code> —— 按估算 token（1 个中文字 ≈ 2 token）从新到旧保留，system 不丢</li>
  </ul></li>
<li><strong>运行自测</strong>：<code>python day09_practice_template.py</code>。
测试 4 是记忆的"图灵测试"：先告诉它"我叫张三，我喜欢 Python"，再问"我叫什么名字？"——
答对了说明记忆链路通了。</li>
<li><strong>验收</strong>：按 <a href="ACCEPTANCE_CRITERIA.html">验收标准文档</a> Day 9 清单自查，并回答三个问题：
裁剪为什么保留 system？检索为什么比"把所有知识塞 prompt"好？压缩和滑动窗口各适合什么场景？</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 对话历史无限制地append → 超出上下文窗口直接报错；必须有裁剪或压缩策略",
"❌ 中文文本用空格分词做检索 → 整句一个'词'，检索永远失灵（要用分词/字符级匹配）",
"❌ Embedding 模型中英文不匹配 → 中文用 <code>bge-large-zh</code> 或 <code>text-embedding-3-small</code>",
"✅ 记忆不是越多越好——塞一堆无关历史反而稀释重点，<strong>相关性检索</strong>才是关键",
])}
<h2>🔗 延伸资源</h2>
{链接列表([
'<a href="https://docs.trychroma.com/">ChromaDB 文档</a>',
'<a href="https://python.langchain.com/docs/tutorials/rag/">LangChain RAG 教程</a>',
])}
"""


def day10() -> str:
    return f"""
<h1>Day 10：阶段二综合实战——多工具 Agent</h1>
<blockquote class="note-block">
<p><strong>🎯 今日目标</strong>：Day 1-9 所有组件的总装。产出一个有 4+ 工具、有记忆、有错误恢复、
有 Token 统计的完整 Agent。今天模板给得最少——因为所有零件你都亲手造过。</p>
</blockquote>
{本日导航(10, False)}
<h2>⏱ 今日安排（约 2 小时）</h2>
{表头列(["时间", "内容", "方式"], [
["20min", "<strong>总装图纸</strong>：组件关系与装配顺序", "阅读"],
["90min", "<strong>总装 + 测试</strong>：完成 6 个 TODO 和 6 个测试场景", "编码"],
["10min", "<strong>验收自查</strong>：对照清单逐项确认", "自查"],
])}

<h2>📖 第一步：总装图纸（各天组件怎么拼）</h2>
{code("""
                    ┌─────────────────────────────────────────┐
                    │            react_agent_with_memory       │
                    │                                          │
 用户输入 ─────────►│ ① memory.short_memory.get_recent()       │ ← Day 9 短期记忆
                    │ ② knowledge = memory.rag.retrieve(...)   │ ← Day 9 RAG 检索
                    │ ③ prompt = 记忆 + 知识 + 工具清单 + 问题  │ ← Day 6 prompt 构建
                    │ ④ for step in range(max_steps):          │ ← Day 1 异步 + 上限
                    │      llm 响应 → 解析 Action              │ ← Day 6 解析
                    │      execute_tool_with_recovery(...)     │ ← Day 8 超时 + 今天加重试
                    │      Observation 回填 → 下一轮           │
                    │ ⑤ metrics 统计 token / 耗时 / 调用次数    │ ← 今天新增
                    └─────────────────────────────────────────┘
""")}
<h3>错误恢复策略（今天的核心新知识点）</h3>
{表头列(["策略", "触发时机", "Agent 行为"], [
["RETRY", "瞬时错误（网络抖动）", "等 0.5s 重试 1-2 次"],
["FALLBACK", "重试仍失败", "换备用方案（如换工具/用 LLM 直接回答）"],
["SKIP", "非关键工具失败", "跳过该步骤，记录后继续"],
["ABORT", "关键步骤失败/超步数", "带错误说明终止，返回已获得的部分结果"],
])}
<p>关键思想：<strong>工具失败不是异常，是给 LLM 的一条 Observation</strong>——
把"计算器报错：除数不能为 0"喂回去，LLM 往往能自己换路子。程序崩溃才是失败，错误信息回传是纠错。</p>
<h2>🛠 第二步：动手实操</h2>
<ol>
<li><strong>打开模板</strong>：<a href="day10_practice_template.html">day10_practice_template.py</a>：
  <ul>
  <li>TODO 2.1：再注册 2 个工具（read_file / search_web 模拟版），凑满 4 个</li>
  <li>TODO 3.1：<code>react_agent_with_memory()</code> 主循环——按总装图纸把 ①-⑤ 串起来</li>
  <li>TODO 4.1：<code>print_metrics()</code> 美化输出统计</li>
  <li>TODO 5.1：<code>execute_tool_with_recovery()</code> —— 重试 2 次仍失败就把错误作为结果返回给 LLM，绝不抛异常打断循环</li>
  <li>TODO 6.1：编写 <code>main()</code> 的 6 个测试场景</li>
  </ul></li>
<li><strong>6 个测试场景（写进 main）</strong>：
  普通对话 / 单工具调用 / 多工具并发（<code>asyncio.gather</code>，Day 1）/ 多轮对话带记忆（Day 9）/
  工具失败后自动恢复（把一个工具故意改成会报错）/ Token 统计打印。</li>
<li><strong>验收</strong>：按 <a href="ACCEPTANCE_CRITERIA.html">验收标准文档</a> Day 10 清单自查。
自测标准：跑 <code>python day10_practice_template.py</code>，6 个场景全部有真实输出（不是 print 占位）。</li>
</ol>
<h2>⚠️ 避坑</h2>
{链接列表([
"❌ 一上来就拼全部组件——先把单工具 ReAct 跑通，再一个个往上挂，每挂一个测一次",
"❌ 工具失败直接 raise → 整个 Agent 崩溃；错误要作为 Observation 回传给 LLM 自行纠正",
"❌ Token 消耗不记录 → 成本失控时你毫无感知；每次 LLM 调用都记 prompt/completion tokens",
"✅ 这是阶段二收官：做完回头把 Day 6 和今天的代码对比一下，你会直观看到'框架前 vs 总装后'的差距",
])}
<h2>🚀 下一站</h2>
<p>阶段三（Day 11-15）将把这个 Agent 做成 FastAPI 服务 + Web 界面 + Docker 部署。
路线图见 <a href="index.html">主页</a>，交付清单见 <a href="ACCEPTANCE_CRITERIA.html">验收标准文档</a>——
从今天起没有模板了，按清单自主搭建，遇到问题回看对应天的学习页。</p>
"""


课程 = [
    (1, "异步编程核心", day01, True),
    (2, "类型系统与装饰器进阶", day02, True),
    (3, "生成器与上下文管理器", day03, True),
    (4, "LLM API 调用与 Function Calling", day04, True),
    (5, "阶段一综合实战：命令行 AI 助手", day05, True),
    (6, "Agent 架构原理：手写 ReAct", day06, True),
    (7, "LangGraph 入门", day07, True),
    (8, "工具系统设计与 MCP 协议", day08, False),
    (9, "记忆系统与 RAG", day09, False),
    (10, "阶段二综合实战：多工具 Agent", day10, False),
]


def 生成学习页(day: int, 主题: str, 内容函数, 有验收: bool, 样式: str) -> str:
    标题 = f"📖 Day{day:02d} Lesson"
    正文 = 内容函数()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{标题}</title>
    <style>
{样式}
    </style>
</head>
<body>
<div class="nav-wrapper">
{构造侧边栏(f"day{day:02d}_lesson.html")}
<div class="main-content">
    <div class="header"><h1>📖 Day {day} 学习页：{主题}</h1></div>
    <div class="content">
{正文}
    </div>
</div>
</div>
<button class="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="返回顶部">⬆</button>
<script>window.addEventListener("scroll",function(){{  var btn=document.querySelector(".back-top");  if(btn)btn.style.display=window.scrollY>300?"block":"none";}});</script>
</body>
</html>"""


def main():
    指定 = [a for a in sys.argv[1:] if a.startswith("day") and a.endswith("_lesson.html")]
    样式 = 提取样式()
    for day, 主题, 内容函数, 有验收 in 课程:
        名称 = f"day{day:02d}_lesson.html"
        if 指定 and 名称 not in 指定:
            continue
        (根目录 / 名称).write_text(生成学习页(day, 主题, 内容函数, 有验收, 样式), encoding="utf-8")
        print(f"✅ 已生成 {名称}")
    print("\n完成")


if __name__ == "__main__":
    main()
