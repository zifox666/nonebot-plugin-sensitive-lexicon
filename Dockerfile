FROM python:3.10-slim

WORKDIR /app

# 安装额外依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libgomp1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY bot.py ./

# 数据持久化
VOLUME ["/app/data"]

EXPOSE 8120

CMD ["python", "bot.py"]

