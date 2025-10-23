# BatchGen Pro 服务器部署指南

## 🚀 服务器信息
- **服务器地址**: 64.112.43.111
- **部署目录**: /srv/batchgen_pro
- **域名**: img.qingmood.xyz
- **前端端口**: 8989
- **后端端口**: 5001

## 📋 部署前准备

### 1. 服务器环境检查
确保服务器已安装：
- Docker 20.10+
- Docker Compose 2.0+
- Nginx
- SSL证书（用于HTTPS）

### 2. 本地环境准备
确保本地已安装：
- Docker
- Docker Compose
- rsync
- SSH访问权限

## 🛠️ 部署步骤

### 方式一：一键部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd BatchGen\ Pro

# 2. 执行部署脚本
./deploy-server.sh deploy
```

### 方式二：手动部署

```bash
# 1. 准备部署文件
./deploy-server.sh prepare

# 2. 上传到服务器
rsync -avz ./deploy_temp/ root@64.112.43.111:/srv/batchgen_pro/

# 3. 配置Nginx
scp docker/nginx-server.conf root@64.112.43.111:/etc/nginx/sites-available/batchgen_pro
ssh root@64.112.43.111 "ln -sf /etc/nginx/sites-available/batchgen_pro /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx"

# 4. 启动服务
ssh root@64.112.43.111 "cd /srv/batchgen_pro && ./start.sh"
```

## 🔧 服务管理

### 登录服务器
```bash
ssh root@64.112.43.111
cd /srv/batchgen_pro
```

### 服务控制
```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 更新服务
```bash
# 本地执行
./deploy-server.sh update
```

## 🌐 访问地址

- **前端**: https://img.qingmood.xyz
- **健康检查**: https://img.qingmood.xyz/health
- **API**: https://img.qingmood.xyz/api/

## ⚙️ 配置说明

### 1. 环境变量配置
编辑 `/srv/batchgen_pro/.env` 文件：
```bash
# API密钥配置
GEMINI_API_KEY=your_gemini_api_key
DOUBAO_API_KEY=your_doubao_api_key

# Redis密码
REDIS_PASSWORD=batchgen_prod_2024
```

### 2. Nginx配置
Nginx配置文件位置：`/etc/nginx/sites-available/batchgen_pro`

主要配置：
- 域名：img.qingmood.xyz
- SSL重定向
- 前端代理到8989端口
- API代理到5001端口
- 静态文件缓存

### 3. SSL证书
确保SSL证书文件存在：
- `/etc/nginx/ssl/img.qingmood.xyz.crt`
- `/etc/nginx/ssl/img.qingmood.xyz.key`

## 🔍 故障排查

### 1. 检查服务状态
```bash
# 检查Docker服务
docker-compose ps

# 检查端口监听
netstat -tlnp | grep -E ':(8989|5001|6379)'

# 检查Nginx状态
systemctl status nginx
```

### 2. 查看日志
```bash
# 应用日志
docker-compose logs -f

# Nginx日志
tail -f /var/log/nginx/batchgen_pro_access.log
tail -f /var/log/nginx/batchgen_pro_error.log
```

### 3. 健康检查
```bash
# 前端健康检查
curl -f http://localhost:8989/health

# 后端健康检查
curl -f http://localhost:5001/api/health
```

## 📊 监控和维护

### 1. 定期维护
- 清理旧的上传文件和生成结果
- 监控磁盘空间使用
- 检查服务运行状态

### 2. 备份策略
- 定期备份Redis数据
- 备份配置文件
- 备份上传的图片文件

### 3. 安全建议
- 定期更新API密钥
- 监控访问日志
- 设置防火墙规则

## 🆘 支持联系

如遇到问题，请检查：
1. 服务运行状态
2. 日志文件
3. 网络连接
4. 配置文件

部署完成后，访问 https://img.qingmood.xyz 即可使用BatchGen Pro！
