"""LLM 客户端：外部服务适配层——换供应商（Qwen/Moonshot/本地模型）只改这个文件

这是 tutorial_03_real_api.py 的浓缩服务版：超时 / 状态码分诊 / 指数退避重试。
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp

from . import config


class LLMError(RuntimeError):
    """LLM 调用失败（重试后仍失败 / 配置缺失）——调用方应捕获并降级"""


async def chat(
    messages: List[Dict],
    tools: Optional[List[Dict]] = None,
    max_tokens: Optional[int] = None,
) -> Dict:
    """调用 /chat/completions，返回完整响应 JSON

    抛出：LLMError（重试后仍失败时）
    """
    if not config.DEEPSEEK_API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY 环境变量（参考项目 README 的配置方式）")

    body: Dict[str, Any] = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens or config.LLM_MAX_TOKENS,
        "temperature": 0.7,
    }
    if tools:
        body["tools"] = tools

    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    最大重试 = 2
    last_err: Optional[Exception] = None
    for attempt in range(最大重试 + 1):
        try:
            async with asyncio.timeout(config.LLM_TIMEOUT):
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{config.LLM_BASE_URL}/chat/completions",
                        json=body,
                        headers=headers,
                    ) as resp:
                        if resp.status == 401:
                            raise LLMError("401：API Key 无效或过期（此错误不重试）")
                        if resp.status == 429:
                            raise RuntimeError("429：触发限流")
                        if resp.status >= 500:
                            raise RuntimeError(f"{resp.status}：服务端故障")
                        if resp.status != 200:
                            text = await resp.text()
                            raise LLMError(f"{resp.status}：{text[:200]}")
                        resp_json = await resp.json()
                        if "choices" not in resp_json:
                            raise RuntimeError(f"响应缺少 choices：{str(resp_json)[:200]}")
                        return resp_json

        except LLMError:
            raise  # 配置类错误不重试，直接上抛
        except (RuntimeError, asyncio.TimeoutError, aiohttp.ClientError) as e:
            last_err = e if isinstance(e, LLMError) else LLMError(str(e))
            if attempt < 最大重试:
                await asyncio.sleep(2 ** attempt)  # 指数退避：1s → 2s

    raise last_err or LLMError("LLM 调用失败")


def 取回答(resp_json: Dict) -> str:
    """从响应 JSON 中取 assistant 文本回答"""
    return resp_json["choices"][0]["message"].get("content") or ""


async def chat_stream(messages: List[Dict], max_tokens: Optional[int] = None):
    """流式调用（Day 13 提供）：逐 chunk yield 文本片段

    SSE 解析规则（和 tutorial_03 第 7 步相同）：
    - 响应是一行行 "data: {...}"，最后一行 "data: [DONE]" 表示结束
    - 每行解析出 choices[0].delta.content 就是增量文本
    """
    if not config.DEEPSEEK_API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY 环境变量（参考项目 README 的配置方式）")

    body = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens or config.LLM_MAX_TOKENS,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    async with asyncio.timeout(config.LLM_TIMEOUT):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.LLM_BASE_URL}/chat/completions", json=body, headers=headers
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMError(f"{resp.status}：{text[:200]}")
                async for raw in resp.content:
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    piece = chunk.get("choices", [{}])[0].get("delta", {}).get("content") or ""
                    if piece:
                        yield piece
