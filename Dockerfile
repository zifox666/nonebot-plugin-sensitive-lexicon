FROM python:3.12-slim as builder

WORKDIR /app

# 只安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 先复制依赖文件（利用缓存）
COPY pyproject.toml uv.lock ./

# 安装依赖到独立目录
RUN uv sync --locked --no-dev

# 最终镜像
FROM python:3.12-slim

WORKDIR /app

# 只安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 从 builder 复制依赖
COPY --from=builder /app/.venv /app/.venv

# 复制源码
COPY src ./src
COPY bot.py ./

# 使用虚拟环境
ENV PATH="/app/.venv/bin:$PATH"

# 数据持久化
VOLUME ["/app/data"]

EXPOSE 8080

CMD ["python", "bot.py"]

