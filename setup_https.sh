#!/bin/bash

# HTTPS配置脚本
# 使用方法: ./setup_https.sh yourdomain.com

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <域名>"
    exit 1
fi

DOMAIN=$1

echo "🔐 为 $DOMAIN 配置HTTPS..."

# 1. 安装Certbot
echo "📦 安装Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 2. 获取SSL证书
echo "🔒 获取SSL证书..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 3. 设置自动续期
echo "⏰ 设置自动续期..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# 4. 测试配置
echo "🔍 测试SSL配置..."
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "🎉 HTTPS配置完成！"
echo ""
echo "访问地址: https://$DOMAIN"
echo ""
echo "SSL证书将自动续期"