#!/bin/bash

# 快速部署脚本
# 使用方法: ./quick_deploy.sh yourdomain.com

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <域名>"
    echo "例如: $0 finance.example.com"
    exit 1
fi

DOMAIN=$1
PROJECT_DIR="/root/Wide-Research-for-Finance"

echo "🚀 开始快速部署到域名: $DOMAIN"

# 1. 安装依赖
echo "📦 安装必要软件..."
sudo apt update
sudo apt install -y nginx python3 python3-pip python3-venv

# 2. 设置Python环境
echo "🐍 配置Python环境..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 创建Web服务
echo "🔧 创建Web服务..."
sudo tee /etc/systemd/system/finance-web.service > /dev/null <<EOF
[Unit]
Description=Finance Web App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python web_app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. 配置Nginx
echo "🌐 配置Nginx..."
sudo tee /etc/nginx/sites-available/finance > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 30d;
    }
    
    location /reports/ {
        alias $PROJECT_DIR/data/reports/;
        autoindex on;
    }
}
EOF

# 5. 启用配置
sudo ln -sf /etc/nginx/sites-available/finance /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 6. 启动服务
echo "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl start finance-web
sudo systemctl enable finance-web
sudo systemctl restart nginx
sudo systemctl enable nginx

# 7. 开放端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

echo ""
echo "🎉 部署完成！"
echo ""
echo "访问地址: http://$DOMAIN"
echo ""
echo "管理命令:"
echo "  重启Web: sudo systemctl restart finance-web"
echo "  查看日志: sudo journalctl -u finance-web -f"
echo ""
echo "配置SSL: sudo certbot --nginx -d $DOMAIN"