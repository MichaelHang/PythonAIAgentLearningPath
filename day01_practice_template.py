"""
Day 1 练习：异步批量调用多个 API（模拟 Agent 多工具并发调用）
验收标准：
1. 必须使用 async/await
2. 必须使用 asyncio.gather() 并发执行
3. 对比同步 vs 异步的性能差异（异步更快）
4. 正确处理异常
5. 代码有类型注解
"""

import asyncio
import time
from typing import List, Dict, Any


# ==================== 任务 1：实现异步 HTTP 请求 ====================
# 提示：使用 aiohttp 或 asyncio 模拟 API 调用

async def 异步请求(url: str, 延迟秒: float = 1.0) -> Dict[str, Any]:
    """
    模拟异步 API 请求
    
    需求：
    1. 使用 await asyncio.sleep(延迟秒) 模拟网络延迟
    2. 返回包含 url、状态码、响应数据的字典
    3. 添加 try/except 处理异常
    
    示例返回：
    {"url": "https://api.example.com/users", "status": 200, "data": {...}}
    """
    # TODO: 在这里写你的代码
    pass


# ==================== 任务 2：并发调用多个 API ====================
# 提示：使用 asyncio.gather()

async def 并发请求(urls: List[str]) -> List[Dict[str, Any]]:
    """
    并发请求多个 URL
    
    需求：
    1. 为每个 URL 创建异步任务
    2. 使用 asyncio.gather() 并发执行
    3. 返回所有结果
    
    提示：
    tasks = [异步请求(url) for url in urls]
    results = await asyncio.gather(*tasks)
    """
    # TODO: 在这里写你的代码
    pass


# ==================== 任务 3：对比同步 vs 异步性能 ====================
# 提示：分别用同步和异步方式请求 5 个 URL，记录耗时

def 同步请求(urls: List[str]) -> List[Dict[str, Any]]:
    """
    同步请求多个 URL（用于对比）
    
    需求：
    1. 使用 for 循环逐个请求
    2. 使用 time.sleep() 模拟延迟
    3. 记录总耗时
    
    提示：这是错误示范，故意写得很慢
    """
    # TODO: 在这里写你的代码
    pass


async def 性能对比():
    """
    对比同步 vs 异步的性能差异
    
    需求：
    1. 准备 5 个 URL（可以相同）
    2. 分别用同步和异步方式请求
    3. 打印两种方式的耗时
    4. 断言：异步耗时 < 同步耗时 * 0.5
    
    预期结果：
    同步：~5 秒（5 个请求 × 1 秒）
    异步：~1 秒（5 个请求并发，只花最慢的那个的时间）
    """
    # TODO: 在这里写你的代码
    pass


# ==================== 任务 4：异常处理 ====================
# 提示：有些请求可能失败，需要捕获异常

async def 异步请求带重试(url: str, 最大重试: int = 3) -> Dict[str, Any]:
    """
    带重试机制的异步请求
    
    需求：
    1. 如果请求失败（模拟随机失败），重试最多 最大重试 次
    2. 使用 try/except 捕获异常
    3. 每次重试前等待 0.5 秒
    
    提示：可以用 random.random() < 0.3 模拟 30% 失败率
    """
    # TODO: 在这里写你的代码
    pass


# ==================== 主函数 ====================

async def main():
    """主函数：运行所有练习"""
    print("=" * 60)
    print("Day 1 练习：异步批量调用多个 API")
    print("=" * 60)
    
    # 测试数据
    urls = [
        "https://api.example.com/users",
        "https://api.example.com/posts",
        "https://api.example.com/comments",
        "https://api.example.com/albums",
        "https://api.example.com/photos",
    ]
    
    # 任务 1：单个异步请求
    print("\n📝 任务 1：单个异步请求")
    result = await 异步请求(urls[0])
    print(f"结果：{result}")
    
    # 任务 2：并发请求
    print("\n📝 任务 2：并发请求")
    results = await 并发请求(urls[:3])
    print(f"并发请求了 {len(results)} 个 URL")
    
    # 任务 3：性能对比
    print("\n📝 任务 3：性能对比（同步 vs 异步）")
    await 性能对比()
    
    # 任务 4：异常处理
    print("\n📝 任务 4：异常处理（带重试）")
    result = await 异步请求带重试(urls[0])
    print(f"带重试的结果：{result}")
    
    print("\n" + "=" * 60)
    print("✅ 所有任务完成！现在运行 python day01_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    开始时间 = time.time()
    asyncio.run(main())
    总耗时 = time.time() - 开始时间
    print(f"\n⏱ 总耗时：{总耗时:.2f} 秒")
