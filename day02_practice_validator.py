#!/usr/bin/env python3
"""
Day 2 练习验收脚本
验收内容：Pydantic Schema + 装饰器工具注册

使用方法：
    python day02_practice_validator.py
    python day02_practice_validator.py --file day02_practice.py
"""

import ast
import inspect
import sys
import time
import subprocess
import json
import functools
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ==================== 配置 ====================
DEFAULT_FILENAME = "day02_practice_template.py"
TIMEOUT = 30  # 秒


# ==================== 颜色输出 ====================
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def 打印(内容: str, 颜色: str = C.END):
    print(f"{C.BOLD}{颜色}{内容}{C.END}")


# ==================== 检查项 ====================

def 检查_pydantic导入(代码: str) -> Tuple[bool, str]:
    """检查 1：是否导入 pydantic"""
    关键词 = ["from pydantic import", "import pydantic"]
    for kw in 关键词:
        if kw in 代码:
            return True, f"✅ 找到 pydantic 导入：{kw}"
    return False, "❌ 未找到 pydantic 导入（需要 from pydantic import BaseModel）"


def 检查_pydantic_schema(代码: str) -> Tuple[bool, str]:
    """检查 2：是否用 Pydantic 定义了输入/输出 Schema"""
    树 = ast.parse(代码)
    找到了_schema = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.ClassDef):
            # 检查类是否继承自 BaseModel
            for base in node.bases:
                if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                    找到了_schema = True
                    详情.append(f"✅ 找到 Pydantic Schema：{node.name}")
                elif isinstance(base, ast.Name) and base.id == "BaseModel":
                    找到了_schema = True
                    详情.append(f"✅ 找到 Pydantic Schema：{node.name}")
    
    if 找到了_schema:
        return True, "\n".join(详情)
    return False, "❌ 未找到 Pydantic Schema（需要定义继承 BaseModel 的类）"


def 检查_装饰器定义(代码: str) -> Tuple[bool, str]:
    """检查 3：是否实现了 @工具 装饰器"""
    树 = ast.parse(代码)
    找到了装饰器 = False
    详情 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            if "工具" in node.name or "tool" in node.name.lower():
                找到了装饰器 = True
                详情.append(f"✅ 找到装饰器函数：{node.name}")
                # 检查是否是三层嵌套
                for child in ast.walk(node):
                    if isinstance(child, ast.FunctionDef) and child != node:
                        详情.append(f"   └─ 包含内层函数：{child.name}（符合三层嵌套结构）")
    
    if 找到了装饰器:
        return True, "\n".join(详情)
    return False, "❌ 未找到 @工具 装饰器定义"


def 检查_functools_wraps(代码: str) -> Tuple[bool, str]:
    """检查 4：装饰器内是否使用了 @functools.wraps"""
    if "functools.wraps" in 代码 or "wraps(" in 代码:
        return True, "✅ 找到 @functools.wraps（正确保留了原函数元信息）"
    return False, "❌ 未找到 @functools.wraps（装饰器必须加 wraps！）"


def 检查_工具注册机制(代码: str) -> Tuple[bool, str]:
    """检查 5：是否有工具注册表"""
    树 = ast.parse(代码)
    找到了注册表 = False
    找到了注册逻辑 = False
    详情 = []
    
    for node in ast.walk(树):
        # 查找工具注册表变量
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and ("注册表" in target.id or "registry" in target.id.lower()):
                    找到了注册表 = True
                    详情.append(f"✅ 找到工具注册表：{target.id}")
        # 查找注册逻辑（工具注册表[名称] = ...）
        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Subscript):
                找到了注册逻辑 = True
                详情.append("✅ 找到工具注册逻辑")
    
    if 找到了注册表 and 找到了注册逻辑:
        return True, "\n".join(详情)
    elif 找到了注册表:
        return True, "\n".join(详情) + "\n⚠️ 未找到明确的注册逻辑（工具注册表[名称] = ...）"
    return False, "❌ 未找到工具注册表"


