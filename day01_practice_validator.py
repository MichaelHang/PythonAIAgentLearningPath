"""
Day 1 练习项目验收脚本
异步批量调用多个 API（模拟 Agent 多工具并发调用）

运行方式：python day01_practice_validator.py
功能：自动检测你的练习代码并提供反馈
"""

import asyncio
import time
import inspect
import importlib.util
from pathlib import Path

print("=" * 70)
print("📋 Day 1 练习项目验收工具")
print("=" * 70)
print()

# ========================================
# 第 1 步：检查是否有练习代码文件
# ========================================

print("【第 1 步】检查练习代码文件...")
print("-" * 70)

练习文件列表 = [
    "day01_practice.py",
    "practice_day01.py", 
    "async_practice.py",
    "day1.py",
]

用户代码文件 = None
for 文件名 in 练习文件列表:
    if Path(文件名).exists():
        用户代码文件 = 文件名
        print(f"✅ 找到练习文件：{文件名}")
        break

if 用户代码文件 is None:
    print("❌ 未找到练习代码文件")
    print("请创建以下名称之一的文件：")
    for 文件名 in 练习文件列表:
        print(f"   - {文件名}")
    print()
    print("💡 如果文件名不同，请手动修改本脚本的「练习文件列表」")
else:
    print(f"📂 将加载：{用户代码文件}")
    print()

# ========================================
# 第 2 步：加载用户的代码
# ========================================

if 用户代码文件:
    print("【第 2 步】加载并分析你的代码...")
    print("-" * 70)
    
    try:
        # 动态加载用户的 Python 文件
        spec = importlib.util.spec_from_file_location("user_code", 用户代码文件)
        用户模块 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(用户模块)
        print(f"✅ 代码加载成功！没有语法错误")
        
        # 分析模块中有哪些函数/类
        所有函数 = [name for name in dir(用户模块) if callable(getattr(用户模块, name)) and not name.startswith("_")]
        print(f"📊 发现 {len(所有函数)} 个可调用对象：{', '.join(所有函数[:10])}")
        print()
        
    except SyntaxError as e:
        print(f"❌ 语法错误：{e}")
        print("请修复语法错误后重新运行本脚本")
        用户模块 = None
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        用户模块 = None
else:
    用户模块 = None

# ========================================
# 第 3 步：性能验收测试
# ========================================

print("【第 3 步】性能验收测试（同步 vs 异步）")
print("-" * 70)
print("一个正确的异步实现应该比同步实现快很多！")
print()

async def 模拟API调用(名称, 延迟):
    """模拟 API 调用"""
    await asyncio.sleep(延迟)
    return f"{名称} 返回结果（延迟 {延迟}s）"

def 测试同步调用():
    """测试同步方式的耗时"""
    开始 = time.time()
    
    结果1 = asyncio.run(模拟API调用("API-1", 1))
    结果2 = asyncio.run(模拟API调用("API-2", 2))
    结果3 = asyncio.run(模拟API调用("API-3", 1.5))
    
    耗时 = time.time() - 开始
    return 耗时, [结果1, 结果2, 结果3]

async def 测试异步调用():
    """测试异步方式的耗时"""
    开始 = time.time()
    
    结果们 = await asyncio.gather(
        模拟API调用("API-1", 1),
        模拟API调用("API-2", 2),
        模拟API调用("API-3", 1.5),
    )
    
    耗时 = time.time() - 开始
    return 耗时, 结果们

print("  🔍 测试 1：同步调用（作为基准）")
同步耗时, 同步结果 = 测试同步调用()
print(f"     结果：{同步耗时:.2f} 秒")
print(f"     预期：~4.5 秒（1 + 2 + 1.5）")
print()

print("  🔍 测试 2：异步并发调用（应该是这样）")
异步耗时, 异步结果 = asyncio.run(测试异步调用())
print(f"     结果：{异步耗时:.2f} 秒")
print(f"     预期：~2.0 秒（取最长的延迟）")
print()

print("  📊 性能对比：")
print(f"     同步：{同步耗时:.2f} 秒")
print(f"     异步：{异步耗时:.2f} 秒")
提升 = (同步耗时 - 异步耗时) / 同步耗时 * 100
print(f"     性能提升：{提升:.1f}%")
print()

if 异步耗时 < 同步耗时 * 0.6:
    print("  ✅ 验收通过！异步版本明显快于同步版本")
