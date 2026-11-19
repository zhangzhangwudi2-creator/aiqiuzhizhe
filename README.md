# AI 求职助手 (`aiqiuzhizhe`)

基于 **FastAPI + ReportLab + Tesseract.js** 的简历诊断、定向改写与保真 PDF 导出工具。  
在线作品集演示与项目说明：[cv.zfzs.lol](https://cv.zfzs.lol)

![AI 求职助手界面](https://cv.zfzs.lol/media/job-helper-ui.jpg)

## 解决的实际问题

1. **防止大模型改写简历时乱删或编造信息（`fact_guard.py`）**
   - 使用 `<TARGET_ROLE>`、`<UNTRUSTED_RESUME>`、`<UNTRUSTED_JOB_DESCRIPTION>` XML 标签隔离不可信输入，降低提示词注入风险。
   - 改写完成后用确定性规则校验原简历的手机号、邮箱、URL 不丢失且无常见捏造实体；不通过时附带具体原因重试 1 次，仍失败直接返回 `HTTP 502` 且绝不写入缓存。
2. **防绕过限流与缓存省额度（`quota.py`）**
   - 请求参数做规范化 SHA-256 哈希，命中 6 小时 `TTLCache` 直接返回结果。
   - 修复了取 `X-Forwarded-For` 首跳会被客户端伪造请求头绕过的问题：在信任代理模式下取最右可信跳实施滑动窗口限流（5 次/小时）。
3. **浏览器端 OCR 与中文 PDF 稳定导出（`pdf_resume.py`）**
   - 前端集成 `Tesseract.js` 识别招聘网站 JD 截图，不消耗服务端算力，同时保留纯文本粘贴兜底。
   - 后端使用 ReportLab 嵌入 `NotoSansSC` 字体排版；提取不到原简历证件照时显式返回 `HTTP 422` 拒绝静默丢照，双栏 `LayoutError` 时自动降级单栏稳定模板。

## 自动化测试

项目内置 **63 项 `pytest`** 回归测试（覆盖限流边界、`X-Forwarded-For` 伪造反例、`fact_guard` 拦截重试、文本输入校验与 PDF 导出契约），并配置了 GitHub Actions CI：

```bash
pip install -r requirements.txt
pytest -q
# 63 passed in ~3s
```

## 当前边界与说明

- 缓存与限流目前保存在单进程内存中（重启清零），适合个人展示和轻量场景；如需多实例部署可替换为 Redis。
- 早期曾实验过一个 PyInstaller 桌面封装原型，因体积膨胀至 150MB+ 且前端未闭环已弃用，目前以 FastAPI Web 生产版为主线。
