# AI 求职助手 🎯

基于 DeepSeek API 的简历-JD 匹配分析工具。上传 PDF 简历，粘贴或截图岗位描述，
AI 自动分析匹配度并生成：
- 优势分析 & 技能缺口
- 简历修改建议 & 面试问题预测
- 针对目标岗位优化的简历（可复制或下载 Word）

## 功能特性

| 功能 | 说明 |
|------|------|
| PDF 简历上传 | 拖拽或点击上传，支持微信直接拖拽 |
| JD 文本输入 | 粘贴文字，或截图自动 OCR 识别（支持多张） |
| 匹配度分析 | 综合评分 + 4 维度结构化报告 |
| 简历优化 | 基于 JD 重新组织语言，保留真实信息 |
| 下载 Word | 一键下载优化后的简历 (.doc 格式) |
| 无需登录 | 直接使用，不保存任何用户文件 |
| 响应式设计 | 手机 / 平板 / 桌面均可正常使用 |

## 技术栈

- **后端**: Python FastAPI
- **AI**: DeepSeek API (deepseek-chat)
- **PDF 解析**: PyPDF
- **OCR**: Tesseract.js (浏览器端，不上传图片)
- **Word 生成**: 浏览器前端生成 .doc 文件
- **部署**: 单服务，适合 Railway / Hugging Face Spaces / 云服务器

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 方式一：创建 .env 文件
echo DEEPSEEK_API_KEY=your_key_here > .env

# 方式二：直接设置环境变量
export DEEPSEEK_API_KEY=your_key_here
```

### 3. 启动服务
```bash
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

## 部署指南

### 所需环境变量
```
DEEPSEEK_API_KEY=sk-xxx  # DeepSeek API 密钥
```

### Railway 部署
```
1. 将代码推送到 GitHub 仓库
2. 在 Railway 创建新项目，连接 GitHub
3. 在项目设置中添加环境变量 DEEPSEEK_API_KEY
4. 启动命令: python main.py
5. Railway 会自动分配域名
```

### Hugging Face Spaces 部署
```
1. 创建 Space → 选择 Docker / 空白
2. 上传代码
3. 在 Settings → Repository Secrets 添加 DEEPSEEK_API_KEY
4. Space 会自动启动并分配域名
```

### 云服务器部署 (Ubuntu)
```bash
# 安装 Python 和依赖
sudo apt update && sudo apt install -y python3 python3-pip
pip install -r requirements.txt

# 设置环境变量
export DEEPSEEK_API_KEY=sk-xxx

# 使用 nohup 后台运行
nohup python main.py > app.log 2>&1 &

# 或使用 systemd 管理（推荐）
```

## 项目结构

```
.
├── main.py           # FastAPI 服务入口
├── backend/
│   ├── __init__.py
│   └── prompts.py    # Prompt 模板
├── static/
│   └── index.html    # 前端页面（单页应用）
├── .env              # 环境变量（不上传 Git）
├── requirements.txt
├── README.md
└── .gitignore
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| POST | `/analyze` | 简历分析 |
| POST | `/rewrite-resume` | 简历优化 |
| GET | `/health` | 健康检查 |

## 隐私说明

- 不上传简历或图片到任何第三方服务器（AI 分析仅调用 DeepSeek API 发送文本）
- OCR 识别在浏览器本地完成，图片不会离开你的设备
- 不保存用户文件，服务重启后数据自动清除
