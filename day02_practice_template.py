"""
Day 2 练习：用 Pydantic 定义 Tool Schema + 装饰器实现工具注册机制
验收标准：
1. 必须使用 Pydantic v2 定义 Tool 的输入/输出 Schema
2. 必须实现一个 @工具 装饰器，自动注册函数到工具注册表
3. 装饰器必须正确使用 @functools.wraps
4. 注册的工具有名称、描述、参数列表、输入输出 Schema
5. 至少注册 3 个不同功能的工具
6. 代码有类型注解
"""

import functools
import inspect
from typing import Any, Dict, List, Callable, Optional, Union
from pydantic import BaseModel, Field, ValidationError
import json


# ==================== 任务 1：用 Pydantic 定义 Tool 的 Schema ====================
# 提示：ToolInput 定义工具的输入参数，ToolOutput 定义输出格式

# TODO 1.1：定义 ToolInput 基类（可选，也可以为每个工具单独定义）
# 提示：可以用 TypedDict 或 BaseModel


# TODO 1.2：为每个工具定义输入 Schema（至少 3 个工具）
# 示例：计算器工具的输入
class 计算器输入(BaseModel):
    表达式: str = Field(..., description="四则运算表达式，例如 '3 + 5 * 2'")


class 计算器输出(BaseModel):
    结果: Union[float, int] = Field(..., description="计算结果")
    表达式: str = Field(..., description="原始表达式")


# TODO 1.3：定义至少 2 个其他工具的 Schema
# 提示：可以定义"天气查询"、"文件搜索"、"翻译"等
# 每个工具都需要输入 Schema 和输出 Schema




# ==================== 任务 2：实现 @工具 装饰器 ====================
# 提示：装饰器需要把被装饰的函数注册到全局工具注册表中

# 全局工具注册表
工具注册表: Dict[str, Dict[str, Any]] = {}


def 工具(
    名称: str,
    描述: str,
    输入模型: Optional[type[BaseModel]] = None,
    输出模型: Optional[type[BaseModel]] = None,
):
    """
    工具注册装饰器
    
    需求：
    1. 这是一个带参数的装饰器（三层嵌套）
    2. 将被装饰的函数注册到 工具注册表
    3. 注册信息包括：名称、描述、函数引用、输入/输出 Schema、参数列表
    4. 必须正确使用 @functools.wraps
    5. 包装函数需要对输入做 Pydantic 验证
    
    提示：
    包装函数应该：
      1. 用 输入模型 验证输入参数（如果提供了的话）
      2. 调用原始函数
      3. 用 输出模型 验证输出（如果提供了的话）
      4. 返回结果
    """
    # TODO 2.1：实现装饰器（三层嵌套）
    # 提示：最外层是 工具()，中间层是装饰器(func)，最内层是包装函数(*args, **kwargs)
    
    def 装饰器(func: Callable):
        @functools.wraps(func)
        def 包装函数(*args, **kwargs):
            # TODO 2.2：输入验证（如果提供了输入模型）
            # 提示：把 kwargs 或 args 转换成输入模型的实例
            
            # TODO 2.3：调用原始函数
            
            # TODO 2.4：输出验证（如果提供了输出模型）
            
            pass  # 删除这句，写你的代码
        
        # TODO 2.5：注册到工具注册表
        # 提示：工具注册表[名称] = {...}
        
        return 包装函数
    return 装饰器


# ==================== 任务 3：用 @工具 装饰器注册至少 3 个工具 ====================

# TODO 3.1：注册计算器工具
# 提示：
# @工具(名称="计算器", 描述="...", 输入模型=计算器输入, 输出模型=计算器输出)
# def 计算(表达式: str):
#     ...

@工具(
    名称="计算器",
    描述="执行四则运算，支持 + - * / 和括号，例如：计算 3 + 5 * 2",
    输入模型=计算器输入,
    输出模型=计算器输出,
)
def 计算(表达式: str) -> dict:
    """执行四则运算"""
    # 注意：生产环境请用 ast.literal_eval 或更安全的方法
    try:
        result = eval(表达式, {"__builtins__": {}}, {})
        return {"结果": result, "表达式": 表达式}
    except Exception as e:
        return {"结果": f"错误: {e}", "表达式": 表达式}


# TODO 3.2：注册天气查询工具
# 提示：定义 天气输入/天气输出，然后用 @工具 装饰


# TODO 3.3：注册第三个工具（自选）
# 提示：可以是文件搜索、翻译、日期计算等


# ==================== 任务 4：实现工具调用函数 ====================

def 调用工具(工具名称: str, **参数) -> Any:
    """
    根据工具名称调用已注册的工具
    
    需求：
    1. 从工具注册表中查找工具
    2. 如果找不到，抛出 ValueError
    3. 调用工具的"函数"
    4. 返回结果
    """
    # TODO 4.1：实现工具调用逻辑
    pass


def 列出所有工具() -> List[Dict[str, Any]]:
    """
    列出所有已注册的工具（供 LLM Function Calling 使用）
    
    需求：
    返回格式（符合 OpenAI Function Calling 格式）：
    [
        {
            "type": "function",
            "function": {
                "name": "计算器",
                "description": "...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "表达式": {"type": "string", "description": "..."}
                    },
                    "required": ["表达式"]
                }
            }
        },
        ...
    ]
    """
    # TODO 4.2：实现工具列表生成（转换为 OpenAI Function Calling 格式）
    # 提示：需要用 输入模型 的 schema() 方法获取 JSON Schema
    pass


# ==================== 主函数：测试所有功能 ====================

def main():
    print("=" * 60)
    print("Day 2 练习：Pydantic Schema + 工具注册装饰器")
    print("=" * 60)
    
    # 测试 1：调用计算器工具
    print("\n📝 测试 1：调用计算器工具")
    结果 = 调用工具("计算器", 表达式="3 + 5 * 2")
    print(f"结果：{结果}")
    
    # 测试 2：输入验证（应该失败）
    print("\n📝 测试 2：输入验证")
    try:
        调用工具("计算器", 表达式="import os; os.system('ls')")  # 危险输入
        print("⚠️ 警告：危险输入没有被拦截！")
    except Exception as e:
        print(f"✅ 输入验证生效：{e}")
    
    # 测试 3：列出所有工具（OpenAI Function Calling 格式）
    print("\n📝 测试 3：工具列表（供 LLM 使用）")
    工具列表 = 列出所有工具()
    print(json.dumps(工具列表, ensure_ascii=False, indent=2))
    
    # 测试 4：查看工具注册表
    print("\n📝 测试 4：工具注册表")
    for 名称, 信息 in 工具注册表.items():
        print(f"🔧 {名称}：{信息['描述']}")
        print(f"   函数：{信息['函数'].__name__}")
        print(f"   参数：{信息.get('参数', [])}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！现在运行 python day02_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    main()
