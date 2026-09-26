"""
============================================================
真实 LLM API 实战教程（OpenAI 兼容：DeepSeek / Qwen / Moonshot…）
============================================================
目标：把 Day 4/6 的 mock 换成真实 API，打通"练习 → 实战"的最后一公里

运行方式：python tutorial_03_real_api.py
环境要求：Python 3.11+，pip install aiohttp

API Key（可选：没有 Key 也能学第 1-3 步，配好后运行可看全部 8 步）：
    申请地址：https://platform.deepseek.com （有免费额度）
    配置方式——设置环境变量（推荐，永远不要把 Key 写进代码！）：
      Windows PowerShell:  $env:DEEPSEEK_API_KEY = "sk-..."
      Windows CMD:         set DEEPSEEK_API_KEY=sk-...
      macOS / Linux:       export DEEPSEEK_API_KEY=sk-...
    也兼容 OPENAI_API_KEY / LLM_API_KEY 环境变量名。

⚠️ 安全三条铁律：
    1. Key 只放环境变量或 .env（.env 必须进 .gitignore）
    2. 报错信息里永远不要打印完整 Key（本教程会演示脱敏）
    3. 所有真实调用都要设 max_tokens 和超时，防止费用失控
============================================================
"""

import asyncio
import json
import os
import time

try:
    import aiohttp
except ImportError:
    aiohttp = None

BASE_URL = "https://api.deepseek.com"   # Qwen/Moonshot 等只需换这里的域名和模型名
MODEL = "deepseek-chat"

# 全局成本统计（第 8 步汇总）
usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}


def 分隔线(标题):
    print("\n" + "=" * 60)
    print(标题)
    print("=" * 60)


def 找key() -> str:
    """按优先级找 API Key——第 1 步的核心：Key 只从环境变量来"""
    for 名称 in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"):
        值 = os.environ.get(名称, "").strip()
        if 值:
            return 值
    return ""


def 脱敏(key: str) -> str:
    """打印时永远脱敏：sk-ab****yz"""
    if len(key) <= 8:
        return "****"
    return f"{key[:5]}****{key[-4:]}"


# ==================== 请求/解析（离线部分也能学） ====================

def 构造请求体(messages, tools=None, stream=False, max_tokens=512):
    """第 2 步：OpenAI 兼容的请求体结构——每个字段都要认识"""
    body = {
        "model": MODEL,
        "messages": messages,          # 对话历史：system/user/assistant/tool
        "max_tokens": max_tokens,      # 必设！防止费用失控
        "temperature": 0.7,
        "stream": stream,
    }
    if tools:
        body["tools"] = tools          # Function Calling：告诉 LLM 有哪些工具
    return body


def 解析响应(resp_json):
    """第 3 步：从响应 JSON 里取出回答和 token 用量"""
    message = resp_json["choices"][0]["message"]
    usage = resp_json.get("usage", {})
    return message, usage


