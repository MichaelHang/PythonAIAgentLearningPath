# Day 14 提供：单阶段构建（简单够用）
# 构建：docker build -t dev-agent .
# 运行：docker run --rm -e DEEPSEEK_API_KEY=sk-xxx -p 8000:8000 dev-agent
# 注意：Key 通过 -e 环境变量传入，永远不要 COPY 进镜像！
FROM python:3.12-slim

WORKDIR /app

# 先复制依赖清单再装依赖——利用 Docker 层缓存：
# 代码改动不会触发重新 pip install（重建速度快一个量级）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
