"""FastAPI 入口：路由层只做 HTTP ↔ 内部转换，业务逻辑都在 agent.py（保持"薄"）

启动方式（在 project_day11_15 目录下）：
    uvicorn app.main:app --reload
交互式文档：
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from . import llm
from .agent import run_agent
from .llm import LLMError
from .memory import MEMORY
from .schemas import ChatRequest, ChatResponse

app = FastAPI(title="智能开发助手 Agent", version="0.1.0")


@app.get("/health")
def health():
    """健康检查（已实现，作为路由层写法的参考）"""
    return {"status": "ok", "sessions": len(MEMORY._sessions)}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # TODO 5.1：调用 run_agent 并包装为 ChatResponse
    #   1. result = await run_agent(req.session_id, req.message)
    #   2. return ChatResponse(session_id=..., answer=..., tool_calls=...)
    # TODO 5.2：统一错误处理
    #   - llm.LLMError → raise HTTPException(status_code=503, detail=str(e))
    #   - 其他异常 → HTTPException(500, ...)（不要把原始 traceback 泄露给客户端）
    raise NotImplementedError("TODO 5.1/5.2：实现 /chat 路由")


# ==================== Day 13：SSE 流式接口 ====================
#
# TODO 6.1：实现 POST /chat/stream（SSE 流式，前端 static/index.html 已写好对应解析）
#
#   参考流程（写成一个异步生成器函数，交给 StreamingResponse）：
#   1. 先复用 run_agent 拿到最终回答与工具调用记录
#      （工具轮次用非流式调用——需要解析 tool_calls；最终回答才流式）
#   2. 按 SSE 格式逐条发给前端（注意：每个 data 行的结尾要有两个换行符）：
#        工具事件：data: {"type": "tool", "name": "...", "output": "..."}
#        回答片段：data: {"type": "answer", "content": "..."}
#        结束哨兵：data: [DONE]
#   3. 把生成器交给：
#        return StreamingResponse(生成器, media_type="text/event-stream")
#
#   提示：事件用 JSON 编码时用 json.dumps(..., ensure_ascii=False)；
#         生成器里不要 print（会把调试信息混进 SSE 流）。
#
# @app.post("/chat/stream")
# async def chat_stream(req: ChatRequest):
#     ...


# TODO 6.2：挂载静态页面（前端聊天界面，文件已给好）
#   from fastapi.staticfiles import StaticFiles
#   app.mount("/static", StaticFiles(directory="static"), name="static")
#   然后浏览器访问 http://127.0.0.1:8000/static/index.html
#   （前后端同源部署，天然没有 CORS 问题——这也是不用跨域 EventSource 方案的原因之一）
