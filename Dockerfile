FROM python:3.9-slim

# 使用国内 Debian 镜像以加速 apt-get（兼容无 sources.list 的 slim 基础镜像）
RUN set -eux; \
        if [ -f /etc/apt/sources.list ]; then \
            sed -i 's@deb.debian.org@mirrors.aliyun.com@g; s@security.debian.org@mirrors.aliyun.com/debian-security@g' /etc/apt/sources.list; \
        else \
            echo 'deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list; \
            echo 'deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list; \
            echo 'deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list; \
        fi

WORKDIR /app

# 安装系统依赖（最小化安装并清理）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p data/reports data/summaries data/weekly data/raw

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "web_app.py"]