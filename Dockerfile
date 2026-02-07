FROM python:3.12-slim

WORKDIR /app

# 安装 OCR 依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --locked

# 数据持久化
VOLUME ["/app/data"]

EXPOSE 8080

CMD ["uv", "run", "python", "bot.py"]