async def call_llm(session, messages, tools=None, stream=False, max_tokens=512, 轮次说明=""):
    """第 3+4 步：带完整错误处理的 LLM 调用（超时/状态码/重试/退避）"""
    body = 构造请求体(messages, tools=tools, stream=stream, max_tokens=max_tokens)
    headers = {"Authorization": f"Bearer {找key()}", "Content-Type": "application/json"}

    最大重试 = 2
    last_err = None
    for attempt in range(最大重试 + 1):
        try:
            async with asyncio.timeout(20):   # 每次请求都有超时
                async with session.post(
                    f"{BASE_URL}/chat/completions", json=body, headers=headers
                ) as resp:
                    # HTTP 状态码分诊：不同错误不同处理
                    if resp.status == 401:
                        raise RuntimeError("401：API Key 无效或过期，请检查环境变量")
                    if resp.status == 429:
                        raise RuntimeError("429：触发限流，需要退避后重试")
                    if resp.status >= 500:
                        raise RuntimeError(f"{resp.status}：服务端暂时故障，重试即可")
                    if resp.status != 200:
                        text = await resp.text()
                        raise RuntimeError(f"{resp.status}：未知错误 {text[:200]}")

                    if stream:
                        return await 解析流式响应(resp)

                    resp_json = await resp.json()
                    # 容错：服务端偶尔返回不完整 JSON 结构，逐层 .get 而不是裸下标
                    if "choices" not in resp_json:
                        raise RuntimeError(f"响应缺少 choices 字段：{str(resp_json)[:200]}")
                    return resp_json

        except RuntimeError as e:
            last_err = e
            可重试 = "429" in str(e) or "500" in str(e) or "缺少 choices" in str(e)
            print(f"  ⚠️ {轮次说明}第 {attempt + 1} 次尝试失败：{e}")
            if not 可重试 or attempt == 最大重试:
                break
            等待 = 2 ** attempt          # 指数退避：1s → 2s → 4s
            print(f"  ⏳ {等待}s 后重试（指数退避）...")
            await asyncio.sleep(等待)
        except asyncio.TimeoutError:
            last_err = RuntimeError("请求超时")
            print(f"  ⚠️ {轮次说明}第 {attempt + 1} 次尝试超时")
            if attempt == 最大重试:
                break
            await asyncio.sleep(2 ** attempt)
        except aiohttp.ClientError as e:
            last_err = RuntimeError(f"网络错误：{type(e).__name__}")
            print(f"  ⚠️ {轮次说明}网络错误：{e}")
            if attempt == 最大重试:
                break
            await asyncio.sleep(2 ** attempt)

    raise last_err or RuntimeError("调用失败")


async def 解析流式响应(resp):
    """第 7 步：SSE 格式逐行解析——每个 chunk 是一行 data: {...}"""
    full = ""
    usage = {}
    print("  助手（流式）：", end="", flush=True)
    async for raw in resp.content:
        line = raw.decode("utf-8").strip()
        if not line.startswith("data:"):
            continue                    # SSE 还有 event:/retry: 等行，只关心 data:
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            break                       # 流结束的哨兵
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue                    # 半行/脏数据直接跳过，不让解析失败打断流
        if chunk.get("usage"):
            usage = chunk["usage"]      # stream_options 包含 usage 时在最后的 chunk 里
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        piece = delta.get("content") or ""
        if piece:
            full += piece
            print(piece, end="", flush=True)
    print()
    return {"choices": [{"message": {"role": "assistant", "content": full}}], "usage": usage}


def 记账(usage):
    usage_total["calls"] += 1
    usage_total["prompt_tokens"] += usage.get("prompt_tokens", 0)
    usage_total["completion_tokens"] += usage.get("completion_tokens", 0)


# ==================== 8 个步骤 ====================

def 第1步_key管理():
    分隔线("第 1 步：API Key 的正确管理")
    key = 找key()
    if key:
        print(f"  ✅ 从环境变量读到 Key：{脱敏(key)}")
    else:
        print("  ⚠️ 未检测到 API Key（DEEPSEEK_API_KEY / OPENAI_API_KEY / LLM_API_KEY）")
    print("  💡 铁律：Key 只放环境变量；打印/报错一律脱敏；.env 必须进 .gitignore")


def 第2步_构造请求():
    分隔线("第 2 步：构造第一个真实请求")
    messages = [
        {"role": "system", "content": "你是一个简洁的助手。"},
        {"role": "user", "content": "用一句话介绍 Python 的 asyncio。"},
    ]
    print(json.dumps(构造请求体(messages), ensure_ascii=False, indent=2))
    print("  💡 认识每个字段：model 选模型、messages 是全部上下文、")
    print("     max_tokens 封顶输出、temperature 控制随机性")


