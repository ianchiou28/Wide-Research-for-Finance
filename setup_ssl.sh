#!/bin/bash

# SSL证书配置脚本
# 使用方法: ./setup_ssl.sh yourdomain.com

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <域名>"
    echo "例如: $0 finance.example.com"
    exit 1
fi

DOMAIN=$1

echo "🔐 开始配置SSL证书: $DOMAIN"

# 1. 安装Certbot
echo "📦 安装Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 2. 获取SSL证书
echo "🔑 获取SSL证书..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 3. 测试自动续期
echo "🔄 测试证书自动续期..."
sudo certbot renew --dry-run

# 4. 设置自动续期
echo "⏰ 设置自动续期..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# 5. 检查证书状态
echo "📋 检查证书状态..."
sudo certbot certificates

echo ""
echo "🎉 SSL配置完成！"
echo ""
echo "🔒 HTTPS访问地址:"
echo "  - 主页: https://$DOMAIN"
echo "  - 数据概览: https://$DOMAIN/overview"
echo "  - 报告列表: https://$DOMAIN/reports/"
echo ""
echo "📅 证书将在到期前自动续期"
echo "🔧 手动续期命令: sudo certbot renew"