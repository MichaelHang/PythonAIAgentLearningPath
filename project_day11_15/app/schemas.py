"""API 的请求/响应模型（Pydantic）——这是 HTTP 层的契约"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat 的请求体"""

    session_id: str = Field("default", description="会话 ID：同一 ID 共享对话记忆")
    message: str = Field(..., min_length=1, description="用户输入")


class ChatResponse(BaseModel):
    """POST /chat 的响应体"""

    session_id: str
    answer: str = Field(..., description="Agent 的最终回答")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="本次回答经过的工具调用记录（用于前端展示思考过程）"
    )


# TODO 1.1：定义 ToolCallRecord 模型并让 ChatResponse.tool_calls 使用它
#   字段建议：tool_name / arguments / output / success
#   好处：前端可以展示 Agent 的"思考过程"（Day 13 会用）
class ToolCallRecord(BaseModel):
    pass


# TODO 1.2：定义 ErrorResponse 模型（code + message），在 main.py 的统一错误处理中使用
