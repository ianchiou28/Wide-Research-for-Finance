FROM python:3.9-slim

# 使用国内 Debian 镜像以加速 apt-get（覆盖 debian.sources 与 sources.list）
RUN cat > /etc/apt/sources.list <<'EOF'
deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware
deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware
deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware
EOF
RUN rm -f /etc/apt/sources.list.d/debian.sources

WORKDIR /app

# 安装系统依赖（最小化安装并清理）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（含 gunicorn 生产服务器）
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录和日志目录
RUN mkdir -p data/reports data/summaries data/weekly data/raw data/logs

# 创建非 root 用户运行应用
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 生产环境使用 gunicorn，4 worker + 2 thread，超时120s
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "web_app:app"]