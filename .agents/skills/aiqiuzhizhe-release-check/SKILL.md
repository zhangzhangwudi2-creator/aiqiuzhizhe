---
name: aiqiuzhizhe-release-check
description: 在 aiqiuzhizhe 仓库准备提交、推送、上线前使用。触发场景：用户说"release check""提交前检查""准备提交""上线检查""验收检查""发布"。必须检查 git diff 范围、重跑测试与评测、核对文档、提交推送、验证 Railway 线上健康与核心接口，并汇报 commit hash 与异常。
---

# aiqiuzhizhe-release-check

## 适用场景

- 一个开发阶段完成、准备提交/推送/上线之前。
- 用户明确要求"提交""推送""上线""发布检查"。

## 输入要求

- 先确认当前分支与 `git status`，明确本阶段应包含的文件。
- 区分本阶段改动与历史遗留的未跟踪文件（如 `tmp/`），不得混入提交。

## 执行步骤

1. 检查改动范围
   - `git status` 与 `git diff --stat`
   - 确认只包含本阶段文件；无误改 `main.py`、`prompts.py`、`fact_guard.py`、前端、`requirements.txt`、限流、部署配置等无关模块。
   - 检查未跟踪文件：不得包含 `.env`、密钥、真实简历、日志、大文件。
2. 重跑验证
   - `.venv/Scripts/python.exe -m pytest -q`
   - `.venv/Scripts/python.exe -m compileall -q .`
   - `.venv/Scripts/python.exe scripts/evaluate_outputs.py`
3. 文档同步检查
   - README 中的功能、测试数量、架构树、API 表是否与实际一致；不一致时在本阶段内修正。
4. 提交
   - 只 `git add` 任务相关文件，禁止 `git add .`。
   - commit message 描述实际改动。
5. 推送并上线检查
   - `git push origin main`
   - 等待 Railway 自动部署；轮询 `/health` 与首页直到稳定。
   - 核心接口冒烟：`/analyze`、`/rewrite-resume` 可用最小真实调用或缓存命中验证；禁止大规模压测，避免不必要 API 费用。

## 禁止事项

- 禁止提交密钥、日志、本地产物、真实简历数据。
- 禁止用 Mock 结果冒充线上真实结果。
- 禁止在未跑完验证命令时描述为可以发布。

## 最终汇报格式

- commit hash
- push 是否成功
- Railway 是否部署成功
- 线上 /health 结果与核心接口结果
- 验证命令的实际结果
- 是否有异常
