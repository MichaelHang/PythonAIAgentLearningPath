"""
Day 9 练习：实现带记忆和 RAG 的 Agent
验收标准：
1. 实现了短期记忆（最近 N 轮对话历史）
2. 对话历史超出限制时有裁剪策略
3. 实现了长期记忆 / RAG（向量检索）
4. 能对新输入做语义检索，找到相关历史/文档
5. 多轮对话：Agent 能"记住"之前说过的话

安装依赖：
    pip install chromadb sentence-transformers
    # 或者
    pip install faiss-cpu numpy
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# ==================== 任务 1：实现短期记忆（对话历史） ====================

@dataclass
class ConversationMessage:
    """对话消息"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    timestamp: float = field(default_factory=lambda: __import__("time").time())


class ShortTermMemory:
    """
    短期记忆管理器
    
    需求：
    1. 存储最近 N 条消息（默认 20 条）
    2. 超出限制时自动裁剪最早的消息
    3. 可以在 messages 和格式化文本之间转换
    4. 保留 system message 不被裁剪
    """
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[ConversationMessage] = []
    
    def add(self, role: str, content: str):
        """添加消息"""
        # TODO 1.1：实现添加消息
        # 提示：
        # 1. 创建 ConversationMessage
        # 2. 追加到列表
        # 3. 如果超出限制，裁剪（但保留 system message）
        pass
    
    def get_recent(self, n: Optional[int] = None) -> List[ConversationMessage]:
        """获取最近 N 条消息"""
        # TODO 1.2：实现获取消息
        pass
    
    def to_api_format(self) -> List[Dict]:
        """转换为 LLM API 格式"""
        # TODO 1.3：实现格式转换
        # [{"role": "user", "content": "..."}, ...]
        pass
    
    def clear(self):
        """清除历史（保留 system message）"""
        # TODO 1.4：实现清除
        pass


# ==================== 任务 2：实现长期记忆 / 向量存储 ====================

class VectorStore(ABC):
    """向量存储抽象类"""
    
    @abstractmethod
    def add(self, text: str, metadata: Optional[Dict] = None):
        """添加文本到向量存储"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, Dict, float]]:
        """搜索最相关的文本，返回 (文本, 元数据, 相似度)"""
        pass


class SimpleVectorStore(VectorStore):
    """
    简单的向量存储（不依赖外部库，用于学习）
    
    使用方式：
    1. 存储（文本, 向量, 元数据）
    2. 检索时计算相似度（cosine similarity）
    
    正式项目请用 ChromaDB 或 FAISS
    """
    
    def __init__(self):
        self.documents: List[Tuple[str, List[float], Dict]] = []
    
    def add(self, text: str, metadata: Optional[Dict] = None, embedding: Optional[List[float]] = None):
        """添加文本"""
        # TODO 2.1：实现添加
        # 提示：先存文本，embedding 可以后续计算
        pass
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, Dict, float]]:
        """搜索最相关的文本（基于关键词匹配的简单实现）"""
        # TODO 2.2：实现简单搜索
        # 提示：
        # 简单版：基于关键词重叠度打分
        # 正式版：用 embedding + cosine similarity
        pass


def simple_keyword_search(query: str, documents: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
    """简单的关键词搜索（不依赖 embedding 模型）"""
    query_words = set(query.lower().split())
    
    scores = []
    for doc in documents:
        doc_words = set(doc.lower().split())
        # Jaccard 相似度
        intersection = len(query_words & doc_words)
        union = len(query_words | doc_words)
        score = intersection / union if union > 0 else 0
        scores.append((doc, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# ==================== 任务 3：实现 RAG 检索模块 ====================

class RAGRetriever:
    """
    RAG 检索器
    
    流程：
    1. 知识库管理：添加文档
    2. 检索：根据用户问题，找到最相关的知识片段
    3. 返回检索结果供 LLM 使用
    """
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.knowledge_base: List[str] = []
    
    def add_knowledge(self, text: str):
        """添加知识到知识库"""
        # TODO 3.1：实现知识添加
        pass
    
    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        检索相关知识
        
        返回：格式化的知识文本（可直接拼接到 Prompt）
        """
        # TODO 3.2：实现检索
        # 提示：
        # 1. 搜索知识库
        # 2. 格式化结果
        # 3. 返回拼接后的文本
        pass


# ==================== 任务 4：实现带记忆的 Agent ====================

