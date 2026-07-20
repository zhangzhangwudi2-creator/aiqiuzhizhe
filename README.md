# AI 求职助手

面向实习与校招场景的简历–岗位匹配工具。用户上传 PDF 简历并输入岗位描述（JD）后，系统调用 DeepSeek 生成结构化匹配分析，也可以在不改动事实的前提下生成针对岗位的简历改写稿。

## 在线功能

- PDF 简历解析与内容长度控制
- JD 文本输入，或在浏览器端使用 Tesseract.js 识别多张截图
- 匹配度、优势、技能缺口、简历建议和面试问题的结构化分析
- 针对目标岗位生成简历改写稿
- 复制改写结果，或下载 Word 兼容的 `.doc` 文件
- 无需注册；服务端不持久化简历文件
- 同一输入结果缓存 6 小时，重复查看不再次消耗模型额度
- 默认每个 IP 每小时最多 5 次未命中缓存的 AI 调用

## 数据与隐私

- JD 截图的 OCR 在浏览器内执行，截图不会上传到服务端。
- PDF 会上传到本服务以提取文字，但不会被持久化保存。
- 提取出的简历文字和 JD 会发送给 DeepSeek API 完成分析或改写。
- 请勿上传身份证号、家庭住址等完成岗位分析不需要的敏感信息。

## 技术栈

- 后端：Python、FastAPI、AsyncOpenAI
- 模型：DeepSeek `deepseek-chat`
- PDF：PyPDF
- OCR：Tesseract.js（浏览器端）
- 前端：原生 HTML、CSS、JavaScript
- 部署：Railway / Nixpacks
- 测试：Pytest

## 当前架构

```text
.
├── main.py                # 当前部署入口与 API
├── prompts.py             # 分析、改写 Prompt
├── static/
│   └── index.html         # 当前线上前端
├── tests/
│   └── test_main.py       # 核心输入校验测试
├── evaluation/            # 不调用 API 的结构评测样例
├── scripts/
│   └── evaluate_outputs.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── nixpacks.toml
```

仓库中的 `backend/` 和 `frontend/` 是早期未完成的架构实验，不属于当前部署版本，其中包含模拟存储和模拟响应。为保留演进记录暂未删除，后续会在确认迁移价值后归档或移除。

## 本地运行

需要 Python 3.10 或更高版本。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 中填写：

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
```

启动：

```powershell
python main.py
```

访问 `http://localhost:8000`。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 前端页面 |
| `POST` | `/analyze` | 简历与 JD 匹配分析 |
| `POST` | `/rewrite-resume` | 针对 JD 改写简历 |
| `GET` | `/health` | 服务和 AI 配置状态 |

上传限制：PDF 最大 10MB；提取后的简历最多使用 30,000 字符；JD 最多 15,000 字符。

## 测试

```powershell
pip install -r requirements-dev.txt
pytest -q
```

测试覆盖空 JD、超长 JD、错误文件类型、损坏 PDF 和无文字 PDF 等边界情况。

不消耗模型额度的离线输出结构评测：

```powershell
python scripts/evaluate_outputs.py
```

当前离线评测只验证输出契约和字段完整性，不声称能够证明内容质量。后续会增加人工标注的质量评分。

## 后续计划

- 增加 Prompt 版本与人工标注评测集，验证内容质量
- 将单机内存限流升级为持久化限流（适用于多实例部署）
- 增加端到端接口测试
- 归档未使用的旧版目录
