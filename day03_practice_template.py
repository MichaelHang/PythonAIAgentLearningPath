"""
Day 3 练习：实现流式 LLM 响应的异步生成器包装器
验收标准：
1. 必须实现异步生成器（async def + yield）
2. 必须实现同步生成器（def + yield）做对比
3. 必须使用 @contextmanager 或 __enter__/__exit__ 实现上下文管理器
4. 必须使用 @asynccontextmanager 实现异步上下文管理器
5. 流式输出模拟：逐块（chunk）产出数据，不是一次性返回
6. 代码有类型注解
"""

import asyncio
import time
from typing import AsyncGenerator, Generator, List, Dict, Any, Optional
from contextlib import contextmanager, asynccontextmanager


# ==================== 任务 1：同步生成器（基础） ====================
# 提示：生成器用 yield 而不是 return，可以暂停和恢复

def 模拟_llm_流式输出_同步(提示词: str, 延迟秒: float = 0.2) -> Generator[str, None, None]:
    """
    同步生成器：模拟 LLM 逐 token 输出
    
    需求：
    1. 用 yield 逐块输出（不要用 return）
    2. 每次 yield 后暂停，下次迭代从上次暂停处继续
    3. 模拟 5 个 chunk 的输出
    
    示例输出：
    "我"
    "我喜欢"
    "我喜欢写"
    "我喜欢写代码"
    "（完成）"
    """
    # TODO 1.1：实现同步生成器
    # 提示：
    # 1. 把 提示词 拆成若干个 chunk
    # 2. 用 for 循环遍历 chunk，每次 yield 一个
    # 3. 每次 yield 前用 time.sleep(延迟秒) 模拟延迟
    pass


def 同步调用示例():
    """演示如何使用同步生成器"""
    print("📝 同步生成器示例：")
    # TODO 1.2：用 for 循环迭代生成器，打印每个 chunk
    # 提示：for chunk in 模拟_llm_流式输出_同步("Hello"):
    #           print(chunk, end="", flush=True)
    pass


# ==================== 任务 2：异步生成器（核心） ====================
# 提示：async def + yield = 异步生成器，可以用在 async for 中

async def 模拟_llm_流式输出_异步(提示词: str, 延迟秒: float = 0.2) -> AsyncGenerator[str, None]:
    """
    异步生成器：模拟 LLM 流式输出（Agent 核心机制）
    
    需求：
    1. 用 async def 定义，函数体里用 yield
    2. 用 await asyncio.sleep() 模拟延迟（不要用 time.sleep！）
    3. 逐 chunk yield，不是一次性返回
    
    提示：这是 Agent 接收 LLM 流式响应的核心模式
    """
    # TODO 2.1：实现异步生成器
    # 提示：
    # 1. 拆分提示词为 chunk
    # 2. async for? 不，用 for + await asyncio.sleep()
    # 3. 每次循环 yield 一个 chunk
    pass


async def 异步调用示例():
    """演示如何使用异步生成器"""
    print("\n📝 异步生成器示例：")
    # TODO 2.2：用 async for 迭代异步生成器
    # 提示：async for chunk in 模拟_llm_流式输出_异步("Hello World"):
    #           print(chunk, end="", flush=True)
    #       print()  # 换行
    pass


# ==================== 任务 3：上下文管理器（同步） ====================
# 提示：上下文管理器用于资源管理（文件、连接、计时等）

class LLM请求计时器:
    """
    同步上下文管理器：统计 LLM 请求耗时
    
    需求：
    1. 实现 __enter__ 和 __exit__ 方法
    2. __enter__ 记录开始时间，返回 self
    3. __exit__ 计算耗时并打印
    4. 支持 with 语句
    """
    def __enter__(self):
        # TODO 3.1：记录开始时间，返回 self
        pass
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO 3.2：计算耗时并打印
        # 提示：如果 exc_type 不为 None，说明 with 块内发生了异常
        pass


@contextmanager
def llm请求计时器_装饰器版本(请求名称: str):
    """
    用 @contextmanager 实现上下文管理器（更简洁）
    
    需求：
    1. 用 @contextmanager 装饰器
    2. yield 之前是 __enter__ 的逻辑
    3. yield 之后是 __exit__ 的逻辑
    """
    # TODO 3.3：实现 @contextmanager 版本的上下文管理器
    # 提示：
    # 1. 记录开始时间
    # 2. yield（yield 处相当于 __enter__ return）
    # 3. 计算耗时并打印（yield 之后相当于 __exit__）
    pass


