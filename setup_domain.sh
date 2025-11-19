#!/bin/bash

# 域名配置自动化脚本
# 使用方法: ./setup_domain.sh yourdomain.com

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <域名>"
    echo "例如: $0 finance.example.com"
    exit 1
fi

DOMAIN=$1
PROJECT_DIR="/root/Wide-Research-for-Finance"

echo "🚀 开始配置域名: $DOMAIN"

# 1. 安装Nginx
echo "📦 安装Nginx..."
sudo apt update
sudo apt install -y nginx

# 2. 创建Web应用服务
echo "🔧 配置Web应用服务..."
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

# 3. 配置Nginx
echo "🌐 配置Nginx反向代理..."
sudo tee /etc/nginx/sites-available/finance-research > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /reports/ {
        alias $PROJECT_DIR/data/reports/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
    
    # 安全配置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
}
EOF

# 4. 启用网站配置
echo "✅ 启用网站配置..."
sudo ln -sf /etc/nginx/sites-available/finance-research /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. 测试Nginx配置
echo "🔍 测试Nginx配置..."
if sudo nginx -t; then
    echo "✅ Nginx配置正确"
else
    echo "❌ Nginx配置错误，请检查"
    exit 1
fi

# 6. 启动服务
echo "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl start finance-web
sudo systemctl enable finance-web
sudo systemctl restart nginx
sudo systemctl enable nginx

# 7. 配置防火墙
echo "🔒 配置防火墙..."
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable

# 8. 检查服务状态
echo "📊 检查服务状态..."
echo "Web应用状态:"
sudo systemctl status finance-web --no-pager -l
echo ""
echo "Nginx状态:"
sudo systemctl status nginx --no-pager -l

echo ""
echo "🎉 域名配置完成！"
echo ""
echo "📋 访问地址:"
echo "  - 主页: http://$DOMAIN"
echo "  - 数据概览: http://$DOMAIN/overview"
echo "  - 报告列表: http://$DOMAIN/reports/"
echo ""
echo "🔧 管理命令:"
echo "  - 重启Web: sudo systemctl restart finance-web"
echo "  - 查看日志: sudo journalctl -u finance-web -f"
echo "  - 重启Nginx: sudo systemctl restart nginx"
echo ""
echo "🔐 配置SSL证书 (可选):"
echo "  sudo apt install certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
echo "⚠️  请确保域名已正确解析到服务器IP: $(curl -s ifconfig.me)"