else:
    print("  ⚠️ 异步版本可能不正确，耗时没有显著减少")
    print("     检查是否真的使用了 asyncio.gather() 或 create_task()")
print()

# ========================================
# 第 4 步：代码质量检查
# ========================================

if 用户模块:
    print("【第 4 步】代码质量检查")
    print("-" * 70)
    
    评分 = 0
    总分 = 0
    
    # 检查 1：是否使用了 async/await
    总分 += 20
    print("  🔍 检查 1：是否使用了 async def 定义异步函数？（20 分）")
    
    异步函数列表 = []
    for name in dir(用户模块):
        obj = getattr(用户模块, name)
        if callable(obj) and inspect.iscoroutinefunction(obj):
            异步函数列表.append(name)
    
    if len(异步函数列表) > 0:
        print(f"     ✅ 发现 {len(异步函数列表)} 个异步函数：{', '.join(异步函数列表)}")
        评分 += 20
    else:
        print("     ❌ 未找到异步函数（使用 async def 定义的函数）")
        print("     💡 提示：确保你的函数用 async def 定义")
    print()
    
    # 检查 2：是否使用了 asyncio.gather() 或 create_task()
    总分 += 20
    print("  🔍 检查 2：是否使用了 asyncio.gather() 或 create_task()？（20 分）")
    
    try:
        with open(用户代码文件, "r", encoding="utf-8") as f:
            代码内容 = f.read()
        
        if "asyncio.gather" in 代码内容:
            print("     ✅ 使用了 asyncio.gather()")
            评分 += 20
        elif "create_task" in 代码内容:
            print("     ✅ 使用了 asyncio.create_task()")
            评分 += 20
        else:
            print("     ❌ 未找到 asyncio.gather() 或 create_task()")
            print("     💡 提示：并发执行多个任务需要用这两个方法之一")
    except:
        print("     ⚠️ 无法读取代码文件")
    print()
    
    # 检查 3：是否有错误处理（try/except）
    总分 += 15
    print("  🔍 检查 3：是否有错误处理（try/except）？（15 分）")
    
    if "try" in 代码内容 and "except" in 代码内容:
        print("     ✅ 有错误处理")
        评分 += 15
    else:
        print("     ⚠️ 未找到错误处理")
        print("     💡 提示：真实 API 调用可能失败，应该加 try/except")
    评分 += 15
    print()
    
    # 检查 4：是否有超时控制（asyncio.timeout）
    总分 += 15
    print("  🔍 检查 4：是否有超时控制（asyncio.timeout）？（15 分）")
    
    if "timeout" in 代码内容.lower():
        print("     ✅ 有超时控制")
        评分 += 15
    else:
        print("     ⚠️ 未找到超时控制")
        print("     💡 提示：API 调用可能卡死，应该用 async with asyncio.timeout():")
    评分 += 15
    print()
    
    # 检查 5：是否有类型注解
    总分 += 10
    print("  🔍 检查 5：是否有类型注解？（10 分）")
    
    if ":" in 代码内容 and "->" in 代码内容:
        print("     ✅ 有类型注解")
        评分 += 10
    else:
        print("     ⚠️ 未找到类型注解")
        print("     💡 提示：类型注解可以帮助 IDE 提供更好的提示")
    print()
    
    # 检查 6：是否有文档字符串（docstring）
    总分 += 10
    print("  🔍 检查 6：是否有文档字符串（docstring）？（10 分）")
    
    if '"""' in 代码内容 or "'''" in 代码内容:
        print("     ✅ 有文档字符串")
        评分 += 10
    else:
        print("     ⚠️ 未找到文档字符串")
        print("     💡 提示：在函数内部第一行用三引号写文档")
    print()
    
    # 检查 7：是否使用了 time.sleep()（常见错误）
    总分 += 10
    print("  🔍 检查 7：是否错误地在异步函数中使用了 time.sleep()？（扣分项）")
    
    if "time.sleep" in 代码内容 and "async def" in 代码内容:
        print("     ❌ 发现 time.sleep()！这会阻塞事件循环！")
        print("     💡 应该改为 await asyncio.sleep()")
    else:
        print("     ✅ 未误用 time.sleep()")
        评分 += 10
    print()
    
    # 总结评分
    print("  " + "=" * 70)
    print(f"  📈 代码质量评分：{评分}/{总分}")
    print("  " + "=" * 70)
    print()
    
    if 评分 >= 总分 * 0.8:
        print("  🎉 优秀！代码质量很高")
    elif 评分 >= 总分 * 0.6:
        print("  👍 良好！还可以改进")
    else:
        print("  💪 需要努力！建议参考教程并重写")
    print()

