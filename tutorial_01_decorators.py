"""
============================================================
Python 装饰器 零基础实战教程
============================================================
目标：从"完全不懂"到"能在 AI Agent 里用装饰器注册工具"

运行方式：python tutorial_01_decorators.py
学习方式：从上到下逐步阅读，每步都输出结果，理解后再看下一步

核心理解（一句话）：装饰器 = 接受一个函数，返回一个新函数
类比：就像给手机套壳 —— 手机还是那个手机，但多了保护/外观功能
============================================================
"""
import functools
import time
from datetime import datetime

print("=" * 60)
print("第 1 步：理解「函数是一等公民」—— 函数可以当参数传递")
print("=" * 60)

def 打招呼(name):
    return f"你好，{name}！"

def 加感叹(func, name):
    """接收一个函数作为参数，调用它并加感叹号"""
    return func(name) + "！！！"

result = 加感叹(打招呼, "hangbo")
print(f"结果：{result}")
print("👉 看到了吗？「打招呼」这个函数被当作参数传给了「加感叹」")
print()

print("=" * 60)
print("第 2 步：函数内部可以定义函数，也可以返回函数")
print("=" * 60)

def 创建乘法器(n):
    """这个函数返回一个新函数！"""
    def 乘n(x):
        return x * n
    return 乘n  # 注意：返回的是函数本身，不是调用的结果

乘3 = 创建乘法器(3)
乘5 = 创建乘法器(5)
print(f"乘3(10) = {乘3(10)}")
print(f"乘5(10) = {乘5(10)}")
print("👉 创建乘法器(3) 返回了一个「把任何数乘以3」的函数")
print()

print("=" * 60)
print("第 3 步：最简单的装饰器 —— 组合上面两个概念")
print("=" * 60)

def 计时装饰器(原函数):
    """包装一个函数，让它执行时自动打印耗时"""
    def 包装函数(*args, **kwargs):
        开始 = time.time()
        结果 = 原函数(*args, **kwargs)
        耗时 = time.time() - 开始
        print(f"  ⏱ {原函数.__name__} 执行耗时：{耗时:.4f} 秒")
        return 结果
    return 包装函数

def 慢速加法(a, b):
    time.sleep(1)
    return a + b

# 方式一：手动包装（理解原理）
慢速加法_计时版 = 计时装饰器(慢速加法)
print("手动包装：")
print(f"结果：{慢速加法_计时版(3, 5)}")
print()

print("=" * 60)
print("第 4 步：@ 语法糖 —— 让代码更优雅")
print("=" * 60)

@计时装饰器  # 这一行等价于：慢速乘法 = 计时装饰器(慢速乘法)
def 慢速乘法(a, b):
    time.sleep(0.5)
    return a * b

print("@语法糖：")
print(f"结果：{慢速乘法(4, 7)}")
print("👉 @计时装饰器 放在 def 上面，Python 会自动完成包装")
print()

print("=" * 60)
print("第 5 步：装饰器的致命陷阱 —— functools.wraps")
print("=" * 60)

def 坏装饰器(原函数):
    """不带 wraps 的装饰器（有 bug）"""
    def 包装(*args, **kwargs):
        return 原函数(*args, **kwargs)
    return 包装

def 好装饰器(原函数):
    """带 wraps 的装饰器（推荐）"""
    @functools.wraps(原函数)  # 保留原函数的元信息
    def 包装(*args, **kwargs):
        return 原函数(*args, **kwargs)
    return 包装

@坏装饰器
def 函数A():
    """这是函数A的文档"""
    pass

@好装饰器
def 函数B():
    """这是函数B的文档"""
    pass

print(f"函数A.__name__ = {函数A.__name__}")   # 输出"包装"，丢失了原名！
print(f"函数A.__doc__  = {函数A.__doc__}")    # None！
print(f"函数B.__name__ = {函数B.__name__}")   # 正确：函数B
print(f"函数B.__doc__  = {函数B.__doc__}")    # 正确：文档
print("👉 写装饰器永远加 @functools.wraps(原函数)，否则丢失函数名和文档")
print()

