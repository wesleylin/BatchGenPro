# GitHub 仓库配置说明

## 📦 仓库信息

**GitHub 仓库地址**: https://github.com/wesleylin/BatchGen-Pro.git

## 🔧 本地配置步骤

### 1. 配置 Git Remote

如果仓库已创建，可以直接添加 remote：

```bash
# 使用 HTTPS（需要输入用户名密码或使用 Personal Access Token）
git remote add origin https://github.com/wesleylin/BatchGen-Pro.git

# 或使用 SSH（需要配置 SSH key）
git remote add origin git@github.com:wesleylin/BatchGen-Pro.git
```

### 2. 首次推送代码

如果 GitHub 仓库已存在：

```bash
# 推送代码到 GitHub
git push -u origin main
```

如果 GitHub 仓库还不存在，需要先在 GitHub 上创建仓库。

### 3. 配置 SSH Key（推荐）

使用 SSH 可以避免每次推送都需要输入密码：

1. **生成 SSH Key**（如果还没有）：
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **复制公钥**：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. **添加到 GitHub**：
   - 登录 GitHub
   - 进入 Settings > SSH and GPG keys
   - 点击 New SSH key
   - 粘贴公钥并保存

4. **测试连接**：
   ```bash
   ssh -T git@github.com
   ```

## 🖥️ 服务器配置

### 首次在服务器上克隆项目

1. **SSH 登录服务器**：
   ```bash
   ssh wesley@64.112.43.111
   ```

2. **克隆项目**：
   ```bash
   cd /srv
   git clone https://github.com/wesleylin/BatchGen-Pro.git batchgen_pro
   cd batchgen_pro
   ```

3. **配置 API 密钥**：
   ```bash
   # 复制配置文件模板（如果存在）
   # 编辑 config/api_keys.py，填入实际的 API 密钥
   ```

4. **启动服务**：
   ```bash
   docker-compose -f docker-compose.server.yml up -d --build
   ```

### 服务器更新流程（已存在的项目）

如果服务器上已有项目目录，需要：

1. **进入项目目录**：
   ```bash
   cd /srv/batchgen_pro
   ```

2. **初始化 Git（如果还没有）**：
   ```bash
   git init
   git remote add origin https://github.com/wesleylin/BatchGen-Pro.git
   git fetch origin
   git reset --hard origin/main
   ```

3. **后续更新**：
   ```bash
   git pull origin main
   docker-compose -f docker-compose.server.yml down
   docker-compose -f docker-compose.server.yml up -d --build
   docker exec nginx_proxy nginx -s reload
   ```

## 📝 注意事项

1. **API 密钥安全**：
   - `config/api_keys.py` 已在 `.gitignore` 中，不会被提交
   - 服务器上需要手动配置 API 密钥

2. **敏感数据**：
   - `.env` 文件不会被提交
   - `uploads/` 和 `results/` 目录不会被提交

3. **工作流程**：
   - 本地开发 → 提交代码 → 推送到 GitHub
   - 服务器 → 从 GitHub 拉取 → 重新部署

## 🔐 GitHub Personal Access Token（如果使用 HTTPS）

如果使用 HTTPS 连接，GitHub 已经不支持密码认证，需要使用 Personal Access Token：

1. **创建 Token**：
   - GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
   - 生成新 token，勾选 `repo` 权限

2. **使用 Token**：
   ```bash
   git push origin main
   # 用户名：你的 GitHub 用户名
   # 密码：输入刚才创建的 Personal Access Token
   ```