def 检查_至少3个工具(代码: str) -> Tuple[bool, str]:
    """检查 6：是否注册了至少 3 个工具"""
    树 = ast.parse(代码)
    工具数量 = 0
    工具列表 = []
    
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            # 检查函数是否有装饰器
            for decorator in node.decorator_list:
                # @工具(...) 或 @工具
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name) and "工具" in decorator.func.id:
                        工具数量 += 1
                        工具列表.append(node.name)
                elif isinstance(decorator, ast.Name) and "工具" in decorator.id:
                    工具数量 += 1
                    工具列表.append(node.name)
    
    if 工具数量 >= 3:
        return True, f"✅ 找到 {工具数量} 个注册的工具：{', '.join(工具列表)}"
    elif 工具数量 > 0:
        return False, f"⚠️ 只找到 {工具数量} 个工具（需要至少 3 个）：{', '.join(工具列表)}"
    return False, "❌ 未找到用 @工具 装饰器注册的工具"


def 检查_类型注解(代码: str) -> Tuple[bool, str]:
    """检查 7：函数是否有类型注解"""
    树 = ast.parse(代码)
    有注解 = 0
    无注解 = 0
    
    for node in ast.walk(树):
        if isinstance(node, ast.FunctionDef):
            # 检查返回值注解
            if node.returns is not None:
                有注解 += 1
            else:
                无注解 += 1
            # 检查参数注解
            for arg in node.args.args:
                if arg.annotation is not None:
                    有注解 += 1
    
    if 有注解 > 无注解:
        return True, f"✅ 类型注解覆盖率较高（有注解 {有注解}，无注解 {无注解}）"
    elif 有注解 > 0:
        return True, f"⚠️ 类型注解覆盖率较低（有注解 {有注解}，无注解 {无注解}）"
    return False, "❌ 未找到类型注解（建议加上 -> 返回值类型）"


def 检查_输入输出验证(代码: str) -> Tuple[bool, str]:
    """检查 8：包装函数内是否有输入/输出验证"""
    关键词 = ["validate", "模型", "输入模型", "输出模型", "schema"]
    找到了 = []
    for kw in 关键词:
        if kw in 代码:
            找到了.append(kw)
    
    if len(找到了) >= 2:
        return True, f"✅ 找到输入/输出验证相关代码：{', '.join(找到了)}"
    elif len(找到了) == 1:
        return True, f"⚠️ 只找到部分验证：{', '.join(找到了)}（建议同时验证输入和输出）"
    return False, "❌ 未找到输入/输出验证（包装函数内应该用 Pydantic 模型验证）"


# ==================== 运行测试 ====================