# ========================================
# 第 5 步：提供参考实现
# ========================================

print("【第 5 步】提供参考实现（如果卡住了可以参考）")
print("-" * 70)
print()

print("以下是一个正确的实现示例：")
print()

print("""```python
import asyncio
import time
from typing import List, Dict, Any

async def 调用API(api名称: str, 参数: Dict[str, Any], 延迟: float = 1.0) -> Dict[str, Any]:
    \"\"\"调用单个 API（异步）\"\"\"
    print(f"  🔧 正在调用 {api名称}...")
    try:
        async with asyncio.timeout(5):  # 超时控制
            await asyncio.sleep(延迟)  # 模拟网络延迟
            result = {
                "api": api名称,
                "params": 参数,
                "result": f"处理结果：{参数}",
                "耗时": 延迟
            }
            print(f"  ✅ {api名称} 调用成功")
            return result
    except asyncio.TimeoutError:
        print(f"  ❌ {api名称} 调用超时")
        return {"error": "timeout"}
    except Exception as e:
        print(f"  ❌ {api名称} 调用失败：{e}")
        return {"error": str(e)}

async def 批量调用API_异步(api列表: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    \"\"\"异步并发调用多个 API\"\"\"
    print(f"🚀 开始异步并发调用 {len(api列表)} 个 API...")
    开始时间 = time.time()
    
    # 使用 gather 并发执行
    results = await asyncio.gather(
        *(调用API(api["name"], api["params"], api.get("delay", 1.0)) for api in api列表),
        return_exceptions=True  # 即使有异常也不中断
    )
    
    总耗时 = time.time() - 开始时间
    print(f"✅ 全部完成！总耗时：{总耗时:.2f} 秒")
    return results

def 批量调用API_同步(api列表: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    \"\"\"同步逐个调用多个 API（作为对比）\"\"\"
    print(f"🐢 开始同步逐个调用 {len(api列表)} 个 API...")
    开始时间 = time.time()
    
    results = []
    for api in api列表:
        print(f"  🔧 正在调用 {api['name']}...")
        time.sleep(api.get("delay", 1.0))  # ❌ 真实代码中不要用 time.sleep
        results.append({
            "api": api["name"],
            "result": f"处理结果：{api['params']}"
        })
        print(f"  ✅ {api['name']} 调用成功")
    
    总耗时 = time.time() - 开始时间
    print(f"✅ 全部完成！总耗时：{总耗时:.2f} 秒")
    return results

# 主函数
async def main():
    # 准备测试数据
    api列表 = [
        {"name": "天气API", "params": {"city": "北京"}, "delay": 2.0},
        {"name": "翻译API", "params": {"text": "Hello"}, "delay": 1.5},
        {"name": "搜索API", "params": {"query": "AI Agent"}, "delay": 1.0},
        {"name": "计算API", "params": {"expr": "2+3*4"}, "delay": 0.5},
    ]
    
    print("=" * 70)
    print("测试 1：同步调用（慢）")
    print("=" * 70)
    同步结果 = 批量调用API_同步(api列表)
    print()
    
    print("=" * 70)
    print("测试 2：异步并发调用（快）")
    print("=" * 70)
    异步结果 = await 批量调用API_异步(api列表)
    print()
    
    print("=" * 70)
    print("结果对比")
    print("=" * 70)
    for i, (同步, 异步) in enumerate(zip(同步结果, 异步结果)):
        print(f"{i+1}. {api列表[i]['name']}")
        print(f"   同步：{同步}")
        print(f"   异步：{异步}")

if __name__ == "__main__":
    asyncio.run(main())
```""")

print()
print("=" * 70)
print("📋 验收总结")
print("=" * 70)
print()
print("✅ 你的练习项目正确的标志：")
print("  1. 使用了 async/await 语法")
print("  2. 使用了 asyncio.gather() 或 create_task() 实现并发")
print("  3. 异步版本比同步版本快至少 30%")
print("  4. 有错误处理（try/except）")
print("  5. 有超时控制（asyncio.timeout）")
print("  6. 没有在异步函数中使用 time.sleep()")
print()
print("🎯 下一步：")
print("  如果通过了本验收，继续 Day 2 的学习！")
print("  如果未通过，参考上面的代码示例并重写你的练习。")
print()
print("=" * 70)
