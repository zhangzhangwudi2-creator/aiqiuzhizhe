---
name: aiqiuzhizhe-incident-diagnosis
description: 在 aiqiuzhizhe 线上故障排查时使用。触发场景：用户报告"网页打不开""生成失败""接口报错""health 挂""Railway 部署失败""DeepSeek 报错""限流或缓存异常""PDF 上传失败""rewrite 校验误杀"。按固定顺序只读诊断：现象、部署、环境变量存在性（不打印值）、代码路径、日志、影响范围；优先给出最小修复、回滚与验证方案，不直接大改代码。
---

# aiqiuzhizhe-incident-diagnosis

## 适用场景与边界

- 线上不可用、接口报错、部署异常、功能异常时的只读诊断。
- 只诊断，不直接大规模修改代码；确需修复时走 aiqiuzhizhe-develop 小步实现。

## 输入要求

- 用户报告的现象、发生时间、URL 或接口、错误文案。
- 可用的探测权限说明（能否访问线上、是否有 Railway/GitHub 凭证）。

## 排查顺序（固定）

1. 定位现象
   - 记录用户报告的 URL、接口、错误文案、发生时间。
   - 只读复现：`/health`、首页 `GET /`、静态资源 `GET /static/app.css`。
2. 检查部署状态
   - GitHub main 最新提交；最近一次 GitHub Actions 运行结果。
   - Railway 是否完成部署（线上内容是否与最新提交匹配）。
3. 检查环境变量存在性（不打印值）
   - `DEEPSEEK_API_KEY`（通过 `/health` 的 `ai_configured` 判断）、`TRUST_X_FORWARDED_FOR`、`RATE_LIMIT_*`、`CACHE_TTL_SECONDS`、`CORS_ORIGINS`。
4. 按错误分类查代码路径
   - 429：限流（`quota.py`、`_client_identity`）；503：未配置 Key（`_get_client`）；502：DeepSeek 异常/空内容/JSON 格式异常/事实校验失败（`fact_guard.py`）；400/413：PDF/JD 校验。
   - PDF 上传失败：`_parse_resume` 与 pypdf；rewrite 误杀：`validate_rewrite_facts`。
5. 看日志
   - 服务日志与错误日志；无结构化日志时用线上最小探测代替，不得编造日志内容。
6. 判断影响范围
   - 单接口 / 全站 / 单用户 / 全部用户。

## 输出要求

- 根因假设 + 证据（代码行为或探测结果）
- 最小修复方案、回滚方案、验证步骤
- 需要用户确认的事项（如环境变量、真实 API 状态）

## 禁止事项

- 禁止一上来大改代码。
- 禁止打印或提交 API Key、简历内容等敏感信息。
- 禁止为了诊断调用付费 API；必须调用时先征得用户同意并最小化。
- 禁止把猜测写成结论。

## 最终汇报格式

- 现象
- 排查过程（做了什么探测）
- 根因与证据
- 影响范围
- 建议的最小修复 / 回滚 / 验证步骤
