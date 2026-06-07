"""
Day 7 练习：用 LangGraph 实现带条件分支的 ReAct Agent
验收标准：
1. 使用 StateGraph 定义 Agent 状态
2. 定义了至少 2 个 Node（call_model、call_tool）
3. 使用了 add_conditional_edges（条件路由）
4. State 类型用 TypedDict 或 Pydantic 模型定义
5. Agent 能完成多步推理（和 Day 6 功能相同，但用 LangGraph 实现）
6. 能正确路由到 END（停止）或继续执行工具
7. 代码可运行

安装依赖：
    pip install langgraph langchain-openai
"""

import json
import asyncio
import functools
from typing import List, Dict, Any, TypedDict, Optional, Annotated, Literal
from typing import AsyncGenerator


# ==================== 任务 1：定义 State ====================

class AgentState(TypedDict):
    """
    Agent 状态定义
    
    需求：
    1. messages: 对话历史列表
    2. tool_calls: 当前轮的工具调用（可选）
    3. tool_results: 工具执行结果（可选）
    4. step_count: 已执行步数
    """
    # TODO 1.1：定义 AgentState 的字段
    # 提示：至少包含 messages（List[Dict]）和 step_count（int）
    pass


# ==================== 任务 2：实现工具系统（复用 Day 6 的） ====================

TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, parameters: Optional[Dict] = None):
    """工具注册装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        TOOLS_REGISTRY[name] = {
            "function": wrapper,
            "description": description,
            "parameters": parameters or {},
        }
        return wrapper
    return decorator


# TODO 2.1：注册工具
@tool("calculator", "执行四则运算", {
    "type": "object",
    "properties": {"expression": {"type": "string"}},
    "required": ["expression"]
})
def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误: {e}"


@tool("weather", "查询城市天气", {
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"]
})
def weather(city: str) -> str:
    数据 = {"北京": "晴 25°C", "上海": "多云 22°C"}
    return 数据.get(city, f"{city} 天气未知")


def get_tools_for_api() -> List[Dict]:
    """生成 OpenAI Function Calling 格式的工具列表"""
    # TODO 2.2：实现工具格式转换
    pass


def execute_tool(name: str, args: Dict) -> str:
    """执行单个工具"""
    # TODO 2.3：实现工具执行
    pass


# ==================== 任务 3：实现 "模拟 LLM 调用" Node ====================
# 提示：先用模拟数据跑通 LangGraph 流程，再换成真实 API
# 如果安装了 langchain-openai，可以直接用它

def mock_llm_response(messages: List[Dict], has_tools: bool = True) -> Dict:
    """
    模拟 LLM 响应（用于测试 LangGraph 流程）
    
    根据 messages 内容返回合适的响应：
    - 如果是首次对话且内容包含"计算"或"天气"，返回 tool_calls
    - 如果已经有工具结果，返回最终回答
    """
    user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_msg = msg["content"]
            break
    
    # 检查是否已经执行过工具（有 tool role 消息）
    has_tool_result = any(msg.get("role") == "tool" for msg in messages)
    
    if has_tool_result:
        # 已经有工具结果，生成最终回答
        return {
            "role": "assistant",
            "content": f"根据查询结果，我已经为您完成了计算。"
        }
    
    # 首次调用，可能需要工具
    if has_tools and "计算" in user_msg:
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_001",
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": json.dumps({"expression": "3+5*2"})
                    }
                }
            ]
        }
    
    if has_tools and "天气" in user_msg:
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_002",
                    "type": "function",
                    "function": {
                        "name": "weather",
                        "arguments": json.dumps({"city": "北京"})
                    }
                }
            ]
        }
    
    return {"role": "assistant", "content": "我是 AI 助手，有什么可以帮你的？"}


# ==================== 任务 4：定义 LangGraph Node ====================

def node_call_model(state: AgentState) -> Dict:
    """
    调用 LLM 模型的 Node
    
    需求：
    1. 从 state["messages"] 获取对话历史
    2. 调用 LLM（先用 mock）
    3. 将 LLM 响应追加到 messages
    4. 返回更新后的 state 字典
    
    返回格式：{"messages": [追加的消息], "step_count": state["step_count"] + 1}
    """
    # TODO 4.1：实现 call_model node
    # 提示：
    # 1. response = mock_llm_response(state["messages"])
    # 2. new_messages = state["messages"] + [response]
    # 3. return {"messages": new_messages, "step_count": state["step_count"] + 1}
    pass


def node_call_tool(state: AgentState) -> Dict:
    """
    执行工具的 Node
    
    需求：
    1. 从 state["messages"] 最后一条消息中获取 tool_calls
    2. 对每个 tool_call 执行对应的工具
    3. 将工具执行结果追加到 messages（role=tool）
    4. 返回更新后的 state 字典
    """
    # TODO 4.2：实现 call_tool node
    # 提示：
    # 1. last_msg = state["messages"][-1]
    # 2. tool_calls = last_msg.get("tool_calls", [])
    # 3. for tc in tool_calls:
    #        name = tc["function"]["name"]
    #        args = json.loads(tc["function"]["arguments"])
    #        result = execute_tool(name, args)
    #        messages.append({"role": "tool", "content": result, ...})
    pass


# ==================== 任务 5：定义 Router（条件路由） ====================

def router_should_continue(state: AgentState) -> str:
    """
    条件路由：判断下一步是继续还是结束
    
    返回：
    - "call_tool": 如果最后一条消息有 tool_calls，需要执行工具
    - "end" 或 "__end__": 如果没有 tool_calls，对话结束
    """
    # TODO 5.1：实现条件路由
    # 提示：
    # 1. 检查 state["messages"][-1] 是否包含 tool_calls
    # 2. 检查 step_count 是否超过上限
    # 3. 返回下一步的 node 名称
    pass


# ==================== 任务 6：构建 LangGraph ====================

def build_agent_graph():
    """
    构建 LangGraph ReAct Agent
    
    图结构：
        START → call_model → [路由器] → call_tool → call_model ...
                                     └→ END
    
    需求：
    1. 创建 StateGraph(AgentState)
    2. add_node("call_model", node_call_model)
    3. add_node("call_tool", node_call_tool)
    4. set_entry_point("call_model")
    5. add_conditional_edges("call_model", router_should_continue, {
         "call_tool": "call_tool",
         "__end__": END
       })
    6. add_edge("call_tool", "call_model")
    7. compile()
    """
    # TODO 6.1：实现 graph 构建
    # 注意：需要先 from langgraph.graph import StateGraph, END
    
    # ====== 先用普通字典模拟，如果装了 langgraph 再取消注释 ======
    
    # from langgraph.graph import StateGraph, END
    # graph = StateGraph(AgentState)
    # graph.add_node("call_model", node_call_model)
    # ...
    # return graph.compile()
    
    pass


# ==================== 任务 7：运行 Agent ====================

async def run_agent(user_input: str, max_steps: int = 10) -> str:
    """
    运行 Agent
    
    需求：
    1. 初始化 state = {"messages": [system_msg, user_msg], "step_count": 0}
    2. 调用 graph.invoke(state) 或 graph.astream(state)
    3. 返回最终回答
    """
    # TODO 7.1：实现 Agent 运行
    pass


# ==================== 模拟 LangGraph 运行（不依赖真实库） ====================

def simulate_langgraph_loop(user_input: str, max_steps: int = 10) -> str:
    """
    模拟 LangGraph 的 ReAct 循环
    
    如果你还没装 langgraph，先用这个模拟器跑通逻辑，
    Day 7 的核心是理解"图"的执行流程，而不是框架 API。
    """
    print(f"\n{'='*50}")
    print(f"🔄 模拟 LangGraph ReAct 循环")
    print(f"{'='*50}")
    
    messages = [
        {"role": "system", "content": "你是一个 AI 助手，可以使用工具。"},
        {"role": "user", "content": user_input},
    ]
    
    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")
        print(f"📍 当前 Node: call_model")
        
        # 调用 LLM
        response = mock_llm_response(messages)
        messages.append(response)
        
        # 检查是否有 tool_calls
        tool_calls = response.get("tool_calls", [])
        
        if tool_calls:
            print(f"🔀 路由到: call_tool")
            
            for tc in tool_calls:
                name = tc["function"]["name"]
                args_str = tc["function"]["arguments"]
                args = json.loads(args_str)
                
                print(f"  🔧 执行工具: {name}")
                print(f"  📥 参数: {args}")
                
                result = execute_tool(name, args)
                print(f"  📤 结果: {result}")
                
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc["id"]
                })
            
            print(f"🔀 路由回: call_model（继续）")
        else:
            print(f"🔀 路由到: END")
            final_answer = response.get("content", "")
            print(f"\n✅ 最终回答: {final_answer}")
            return final_answer
    
    return "达到最大步数限制"


# ==================== 主函数 ====================

async def main():
    print("=" * 60)
    print("Day 7 练习：LangGraph ReAct Agent")
    print("=" * 60)
    
    # 测试 1：用模拟器跑通 ReAct 流程
    print("\n📝 测试 1：计算问题")
    print("用户：帮我计算 3 + 5 * 2")
    simulate_langgraph_loop("帮我计算 3 + 5 * 2")
    
    # 测试 2：另一个工具
    print("\n\n📝 测试 2：天气查询")
    print("用户：北京今天天气怎么样？")
    simulate_langgraph_loop("北京今天天气怎么样？")
    
    print("\n" + "=" * 60)
    print("✅ 模拟流程通过！")
    print("\n下一步：安装 langgraph，用真实库重写")
    print("  pip install langgraph langchain-openai")
    print("  然后取消 build_agent_graph() 中的注释")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
