# Python 工程师 AI Agent 开发 15 天学习路线图

一个纯静态的中文学习网站：15 天从 Python 高级特性到独立开发 AI Agent。
打开 [index.html](index.html) 即可开始学习。

## 学习路线

| 阶段 | 内容 | 配套材料 |
|---|---|---|
| 阶段一（Day 1-5） | Python 异步/类型系统/生成器 + LLM API + Function Calling | 每天练习模板 + 自动验收脚本 |
| 阶段二（Day 6-10） | ReAct Agent、LangGraph、MCP、RAG 与记忆系统 | 每天练习模板 + 自动验收脚本 |
| 阶段三（Day 11-15） | 完整 Agent 项目实战（FastAPI + 部署） | Day 11-15 学习页 + 项目脚手架 `project_day11_15/`（前端/测试/Docker 文件已提供） |

## 快速开始

```bash
# 1. 环境要求：Python >= 3.11（教程用到 asyncio.timeout）
python --version

# 2. 安装依赖
pip install -r requirements.txt

# 3. 跑一遍 Day 1 的异步教程热身
python tutorial_02_async.py

# 3.5（可选）配好 Key 后体验真实 LLM API
#   PowerShell:  $env:DEEPSEEK_API_KEY = "sk-..."
python tutorial_03_real_api.py

# 4. 开始 Day 1：打开 day01_practice_template.html，完成其中的 TODO
python day01_practice_template.py      # 运行你的实现
python day01_practice_validator.py     # 行为级验收打分

# 5. 在浏览器打开 index.html，按路线图逐天推进
```

## 每天的学习闭环

1. **学**：打开 `dayNN_lesson.html`（学习页）——今天的目标、理论知识点（带代码示例）、
   分步实操指引、每道 TODO 的提示、验收达标线，全在这一页
2. **看**：回到 index.html 看当天的表格概览、免费资源和避坑清单
3. **练**：打开 `dayNN_practice_template.html`（或直接编辑 .py 文件），按学习页的指引完成里面的 TODO
4. **验**：运行 `python dayNN_practice_validator.py`，验收脚本会**直接调用你实现的函数**、
   断言真实返回值和真实耗时，空白模板只有个位数分数，全部做对才能拿满分
   （也可用 `--file 你的文件.py` 验收任意文件；Day 1-10 全部有自动验收）
5. [ACCEPTANCE_CRITERIA.html](ACCEPTANCE_CRITERIA.html) 提供每天的分值明细和手动清单，作为深度自查补充

## 目录结构

```
index.html                       # 学习路线图主页（15 天大纲 + 避坑指南 + 资源汇总）
ACCEPTANCE_CRITERIA.html         # 每个练习的验收标准与手动清单
day01~day10_lesson.html          # 每天的学习页（目标/理论/实操步骤/验收要求）
tutorial_01_decorators.py/.html  # 装饰器 8 步实战教程（对应 Day 2）
tutorial_02_async.py/.html       # 异步 9 步实战教程（对应 Day 1）
tutorial_03_real_api.py/.html    # 真实 LLM API 实战教程（可选，需 Key：DeepSeek/Qwen 等）
day01~day10_practice_template.*  # 每天练习模板（含 TODO）
day01~day10_practice_validator.* # 自动验收脚本（行为级打分，全部 10 天）
generate_html.py                 # 修改 .py 后重新生成对应代码页
generate_lessons.py              # 学习页内容源文件（改课程内容后运行）
fonts/                           # Maple Mono 代码字体（自托管 woff2，OFL 协议）
```

## 依赖说明

- **必装**：`pydantic`（Day 2、Day 5）
- **可选**：`langgraph langchain-openai`（Day 7 真实框架练习）、`mcp`（Day 8 SDK 对照）、
  `chromadb` 或 `faiss-cpu`（Day 9 正式向量检索）、`aiohttp`（真实 API 调用）
- 所有练习默认使用内置 mock，**不需要任何 LLM API Key** 即可完成；
  想接真实 API 时可在 Day 4/5/6 中替换为 DeepSeek / Qwen 等兼容接口

## 维护者

修改任何 `.py` 文件后运行 `python generate_html.py`，保持网页与代码同步。