def 第3步_离线解析演示():
    print("\n【第 3 步（离线演示）：解析一个真实格式的响应】")
    样例 = {
        "choices": [{"message": {"role": "assistant", "content": "asyncio 是 Python 的异步 IO 框架。"}}],
        "usage": {"prompt_tokens": 21, "completion_tokens": 12},
    }
    message, usage = 解析响应(样例)
    print(f"  回答：{message['content']}")
    print(f"  用量：prompt {usage['prompt_tokens']} + completion {usage['completion_tokens']} tokens")
    记账(usage)


async def 第3步_发送请求(session):
    分隔线("第 3 步：发送第一个真实请求")
    messages = [
        {"role": "system", "content": "你是一个简洁的助手。"},
        {"role": "user", "content": "用一句话介绍 Python 的 asyncio。"},
    ]
    resp_json = await call_llm(session, messages, 轮次说明="第3步 ")
    message, usage = 解析响应(resp_json)
    记账(usage)
    print(f"  ✅ 回答：{message['content']}")
    print(f"  💰 用量：prompt {usage.get('prompt_tokens')} + completion {usage.get('completion_tokens')} tokens")


async def 第4步_错误处理(session):
    分隔线("第 4 步：错误处理四件套（超时/状态码/重试/退避）")
    print("  上一条的调用已经带全了这四件套（见 call_llm 源码）：")
    print("  ① asyncio.timeout(20) 每次请求都有超时")
    print("  ② 状态码分诊：401 不重试（Key 错）、429/5xx 重试、其他报错")
    print("  ③ 指数退避重试：1s → 2s，最多 2 次")
    print("  ④ JSON/结构容错：响应缺字段时不裸下标崩溃")
    print("  现在故意用错误的 Key 调用，看 401 分诊：")
    try:
        async with asyncio.timeout(20):
            async with session.post(
                f"{BASE_URL}/chat/completions",
                json=构造请求体([{"role": "user", "content": "hi"}]),
                headers={"Authorization": "Bearer sk-wrong-key", "Content-Type": "application/json"},
            ) as resp:
                if resp.status == 401:
                    print("  ✅ 收到 401——Key 无效时不重试，直接提示用户检查配置")
                else:
                    print(f"  ℹ️ 收到状态码 {resp.status}")
    except Exception as e:
        print(f"  ℹ️ 网络不通（{type(e).__name__}）——线上环境这会被 call_llm 的重试兜住")


async def 第5步_多轮对话(session):
    分隔线("第 5 步：多轮对话——上下文就是 messages 列表")
    messages = [
        {"role": "system", "content": "你是一个简洁的助手。"},
    ]
    messages.append({"role": "user", "content": "我叫小张，我最喜欢的数字是 42。"})
    resp = await call_llm(session, messages, max_tokens=256, 轮次说明="第5步-1 ")
    记账(解析响应(resp)[1])
    print(f"  助手：{解析响应(resp)[0]['content'][:60]}")

    messages.append({"role": "assistant", "content": 解析响应(resp)[0]["content"]})
    messages.append({"role": "user", "content": "我叫什么名字？最喜欢的数字是多少？"})
    resp = await call_llm(session, messages, max_tokens=256, 轮次说明="第5步-2 ")
    message, usage = 解析响应(resp)
    记账(usage)
    print(f"  助手：{message['content'][:80]}")
    print("  💡 答对了——因为历史里带着第一轮的 user 消息。上下文 = 你给它的列表")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行四则运算，输入四则运算表达式字符串",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "如 '3 + 5 * 2'"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
]


def 执行工具(name, arguments):
    """本地执行工具——和 Day 4/6 的注册表一个道理，这里直接 if/else"""
    if name == "calculator":
        try:
            return str(eval(arguments["expression"], {"__builtins__": {}}, {}))
        except Exception as e:
            return f"错误: {e}"
    if name == "get_weather":
        return {"北京": "晴 25°C"}.get(arguments.get("city", ""), "天气未知")
    return f"未知工具 {name}"