def 运行用户代码(文件路径: Path) -> Tuple[bool, str, float]:
    """运行用户的代码文件，返回（是否成功, 输出, 耗时）"""
    try:
        开始 = time.time()
        结果 = subprocess.run(
            [sys.executable, str(文件路径)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        耗时 = time.time() - 开始
        
        if 结果.returncode == 0:
            return True, 结果.stdout, 耗时
        else:
            return False, f"运行失败：\n{结果.stderr}", 耗时
    except subprocess.TimeoutExpired:
        return False, f"⏰ 运行超时（{TIMEOUT} 秒）", TIMEOUT
    except Exception as e:
        return False, f"运行出错：{e}", 0.0


def 检查_代码可运行(文件路径: Path) -> Tuple[bool, str]:
    """检查：代码是否能正常运行"""
    成功, 输出, 耗时 = 运行用户代码(文件路径)
    if 成功:
        return True, f"✅ 代码运行成功（耗时 {耗时:.2f} 秒）\n   输出预览：\n{输出[:300]}{'...' if len(输出) > 300 else ''}"
    else:
        return False, f"❌ 代码运行失败：\n{输出[:500]}"


def 检查_工具注册表可用(文件路径: Path) -> Tuple[bool, str]:
    """检查：注册的工具能否被调用"""
    # 在子进程中运行检验代码
    检验代码 = """
import sys
sys.path.insert(0, ".")
from pathlib import Path

# 动态导入用户的模块
import importlib.util
spec = importlib.util.spec_from_file_location("user_module", r"{}")
user_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_module)

# 检查工具注册表
if hasattr(user_module, "工具注册表"):
    registry = user_module.工具注册表
    print(f"✅ 工具注册表包含 {len(registry)} 个工具")
    for name, info in registry.items():
        print(f"   - {name}: {info.get('描述', '无描述')}")
else:
    print("❌ 未找到 工具注册表 变量")
""".format(str(文件路径).replace("\\", "\\\\"))
    
    try:
        结果 = subprocess.run(
            [sys.executable, "-c", 检验代码],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        if 结果.returncode == 0:
            return True, 结果.stdout.strip()
        else:
            return False, 结果.stderr.strip()
    except Exception as e:
        return False, f"检查失败：{e}"


# ==================== 主逻辑 ====================

def 验收(文件路径: Path) -> int:
    """主控函数，返回分数（0-100）"""
    打印(f"\n{'='*60}", C.CYAN)
    打印(f"  Day 2 练习验收：{文件路径.name}", C.CYAN)
    打印(f"{'='*60}\n", C.CYAN)
    
    if not 文件路径.exists():
        打印(f"❌ 文件不存在：{文件路径}", C.RED)
        打印(f"   请创建 {文件路径.name}，或指定正确路径：", C.YELLOW)
        打印(f"   python day02_practice_validator.py --file your_file.py", C.YELLOW)
        return 0
    
    # 读取代码
    with open(文件路径, "r", encoding="utf-8") as f:
        代码 = f.read()
    
    # 代码静态检查
    检查项 = [
        ("Pydantic 导入", 检查_pydantic导入),
        ("Pydantic Schema 定义", 检查_pydantic_schema),
        ("@工具 装饰器实现", 检查_装饰器定义),
        ("@functools.wraps 使用", 检查_functools_wraps),
        ("工具注册机制", 检查_工具注册机制),
        ("至少 3 个注册工具", 检查_至少3个工具),
        ("类型注解", 检查_类型注解),
        ("输入/输出验证", 检查_输入输出验证),
    ]
    
    分数 = 0
    满分 = len(检查项) * 10 + 20  # 静态 80 分 + 运行 20 分
    
    for 名称, 检查函数 in 检查项:
        通过, 消息 = 检查函数(代码)
        打印(f"  [{名称}]", C.BLUE)
        if 通过:
            打印(f"  {消息}", C.GREEN)
            分数 += 10
        else:
            打印(f"  {消息}", C.RED)
    
    # 运行检查
    打印(f"\n  [代码可运行性]", C.BLUE)
    通过, 消息 = 检查_代码可运行(文件路径)
    if 通过:
        打印(f"  {消息}", C.GREEN)
        分数 += 10
    else:
        打印(f"  {消息}", C.RED)
    
    # 工具注册表检查
    打印(f"\n  [工具注册表可用性]", C.BLUE)
    通过, 消息 = 检查_工具注册表可用(文件路径)
    if 通过:
        打印(f"  {消息}", C.GREEN)
        分数 += 10
    else:
        打印(f"  {消息}", C.YELLOW)
        分数 += 5  # 部分分数
    
    # ==================== 评分 ====================
    打印(f"\n{'='*60}", C.CYAN)
    颜色 = C.GREEN if 分数 >= 80 else (C.YELLOW if 分数 >= 60 else C.RED)
    打印(f"  总分：{分数}/{满分}", 颜色)
    
    if 分数 >= 80:
        打印(f"  🎉 验收通过！你的代码质量很好！", C.GREEN)
    elif 分数 >= 60:
        打印(f"  ⚠️ 基本通过，但还有改进空间（建议 80+ 分再继续）", C.YELLOW)
    else:
        打印(f"  ❌ 还需要努力，请参考上面的提示改进", C.RED)
    
    打印(f"{'='*60}\n", C.CYAN)
    
    # 改进建议
    if 分数 < 80:
        打印("📋 改进建议：", C.YELLOW)
        if not 检查_pydantic导入(代码)[0]:
            打印("  • 导入 pydantic：from pydantic import BaseModel, Field", C.YELLOW)
        if not 检查_functools_wraps(代码)[0]:
            打印("  • 装饰器内部必须加 @functools.wraps(func)", C.YELLOW)
        if not 检查_至少3个工具(代码)[0]:
            打印("  • 用 @工具 装饰器注册至少 3 个工具函数", C.YELLOW)
        if not 检查_输入输出验证(代码)[0]:
            打印("  • 在装饰器的包装函数内用 Pydantic 模型验证输入/输出", C.YELLOW)
        print()
    
    return 分数


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Day 2 练习验收脚本")
    parser.add_argument("--file", default=DEFAULT_FILENAME, help=f"练习文件路径（默认：{DEFAULT_FILENAME}）")
    args = parser.parse_args()
    
    文件路径 = Path(args.file)
    分数 = 验收(文件路径)
    sys.exit(0 if 分数 >= 80 else 1)


if __name__ == "__main__":
    main()
