# GitHub上传说明

## 📦 打包内容

此目录包含所有需要上传到GitHub的文件，已自动排除：
- 用户数据文件（*.json）
- 日志文件（logs/）
- 数据目录（data/）
- Python缓存（__pycache__/）
- 配置文件（config.py，包含敏感信息）
- 打包脚本（package_for_github.*）

## 🚀 上传步骤

### 方式一：使用Git命令行

1. **初始化Git仓库**（如果还没有）：
   ```bash
   cd github_upload_package
   git init
   ```

2. **添加所有文件**：
   ```bash
   git add .
   ```

3. **提交**：
   ```bash
   git commit -m "Initial commit: LOF基金套利工具"
   ```

4. **添加远程仓库**：
   ```bash
   git remote add origin https://github.com/your-username/your-repo-name.git
   ```

5. **推送到GitHub**：
   ```bash
   git branch -M main
   git push -u origin main
   ```

### 方式二：使用GitHub Desktop

1. 打开GitHub Desktop
2. 选择 `File` -> `Add Local Repository`
3. 选择 `github_upload_package` 目录
4. 点击 `Publish repository` 上传到GitHub

### 方式三：直接在GitHub网页上传

1. 在GitHub创建新仓库
2. 点击 `uploading an existing file`
3. 将 `github_upload_package` 目录中的所有文件拖拽上传

## ⚠️ 重要提示

### 首次部署配置

用户首次部署时需要：

1. **复制配置文件模板**：
   ```bash
   cp config.example.py config.py
   ```

2. **配置Tushare Token**（两种方式任选其一）：

   **方式一：使用环境变量（推荐）**
   ```bash
   # Linux/Mac
   export TUSHARE_TOKEN=your_real_token_here
   
   # Windows (PowerShell)
   $env:TUSHARE_TOKEN="your_real_token_here"
   
   # Windows (CMD)
   set TUSHARE_TOKEN=your_real_token_here
   ```

   **方式二：直接在config.py中填写**
   编辑 `config.py`，将 `your_tushare_token_here` 替换为真实的token。

### 获取Tushare Token

1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号并登录
3. 在个人中心获取token

## 📋 文件说明

- **config.example.py**: 配置文件模板，包含所有配置项的说明
- **.gitignore**: Git忽略文件配置，确保敏感信息不会被提交
- **requirements.txt**: Python依赖包列表
- **README.md**: 项目说明文档
- **DEPLOYMENT.md**: Windows部署指南
- **DEPLOYMENT_LINUX.md**: Linux部署指南
- **deploy.bat / deploy.sh**: 一键部署脚本
- **install_service.bat / install_service.sh**: 服务安装脚本

## 🔒 安全建议

1. **不要提交敏感信息**：
   - `config.py` 已在 `.gitignore` 中，不会被提交
   - 确保没有在代码中硬编码token或密码

2. **使用环境变量**：
   - 推荐使用环境变量存储敏感配置
   - 生产环境建议使用密钥管理服务

3. **定期更新依赖**：
   - 定期检查并更新 `requirements.txt` 中的依赖包
   - 关注安全漏洞公告

## 📝 后续更新

如果需要更新GitHub仓库：

1. 在项目根目录运行打包脚本：
   ```bash
   # Windows
   package_for_github.bat
   
   # Linux
   ./package_for_github.sh
   ```

2. 进入打包目录并提交更改：
   ```bash
   cd github_upload_package
   git add .
   git commit -m "Update: 描述你的更改"
   git push
   ```