print("=" * 60)
print("第 6 步：带参数的装饰器 —— 进阶必备")
print("=" * 60)

# 需求：有时候想重试 3 次，有时候想重试 5 次
# 需要「装饰器工厂」：一个返回装饰器的函数

def 重试(最大次数=3, 等待秒=1):
    """装饰器工厂：根据参数创建不同的重试装饰器"""
    def 装饰器(原函数):
        @functools.wraps(原函数)
        def 包装(*args, **kwargs):
            for i in range(最大次数):
                try:
                    return 原函数(*args, **kwargs)
                except Exception as e:
                    if i == 最大次数 - 1:
                        raise  # 最后一次还失败就抛出
                    print(f"  重试 {i+1}/{最大次数}：{e}")
                    time.sleep(等待秒)
        return 包装
    return 装饰器

@重试(最大次数=3, 等待秒=0.5)
def 不稳定的网络请求():
    global 调用次数
    调用次数 += 1
    if 调用次数 < 3:
        raise ConnectionError("网络断开")
    return "数据获取成功"

调用次数 = 0
print(f"结果：{不稳定的网络请求()}")
print()

print("=" * 60)
print("第 7 步：类装饰器 —— 另一种写法")
print("=" * 60)

class 记录调用次数:
    """用类做装饰器，可以保存状态（调用了多少次）"""
    def __init__(self, 原函数):
        self.原函数 = 原函数
        self.次数 = 0

    def __call__(self, *args, **kwargs):
        self.次数 += 1
        print(f"  {self.原函数.__name__} 已被调用 {self.次数} 次")
        return self.原函数(*args, **kwargs)

@记录调用次数
def 计算平方(x):
    return x * x

print(f"计算平方(5) = {计算平方(5)}")
print(f"计算平方(6) = {计算平方(6)}")
print(f"计算平方(7) = {计算平方(7)}")
print()

print("=" * 60)
print("第 8 步：AI Agent 实战 —— 工具注册装饰器")
print("=" * 60)
print("这是你未来 AI Agent 的核心机制之一！")
print()

# 模拟 Agent 的工具注册表
工具注册表 = {}

def 工具(名称: str, 描述: str):
    """装饰器：把 Python 函数注册为 Agent 可用的工具"""
    def 装饰器(func):
        @functools.wraps(func)
        def 包装(*args, **kwargs):
            return func(*args, **kwargs)
        工具注册表[名称] = {
            "函数": 包装,
            "描述": 描述,
            "参数": func.__code__.co_varnames[:func.__code__.co_argcount]
        }
        return 包装
    return 装饰器

# 注册工具 —— 看！和写普通函数一样简单
@工具("计算器", "执行四则运算，例如：计算 3 + 5 * 2")
def 计算(表达式: str):
    return eval(表达式)  # 生产环境用 ast.literal_eval 更安全

@工具("天气查询", "查询指定城市的天气")
def 查天气(城市: str):
    # 模拟 API 调用
    return {"城市": 城市, "温度": "25°C", "天气": "晴"}

@工具("文件搜索", "搜索包含关键词的文件")
def 搜文件(关键词: str):
    return ["main.py", "config.py", "agent.py"]

# 打印注册表
print("已注册的工具：")
for 名称, 信息 in 工具注册表.items():
    print(f"  🔧 {名称}：{信息['描述']}")
    print(f"     参数：{信息['参数']}")
print()

# 调用工具
print(f"计算(3+5*2) = {计算('3+5*2')}")
print(f"查天气('北京') = {查天气('北京')}")
print()

print("=" * 60)
print("总结：装饰器核心要点")
print("=" * 60)
print("""
1. 装饰器本质：接受函数 → 返回新函数（第1-2步）
2. 基本写法：def 装饰器(func): ... return 包装函数（第3步）
3. @语法糖：@装饰器名 放在 def 上一行（第4步）
4. 必须加 @functools.wraps(原函数)（第5步）
5. 带参数：三层嵌套，最外层接收参数（第6步）
6. AI Agent 应用：用装饰器注册工具（第8步）

学完这个，去看 Day 2 的 Pydantic 和高级 typing，
你会发现自己能写出更规范的代码！
""")
