#!/bin/bash
# 阿里云一键部署脚本

echo "=== 开始部署财经信息聚合平台 ==="

# 1. 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# 2. 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 3. 克隆项目
if [ ! -d "wide-research-for-finance" ]; then
    git clone https://github.com/ianchiou28/Wide-Research-for-Finance.git
    cd wide-research-for-finance
else
    cd wide-research-for-finance
    git pull
fi

# 4. 配置环境变量
if [ ! -f ".env" ]; then
    echo "请配置.env文件:"
    echo "DEEPSEEK_API_KEY=your_key_here" > .env
    echo "请编辑.env文件添加你的API密钥"
    exit 1
fi

# 5. 启动服务
echo "启动Docker服务..."
sudo docker-compose up -d

echo "=== 部署完成 ==="
echo "网站地址: http://$(curl -s ifconfig.me)"
echo "查看日志: docker-compose logs -f"