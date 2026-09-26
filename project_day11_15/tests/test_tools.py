"""Day 14：工具系统测试——注册、执行出口、路径安全边界"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import config
from app.tools import TOOLS_REGISTRY, execute_tool, get_tool_list, _安全路径


def test_注册后工具可见():
    # TODO 7.1（Day 12 完成后自动通过）：calculator 应出现在注册表
    assert "calculator" in TOOLS_REGISTRY


def test_get_tool_list格式():
    tools = get_tool_list()
    assert isinstance(tools, list) and len(tools) >= 1
    fn = tools[0]["function"]
    assert fn["name"] and fn["description"] and "properties" in fn["parameters"]


def test_execute_tool计算():
    assert "13" in execute_tool("calculator", {"expression": "3 + 5 * 2"})


def test_execute_tool_未知工具不崩溃():
    out = execute_tool("不存在的工具xyz", {})
    assert "错误" in out or "未注册" in out


def test_安全路径_拒绝越界():
    with pytest.raises(PermissionError):
        _安全路径("../../etc/passwd")


def test_安全路径_接受界内路径():
    p = _安全路径("notes/a.md")
    assert config.WORKSPACE_DIR in str(p) or str(p).startswith(str(Path(config.WORKSPACE_DIR).resolve()))