class MemoryAgent:
    """
    带记忆的 AI Agent
    
    组件：
    - ShortTermMemory：短期对话历史
    - RAGRetriever：长期记忆/知识检索
    - 工具系统：和之前一样
    
    每次对话时：
    1. 检索相关记忆/知识
    2. 将检索结果注入 System Prompt
    3. 处理用户输入
    4. 更新短期记忆
    """
    
    def __init__(self):
        self.short_memory = ShortTermMemory(max_messages=20)
        self.vector_store = SimpleVectorStore()
        self.rag = RAGRetriever(self.vector_store)
        
        # 添加一些初始知识
        self.rag.add_knowledge("Python 是一种高级编程语言，广泛用于 AI 开发。")
        self.rag.add_knowledge("AI Agent 是一种能自主决策的智能体，核心是 ReAct 循环。")
        self.rag.add_knowledge("LangGraph 是 LangChain 的图工作流框架，用于构建 AI Agent。")
    
    async def chat(self, user_input: str) -> str:
        """处理用户输入，返回回答"""
        # TODO 4.1：实现带记忆的对话
        # 流程：
        # 1. 检索相关知识（RAG）
        # 2. 构建 System Prompt（包含相关知识）
        # 3. 构建 Messages（短期记忆 + 当前输入）
        # 4. 调用 LLM（先用模拟）
        # 5. 将回答加入短期记忆
        # 6. 返回回答
        pass
    
    def remember_fact(self, fact: str):
        """记住一个事实（长期记忆）"""
        self.rag.add_knowledge(fact)


# ==================== 任务 5：实现上下文窗口管理 ====================

def compress_conversation(
    messages: List[ConversationMessage],
    max_tokens: int = 4000,
) -> List[ConversationMessage]:
    """
    对话压缩策略
    
    当对话历史超出 token 限制时：
    1. 方案 A：滑动窗口（只保留最近 N 轮）
    2. 方案 B：摘要压缩（调用 LLM 将历史总结为一段话）
    3. 方案 C：智能裁剪（保留关键信息，丢弃冗余）

    这里实现最简单的方案 A
    """
    # TODO 5.1：实现对话压缩
    # 提示：
    # 1. 估算每条消息的 token 数（粗略：1 个中文字 ≈ 2 tokens）
    # 2. 从最新消息开始往前保留
    # 3. 确保 system message 不被丢弃
    pass


# ==================== 主函数：测试 ====================

async def main():
    print("=" * 60)
    print("Day 9 练习：记忆系统 + RAG")
    print("=" * 60)
    
    # 测试 1：短期记忆
    print("\n📝 测试 1：短期记忆（添加 + 裁剪）")
    memory = ShortTermMemory(max_messages=5)
    memory.add("system", "你是一个 AI 助手")
    memory.add("user", "我叫张三")
    memory.add("assistant", "你好张三！")
    memory.add("user", "Python 是什么？")
    memory.add("assistant", "Python 是一种编程语言。")
    memory.add("user", "它难学吗？")  # 触发裁剪
    
    消息 = memory.to_api_format()
    print(f"  存储了 {len(memory.messages)} 条消息")
    for m in 消息:
        print(f"    [{m['role']}] {m['content'][:40]}...")
    
    # 测试 2：关键词搜索
    print("\n📝 测试 2：关键词搜索")
    docs = ["Python 编程", "AI Agent 开发", "天气查询", "LangGraph 框架"]
    results = simple_keyword_search("Python Agent 开发", docs, top_k=3)
    for doc, score in results:
        print(f"  📄 {doc}: 相似度 {score:.2f}")
    
    # 测试 3：RAG 检索
    print("\n📝 测试 3：RAG 检索")
    retriever = RAGRetriever(SimpleVectorStore())
    retriever.add_knowledge("Python 是 AI 开发的主力语言")
    retriever.add_knowledge("AI Agent 的核心是 ReAct 循环")
    retriever.add_knowledge("今天北京天气晴朗")
    
    result = retriever.retrieve("AI Agent 的核心是什么？", top_k=2)
    print(f"  检索结果：\n{result}")
    
    # 测试 4：多轮对话记忆
    print("\n📝 测试 4：多轮对话记忆")
    agent = MemoryAgent()
    
    response = await agent.chat("我叫张三，我喜欢 Python")
    print(f"  用户：我叫张三，我喜欢 Python")
    print(f"  助手：{response}")
    
    response = await agent.chat("我叫什么名字？我喜欢什么？")
    print(f"\n  用户：我叫什么名字？我喜欢什么？")
    print(f"  助手：{response}")
    print(f"\n  注：如果 Agent 答对了，说明记忆系统正常工作 ✅")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！现在运行 python day09_practice_validator.py 验收")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
