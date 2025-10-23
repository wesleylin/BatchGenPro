#!/bin/bash

# BatchGen Pro 服务器部署脚本
# 服务器地址: 64.112.43.111
# 部署目录: /srv/batchgen_pro
# 域名: img.qingmood.xyz
# 端口: 8989

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_HOST="64.112.43.111"
SERVER_USER="root"
SERVER_DIR="/srv/batchgen_pro"
DOMAIN="img.qingmood.xyz"
FRONTEND_PORT="8989"
BACKEND_PORT="5001"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查本地环境
check_local_env() {
    log_step "检查本地环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "本地Docker未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "本地Docker Compose未安装"
        exit 1
    fi
    
    if ! command -v rsync &> /dev/null; then
        log_error "rsync未安装，请先安装: brew install rsync"
        exit 1
    fi
    
    log_info "本地环境检查通过"
}

# 检查服务器连接
check_server_connection() {
    log_step "检查服务器连接..."
    
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $SERVER_USER@$SERVER_HOST exit 2>/dev/null; then
        log_error "无法连接到服务器 $SERVER_HOST"
        log_info "请确保SSH密钥已配置或使用密码登录"
        exit 1
    fi
    
    log_info "服务器连接正常"
}

# 准备部署文件
prepare_deployment() {
    log_step "准备部署文件..."
    
    # 创建临时部署目录
    DEPLOY_DIR="./deploy_temp"
    rm -rf $DEPLOY_DIR
    mkdir -p $DEPLOY_DIR
    
    # 复制必要文件
    cp -r backend $DEPLOY_DIR/
    cp -r frontend $DEPLOY_DIR/
    cp -r config $DEPLOY_DIR/
    cp -r docker $DEPLOY_DIR/
    cp docker-compose.server.yml $DEPLOY_DIR/docker-compose.yml
    cp Dockerfile.backend $DEPLOY_DIR/
    cp Dockerfile.frontend $DEPLOY_DIR/
    cp .dockerignore $DEPLOY_DIR/
    cp env.example $DEPLOY_DIR/
    
    # 创建服务器启动脚本
    cat > $DEPLOY_DIR/start.sh << 'EOF'
#!/bin/bash
set -e

echo "启动BatchGen Pro服务..."

# 创建必要目录
mkdir -p uploads results logs

# 设置权限
chmod 755 uploads results logs

# 启动服务
docker-compose up -d

echo "服务启动完成！"
echo "前端地址: http://localhost:8989"
echo "后端地址: http://localhost:5001"
echo "健康检查: http://localhost:8989/health"
EOF
    
    chmod +x $DEPLOY_DIR/start.sh
    
    # 创建停止脚本
    cat > $DEPLOY_DIR/stop.sh << 'EOF'
#!/bin/bash
echo "停止BatchGen Pro服务..."
docker-compose down
echo "服务已停止"
EOF
    
    chmod +x $DEPLOY_DIR/stop.sh
    
    # 创建重启脚本
    cat > $DEPLOY_DIR/restart.sh << 'EOF'
#!/bin/bash
echo "重启BatchGen Pro服务..."
docker-compose down
docker-compose up -d
echo "服务重启完成！"
EOF
    
    chmod +x $DEPLOY_DIR/restart.sh
    
    log_info "部署文件准备完成"
}

# 上传文件到服务器
upload_to_server() {
    log_step "上传文件到服务器..."
    
    # 创建服务器目录
    ssh $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_DIR"
    
    # 上传文件
    rsync -avz --delete $DEPLOY_DIR/ $SERVER_USER@$SERVER_HOST:$SERVER_DIR/
    
    log_info "文件上传完成"
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx..."
    
    # 上传Nginx配置
    scp docker/nginx-server.conf $SERVER_USER@$SERVER_HOST:/etc/nginx/sites-available/batchgen_pro
    
    # 启用站点
    ssh $SERVER_USER@$SERVER_HOST "
        # 创建软链接
        ln -sf /etc/nginx/sites-available/batchgen_pro /etc/nginx/sites-enabled/
        
        # 测试Nginx配置
        nginx -t
        
        # 重载Nginx
        systemctl reload nginx
        
        echo 'Nginx配置完成'
    "
    
    log_info "Nginx配置完成"
}

# 启动服务
start_services() {
    log_step "启动服务..."
    
    ssh $SERVER_USER@$SERVER_HOST "
        cd $SERVER_DIR
        
        # 创建环境变量文件
        if [ ! -f .env ]; then
            cp env.example .env
            echo '请编辑 .env 文件配置API密钥'
        fi
        
        # 启动服务
        ./start.sh
        
        # 等待服务启动
        sleep 30
        
        # 检查服务状态
        echo '检查服务状态...'
        docker-compose ps
    "
    
    log_info "服务启动完成"
}

# 检查部署状态
check_deployment() {
    log_step "检查部署状态..."
    
    ssh $SERVER_USER@$SERVER_HOST "
        cd $SERVER_DIR
        
        echo '=== Docker服务状态 ==='
        docker-compose ps
        
        echo ''
        echo '=== 服务健康检查 ==='
        curl -f http://localhost:8989/health && echo '前端服务正常' || echo '前端服务异常'
        curl -f http://localhost:5001/api/health && echo '后端服务正常' || echo '后端服务异常'
        
        echo ''
        echo '=== 端口监听状态 ==='
        netstat -tlnp | grep -E ':(8989|5001|6379)'
    "
    
    log_info "部署状态检查完成"
}

# 显示访问信息
show_access_info() {
    log_step "部署完成！"
    
    echo ""
    echo "=========================================="
    echo "🎉 BatchGen Pro 部署成功！"
    echo "=========================================="
    echo ""
    echo "🌐 访问地址:"
    echo "   前端: https://$DOMAIN"
    echo "   健康检查: https://$DOMAIN/health"
    echo ""
    echo "🔧 服务器信息:"
    echo "   服务器: $SERVER_HOST"
    echo "   部署目录: $SERVER_DIR"
    echo "   前端端口: $FRONTEND_PORT"
    echo "   后端端口: $BACKEND_PORT"
    echo ""
    echo "📋 管理命令:"
    echo "   ssh $SERVER_USER@$SERVER_HOST"
    echo "   cd $SERVER_DIR"
    echo "   ./start.sh    # 启动服务"
    echo "   ./stop.sh     # 停止服务"
    echo "   ./restart.sh  # 重启服务"
    echo "   docker-compose logs -f  # 查看日志"
    echo ""
    echo "⚠️  注意事项:"
    echo "   1. 请编辑 $SERVER_DIR/.env 文件配置API密钥"
    echo "   2. 确保SSL证书已正确配置"
    echo "   3. 检查防火墙设置"
    echo ""
}

# 清理临时文件
cleanup() {
    log_step "清理临时文件..."
    rm -rf ./deploy_temp
    log_info "清理完成"
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            check_local_env
            check_server_connection
            prepare_deployment
            upload_to_server
            configure_nginx
            start_services
            check_deployment
            show_access_info
            cleanup
            ;;
        "update")
            log_info "更新服务..."
            check_server_connection
            prepare_deployment
            upload_to_server
            ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_DIR && ./restart.sh"
            check_deployment
            cleanup
            ;;
        "status")
            check_server_connection
            check_deployment
            ;;
        "logs")
            check_server_connection
            ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_DIR && docker-compose logs -f"
            ;;
        *)
            echo "使用方法: $0 {deploy|update|status|logs}"
            echo "  deploy  - 完整部署"
            echo "  update  - 更新服务"
            echo "  status  - 检查状态"
            echo "  logs    - 查看日志"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