async def 第6步_FunctionCalling(session):
    分隔线("第 6 步：真实 Function Calling（Day 4 的真实版）")
    messages = [{"role": "user", "content": "帮我计算 3 + 5 * 2 等于多少？"}]

    for 轮 in range(3):                      # 有上限，防费用失控
        resp = await call_llm(session, messages, tools=TOOLS, max_tokens=512,
                              轮次说明=f"第6步-轮{轮 + 1} ")
        message, usage = 解析响应(resp)
        记账(usage)

        if not message.get("tool_calls"):
            print(f"  ✅ 最终回答：{message['content']}")
            return

        messages.append(message)             # assistant 的 tool_calls 也要回填历史
        for tc in message["tool_calls"]:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])   # arguments 是 JSON 字符串！
            result = 执行工具(name, args)
            print(f"  🔧 第 {轮 + 1} 轮 LLM 要求调用 {name}({args}) → {result}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    print("  ⚠️ 达到最大轮数，停止（真实项目同样要设上限）")


async def 第7步_流式输出(session):
    分隔线("第 7 步：流式输出——打字机效果的真实实现")
    messages = [{"role": "user", "content": "用三句话介绍 AI Agent。"}]
    body = 构造请求体(messages, stream=True, max_tokens=256)
    body["stream_options"] = {"include_usage": True}   # 让最后一块带 usage
    headers = {"Authorization": f"Bearer {找key()}", "Content-Type": "application/json"}
    async with asyncio.timeout(30):
        async with session.post(f"{BASE_URL}/chat/completions", json=body,
                                headers=headers) as resp:
            result = await 解析流式响应(resp)
    记账(result["usage"])
    print("  💡 逐 chunk 到达就逐 chunk 打印——ChatGPT 的打字机效果就是这个原理")


def 第8步_成本汇总():
    分隔线("第 8 步：成本统计——每次调用都要记账")
    p, c = usage_total["prompt_tokens"], usage_total["completion_tokens"]
    print(f"  本次教程共调用 {usage_total['calls']} 次 LLM")
    print(f"  Token：prompt {p} + completion {c} = {p + c}")
    print("  💡 生产做法：每次调用记录 usage 入库/日志，设日预算告警")


# ==================== 主流程 ====================

async def main():
    print("=" * 60)
    print("真实 LLM API 实战教程（tutorial_03）")
    print("=" * 60)

    第1步_key管理()
    第2步_构造请求()

    key = 找key()
    if aiohttp is None:
        print("\n❌ 缺少 aiohttp：pip install aiohttp （装好后重跑本教程）")
        return
    if not key:
        第3步_离线解析演示()
        第8步_成本汇总()
        print("\n" + "=" * 60)
        print("📌 以上是离线部分。配置环境变量 DEEPSEEK_API_KEY 后重新运行，")
        print("   即可体验第 3-7 步：真实调用 / 错误重试 / 多轮对话 /")
        print("   Function Calling / 流式输出（有免费额度，本教程消耗很小）")
        print("=" * 60)
        return

    timeout = aiohttp.ClientTimeout(total=None)   # 每个请求内部已有 asyncio.timeout
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await 第3步_发送请求(session)
            await 第4步_错误处理(session)
            await 第5步_多轮对话(session)
            await 第6步_FunctionCalling(session)
            await 第7步_流式输出(session)
    except RuntimeError as e:
        print(f"\n⚠️ API 调用中断：{e}")
        print("💡 这正是第 4 步教的内容——检查 Key / 网络 / 额度后重跑即可")
    except Exception as e:
        print(f"\n⚠️ 网络异常：{type(e).__name__}: {e}")
        print("💡 检查网络 / 代理后重跑；离线部分（第 1-3 步）不受影响")

    第8步_成本汇总()
    print("\n🎉 学完本教程，你已经具备把 Day 4-10 的 mock 全部换成真实 API 的能力")
    print("   下一步：Day 11-15 项目实战（见 index.html 路线图）")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 已中断")
