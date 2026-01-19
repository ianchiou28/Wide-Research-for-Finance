#!/bin/bash

###############################################################################
# Wide Research for Finance - 自动化部署脚本
# 用于Linux云服务器的一键部署和管理
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# 步骤 1: 检查系统
###############################################################################
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Linux系统检测成功"
    else
        log_error "当前脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [ "$DISK_SPACE" -lt 5242880 ]; then  # 5GB
        log_warn "磁盘空间不足5GB，建议扩展"
    fi
    
    # 检查权限
    if [ "$EUID" -ne 0 ]; then 
        log_error "请使用sudo运行此脚本"
        exit 1
    fi
    
    log_success "系统检查完成"
}

###############################################################################
# 步骤 2: 安装Docker
###############################################################################
install_docker() {
    log_info "检查Docker安装状态..."
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_success "Docker已安装: $DOCKER_VERSION"
        return
    fi
    
    # 在 auto_deploy.sh 的 install_docker() 函数中，替换第75-110行为：

    log_info "开始安装Docker..."
    
    # 更新包管理器
    apt update -y
    apt install -y curl gnupg lsb-release ca-certificates
    
    # 确保keyrings目录存在
    mkdir -p /etc/apt/keyrings
    chmod 755 /etc/apt/keyrings
    
    # 删除旧的密钥文件（避免交互提示）
    rm -f /etc/apt/keyrings/docker.gpg
    
    # 使用阿里云镜像安装Docker（更稳定）
    log_info "使用阿里云镜像源..."
    
    # 多源重试下载GPG密钥
    GPG_SUCCESS=0
    for mirror in \
        "https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg" \
        "https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg" \
        "https://download.docker.com/linux/ubuntu/gpg"
    do
        log_info "尝试从 ${mirror} 下载GPG密钥..."
        if curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 10 "${mirror}" | gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null; then
            log_success "GPG密钥下载成功"
            GPG_SUCCESS=1
            break
        else
            log_warn "从 ${mirror} 下载失败，尝试下一个源..."
        fi
    done
    
    if [ $GPG_SUCCESS -eq 0 ]; then
        log_error "所有镜像源均无法下载Docker GPG密钥，可能是网络问题"
        log_info "建议检查网络连接或稍后重试"
        exit 1
    fi
    
    # 添加Docker仓库（优先使用阿里云镜像）
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    log_info "更新软件包索引..."
    apt update -y
    
    log_info "安装Docker组件..."
    if ! apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin; then
        log_warn "apt安装失败，尝试使用官方一键安装脚本..."
        curl -fsSL https://get.docker.com | sh || {
            log_error "Docker安装失败，请检查网络或手动安装"
            exit 1
        }
    fi
    
    # 配置Docker国内镜像加速
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<EOF
{
    "registry-mirrors": [
        "https://docker.m.daocloud.io",
        "https://mirror.ccs.tencentyun.com",
        "https://hub-mirror.c.163.com",
        "https://dockerproxy.com"
    ]
}
EOF
    
    # 启动Docker
    systemctl enable docker 2>/dev/null || true
    systemctl restart docker || systemctl start docker
    
    log_success "Docker安装完成"
}

###############################################################################
# 步骤 2.1: 配置Docker镜像加速（无论是否已安装）
###############################################################################
configure_docker_mirrors() {
        log_info "配置Docker镜像加速..."
        mkdir -p /etc/docker
        cat > /etc/docker/daemon.json <<EOF
{
    "registry-mirrors": [
        "https://docker.m.daocloud.io",
        "https://mirror.ccs.tencentyun.com",
        "https://hub-mirror.c.163.com",
        "https://dockerproxy.com"
    ]
}
EOF

        systemctl restart docker || systemctl start docker
        log_success "镜像加速配置完成"
}

###############################################################################
# 步骤 3: 安装Docker Compose
###############################################################################
install_docker_compose() {
    log_info "检查Docker Compose安装状态..."
    
    if command -v docker-compose &> /dev/null; then
        DC_VERSION=$(docker-compose --version)
        log_success "Docker Compose已安装: $DC_VERSION"
        return
    fi
    
    log_info "开始安装Docker Compose..."
    
    # 使用国内镜像下载（更稳定）
    DOCKER_COMPOSE_VERSION="v2.24.0"
    log_info "下载Docker Compose ${DOCKER_COMPOSE_VERSION}..."
    
    # 尝试使用镜像站点
    curl -L "https://get.daocloud.io/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose || \
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成: $DOCKER_COMPOSE_VERSION"
}

###############################################################################
# 步骤 4: 配置用户权限
###############################################################################
setup_user() {
    log_info "配置Docker用户权限..."
    
    # 创建docker组（如果不存在）
    getent group docker || groupadd docker
    
    # 将当前用户加入docker组
    usermod -aG docker $USER
    
    log_success "用户权限配置完成（需要重新登录生效）"
}

###############################################################################
# 步骤 5: 克隆项目
###############################################################################
clone_project() {
    local deploy_dir=${1:-.}
    
    log_info "克隆项目代码..."
    
    cd $deploy_dir
    
    if [ -d "Wide-Research-for-Finance" ]; then
        log_warn "项目已存在，更新代码..."
        cd Wide-Research-for-Finance
        git pull origin server-base
    else
        git clone -b server-base https://github.com/ianchiou28/Wide-Research-for-Finance.git
        cd Wide-Research-for-Finance
    fi
    
    log_success "项目克隆完成: $(pwd)"
}

