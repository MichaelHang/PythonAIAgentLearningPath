# 智能开发助手 Agent —— 项目脚手架（Day 11-15）

这是 15 天路线图**阶段三**的起点：一个分层清晰的 FastAPI 项目骨架，TODO 已经标好，
Day 11-15 的所有开发都在这个目录里进行。

## 使用方式

```bash
# 0. 建议把本目录复制一份作为你的项目根目录（保留本仓库原样作参考）
#    以下命令都在 project_day11_15/ 目录下执行

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 Key（永远用环境变量，不要写进代码）
#    Windows PowerShell:  $env:DEEPSEEK_API_KEY = "sk-..."
#    macOS / Linux:       export DEEPSEEK_API_KEY=sk-...
#    也可以复制 .env.example 为 .env 自行加载

# 3. 启动开发服务器（在项目根目录运行）
uvicorn app.main:app --reload

# 4. 测试接口
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s1", "message": "帮我计算 3 + 5 * 2"}'

# 交互式 API 文档：浏览器打开 http://127.0.0.1:8000/docs
```

## 目录结构（为什么这样分层）

```
app/
├── main.py      # FastAPI 路由层：只做 HTTP ↔ 内部转换，保持"薄"
├── schemas.py   # 请求/响应模型（Pydantic）：API 的契约
├── agent.py     # Agent 核心循环：业务层（Day 4/6/9 的服务化组装）
├── tools.py     # 工具系统：注册表 + 内置工具（Day 2/8 模式）
├── memory.py    # 会话记忆：session_id → 会话隔离（Day 9 服务化）
├── llm.py       # LLM 客户端：外部服务适配层——换供应商只改这里
└── config.py    # 配置中心：环境变量单点读取
```

分层的好处：路由层薄到可以直接读懂数据流向；业务逻辑可以脱离 HTTP 单测；
换 LLM 供应商（DeepSeek → Qwen → 本地模型）只动 `llm.py` 一个文件。

## 每天的任务

| 天 | 内容 | 对应 TODO |
|---|---|---|
| Day 11 | 架构理解 + FastAPI 搭建 + Agent 核心循环 | `schemas.py` / `agent.py` / `main.py` |
| Day 12 | 工具系统完善 + 会话记忆 + 错误处理 | `tools.py` / `memory.py` |
| Day 13 | Web UI + SSE 流式 | `main.py` TODO 6.x（`llm.chat_stream` 和 `static/index.html` 已提供） |
| Day 14 | pytest 测试 + Docker 部署 | `tests/`（`test_memory/test_tools/test_api`）+ `Dockerfile` |
| Day 15 | 文档 + 收尾 | 更新本 README |

## 设计约定（改代码前先读）

1. **Key 只从 `config.py` 来**——任何模块不要直接 `os.environ`
2. **路由层不做业务**——`main.py` 里不写 Agent 逻辑
3. **工具执行走注册表**——`agent.py` 不要绕过 `tools.py` 直接调函数
4. **错误处理三层**：LLM 超时重试在 `llm.py`、工具失败作为 Observation 回传在 `agent.py`、
   统一 HTTP 错误响应在 `main.py`
5. **单进程够用**：`memory.py` 用进程内字典；真要多进程部署时换成 Redis（README 层面了解即可）