def 上下文管理器示例():
    """演示如何使用上下文管理器"""
    print("\n📝 同步上下文管理器示例：")
    
    # 方式 1：类实现
    with LLM请求计时器():
        time.sleep(0.5)
        print("  （模拟 LLM 请求中...）")
    
    # 方式 2：@contextmanager 实现
    with llm请求计时器_装饰器版本("查询天气"):
        time.sleep(0.3)
        print("  （模拟工具调用中...）")


# ==================== 任务 4：异步上下文管理器 ====================

class 异步LLM请求计时器:
    """
    异步上下文管理器：统计异步 LLM 请求耗时
    
    需求：
    1. 实现 __aenter__ 和 __aexit__ 方法（注意是 aenter/aexit）
    2. 用 asyncio.sleep() 而不是 time.sleep()
    """
    async def __aenter__(self):
        # TODO 4.1：记录开始时间，返回 self
        pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # TODO 4.2：计算耗时并打印
        pass


@asynccontextmanager
async def 异步请求计时器(请求名称: str):
    """用 @asynccontextmanager 实现异步上下文管理器"""
    # TODO 4.3：实现异步上下文管理器
    # 提示：和同步版本类似，但用 async def + yield
    pass


async def 异步上下文管理器示例():
    """演示如何使用异步上下文管理器"""
    print("\n📝 异步上下文管理器示例：")
    
    async with 异步LLM请求计时器():
        await asyncio.sleep(0.5)
        print("  （模拟异步 LLM 请求中...）")
    
    async with 异步请求计时器("批量工具调用"):
        await asyncio.sleep(0.3)
        print("  （模拟并发工具调用中...）")


# ==================== 任务 5：组合——流式输出 + 计时 ====================
# 这是 Day 3 的最终目标：一个完整的流式 LLM 调用包装器

class 流式LLM客户端:
    """
    流式 LLM 客户端（完整的 Agent 组件）
    
    需求：
    1. __init__ 接受 API key 和模型名称
    2. chat() 方法返回异步生成器（AsyncGenerator）
    3. 用异步上下文管理器包装，自动计时
    4. 支持 system_prompt 和 user_prompt
    """
    def __init__(self, 模型名称: str = "deepseek-chat"):
        self.模型名称 = 模型名称
    
    def chat(self, 提示词: str) -> AsyncGenerator[str, None]:
        """
        发起聊天请求，返回流式响应
        
        需求：
        1. 这是一个异步生成器方法
        2. 用异步上下文管理器包装，自动打印耗时
        3. 逐 chunk yield 响应内容
        """
        # TODO 5.1：实现流式 chat 方法
        # 提示：这是异步生成器，用 async def + yield
        # 结合 async with 异步上下文管理器
        pass


async def 最终示例():
    """Day 3 最终示例：完整的流式 LLM 客户端"""
    print("\n📝 Day 3 最终示例：流式 LLM 客户端")
    
    客户端 = 流式LLM客户端(模型名称="deepseek-chat")
    
    print("用户：请用中文介绍 Python 的 async/await")
    print("助手：", end="")
    
    async for chunk in 客户端.chat("请用中文介绍 Python 的 async/await"):
        print(chunk, end="", flush=True)
    print()  # 换行


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    print("=" * 60)
    print("Day 3 练习：流式 LLM 响应的异步生成器包装器")
    print("=" * 60)
    
    # 任务 1：同步生成器
    同步调用示例()
    
    # 任务 2：异步生成器
    await 异步调用示例()
    
    # 任务 3：同步上下文管理器
    上下文管理器示例()
    
    # 任务 4：异步上下文管理器
    await 异步上下文管理器示例()
    
    # 任务 5：组合
    await 最终示例()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例完成！现在运行 python day03_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    开始时间 = time.time()
    asyncio.run(main())
    总耗时 = time.time() - 开始时间
    print(f"\n⏱ 总耗时：{总耗时:.2f} 秒")