###############################################################################
# 步骤 6: 配置环境变量
###############################################################################
setup_env() {
    local project_dir=$1
    
    log_info "配置环境变量..."
    
    if [ ! -f "$project_dir/.env" ]; then
        log_warn ".env文件不存在，创建新的..."
        
        cat > "$project_dir/.env" <<EOF
# DeepSeek API密钥（必需）
DEEPSEEK_API_KEY=sk-your_api_key_here

# 邮件配置（可选）
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# Docker环境标识
DOCKER_ENV=true
EOF
        
        log_warn "请编辑.env文件，添加你的DEEPSEEK_API_KEY:"
        log_warn "nano $project_dir/.env"
        
        return 1
    else
        log_success ".env文件已存在"
        return 0
    fi
}

###############################################################################
# 步骤 7: 构建和启动服务
###############################################################################
start_services() {
    local project_dir=$1
    
    log_info "构建Docker镜像..."
    cd $project_dir
    docker-compose build
    
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    sleep 5
    
    log_info "验证服务状态..."
    docker-compose ps
    
    log_success "服务启动完成"
}

###############################################################################
# 步骤 8: 验证部署
###############################################################################
verify_deployment() {
    local project_dir=$1
    
    log_info "验证部署状态..."
    cd $project_dir
    
    # 检查容器是否运行
    if ! docker-compose ps | grep -q "finance-app"; then
        log_error "finance-app容器未运行"
        return 1
    fi
    
    # 等待应用启动
    sleep 10
    
    # 测试API
    if curl -s http://localhost:5000/api/latest &> /dev/null; then
        log_success "API服务正常"
    else
        log_warn "API服务暂未响应，请稍候"
    fi
    
    log_success "部署验证完成"
}

###############################################################################
# 步骤 9: 设置自动备份
###############################################################################
setup_backup() {
    local project_dir=$1
    local backup_dir="/var/backups/finance-app"
    
    log_info "设置自动备份..."
    
    mkdir -p $backup_dir
    
    # 创建备份脚本
    cat > /usr/local/bin/backup-finance-app.sh <<'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/var/backups/finance-app"
PROJECT_DIR="$1"
BACKUP_PATH="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S)"

mkdir -p $BACKUP_PATH
cp -r $PROJECT_DIR/data $BACKUP_PATH/

# 保留最近7个备份
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

echo "备份完成: $BACKUP_PATH"
BACKUPEOF
    
    chmod +x /usr/local/bin/backup-finance-app.sh
    
    # 添加定时任务
    cat > /etc/cron.d/finance-app-backup <<EOF
# 每天凌晨2点执行备份
0 2 * * * root /usr/local/bin/backup-finance-app.sh $project_dir
EOF
    
    log_success "自动备份已配置（每天凌晨2点）"
}

###############################################################################
# 步骤 10: 输出部署信息
###############################################################################
print_summary() {
    local project_dir=$1
    local server_ip=$2
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          部署完成！Wide Research for Finance                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "📊 应用信息:"
    echo "  项目位置: $project_dir"
    echo "  Web访问: http://$server_ip"
    echo "  API地址: http://$server_ip/api/latest"
    echo ""
    echo "🐳 常用命令:"
    echo "  查看日志: docker-compose -f $project_dir/docker-compose.yml logs -f"
    echo "  启动服务: docker-compose -f $project_dir/docker-compose.yml up -d"
    echo "  停止服务: docker-compose -f $project_dir/docker-compose.yml down"
    echo "  重启服务: docker-compose -f $project_dir/docker-compose.yml restart"
    echo ""
    echo "⚙️  后续操作:"
    echo "  1. 编辑.env文件配置DEEPSEEK_API_KEY:"
    echo "     nano $project_dir/.env"
    echo ""
    echo "  2. 重启服务以应用配置:"
    echo "     docker-compose -f $project_dir/docker-compose.yml restart"
    echo ""
    echo "  3. 查看应用日志:"
    echo "     docker-compose -f $project_dir/docker-compose.yml logs -f finance-app"
    echo ""
    echo "📚 文档:"
    echo "  - 部署指南: $project_dir/DEPLOYMENT_GUIDE_CN.md"
    echo "  - README: $project_dir/README.md"
    echo ""
}

###############################################################################
# 主函数
###############################################################################
main() {
    log_info "开始部署 Wide Research for Finance"
    echo ""
    
    # 确认部署目录
    DEPLOY_DIR=${1:-/opt}
    log_info "部署目录: $DEPLOY_DIR"
    
    # 执行各个步骤
    check_system
    install_docker
    configure_docker_mirrors
    install_docker_compose
    setup_user
    
    # 创建/进入部署目录
    mkdir -p $DEPLOY_DIR
    cd $DEPLOY_DIR
    
    clone_project $DEPLOY_DIR
    PROJECT_DIR="$DEPLOY_DIR/Wide-Research-for-Finance"

    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi

    if ! setup_env $PROJECT_DIR; then
        log_error "环境配置不完整，请先编辑.env文件"
        exit 1
    fi
    
    start_services $PROJECT_DIR
    verify_deployment $PROJECT_DIR
    setup_backup $PROJECT_DIR
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")
    
    print_summary $PROJECT_DIR $SERVER_IP
    
    log_success "部署流程完全结束！"
}

###############################################################################
# 运行脚本
###############################################################################
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
