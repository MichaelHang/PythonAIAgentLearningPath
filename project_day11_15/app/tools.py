"""工具系统：注册表 + 内置工具（Day 2 装饰器模式 + Day 8 安全约定的服务化版本）"""

import functools
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import config

TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, parameters: Dict):
    """工具注册装饰器（三层骨架已给好，导入安全；TODO 2.1 只差注册那一行）

    骨架说明（和 Day 2 练习同款）：
    - 最外层 tool()：收 name/description/parameters
    - 中间层 decorator()：收被装饰的函数
    - 最内层 wrapper()：调用时执行原函数
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # TODO 2.1：把工具注册进 TOOLS_REGISTRY[name]，内容：
        #   {"function": wrapper, "description": description, "parameters": parameters}

        return wrapper
    return decorator


# ---- 示例工具（已实现，照着写后面的） ----

@tool(
    "calculator",
    "执行四则运算，输入运算表达式字符串，如 '3 + 5 * 2'",
    {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "运算表达式"}},
        "required": ["expression"],
    },
)
def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


def get_tool_list() -> List[Dict]:
    """TODO 2.2：把注册表转成 OpenAI Function Calling 的 tools 参数（Day 4 原题）"""
    raise NotImplementedError("TODO 2.2")


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """TODO 2.3：按名称执行工具

    要求：
    1. 工具不存在时返回错误字符串（不要抛异常——错误要作为 Observation 回传给 LLM）
    2. 工具内部抛异常时也捕获并返回错误字符串
    """
    raise NotImplementedError("TODO 2.3")


# ---- 文件工具（TODO 2.4：先实现安全边界，再实现读取） ----

def _安全路径(path: str) -> Path:
    """TODO 2.4：路径安全检查（本项目最重要的安全设计！）

    要求：
    1. 把 path 拼到 config.WORKSPACE_DIR 下（相对路径）
    2. .resolve() 后检查结果仍然位于 WORKSPACE_DIR 内——防止 "../../etc/passwd" 路径穿越
    3. 越界时抛 PermissionError
    提示：Path.resolve() + Path.relative_to() 的组合
    """
    raise NotImplementedError("TODO 2.4")


@tool(
    "read_file",
    "读取工作区内文本文件的内容",
    {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "相对工作区的文件路径，如 notes/a.md"}},
        "required": ["path"],
    },
)
def read_file(path: str) -> str:
    target = _安全路径(path)
    return target.read_text(encoding="utf-8")


# TODO 2.5：再注册一个你自选的工具（如 write_file / list_files / word_count）
#   write_file 同样必须经过 _安全路径 检查！
