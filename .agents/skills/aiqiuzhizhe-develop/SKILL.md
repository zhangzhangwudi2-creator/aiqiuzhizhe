---
name: aiqiuzhizhe-develop
description: 在 aiqiuzhizhe 仓库执行中等粒度功能开发、缺陷修复或补测试时使用。触发场景：用户说"继续开发""实现 XXX""修复 XXX""接着做""补测试"，且目标代码在本仓库。要求先读代码、明确允许和禁止修改的文件、小步修改、补测试、运行验证命令并汇报实际结果。
---

# aiqiuzhizhe-develop

## 适用场景

- 为 AI 求职助手（FastAPI + DeepSeek + 前端单页）实现新功能或修复缺陷。
- 补测试、调整 Prompt 安全边界、事实一致性校验等已有模块的小步演进。
- 本 skill 用于中等粒度开发；大规模重构或跨模块改动应先拆小再执行。

## 输入要求

- 明确本次任务的输入、输出、边界和验收条件后再动手。
- 任务描述含糊时，先给出假设并在汇报中标明，不静默扩大范围。

## 开始前必须阅读

- `main.py`（接口、DeepSeek 调用、限流、缓存、事实校验接入点）
- `prompts.py`、`schemas.py`、`quota.py`、`pdf_resume.py`、`fact_guard.py`
- `static/index.html`（仅当改动涉及前端时）
- `tests/` 下相关测试与 `evaluation/`、`README.md`
- `git status` 与 `git log --oneline -5`，确认当前分支和未提交改动

## 允许修改 / 禁止修改

- 允许：任务明确指出的文件；为完成任务必须新增的测试文件。
- 禁止：前端页面与 CSS、PDF 导出、限流逻辑、target_role 自动推断、`requirements.txt`、部署配置，除非任务明确要求。
- 禁止无关重构、格式化大改和顺手修改无关文件。
- 禁止引入新依赖，除非任务明确要求。

## 执行步骤

1. 阅读相关代码与测试，确认现状。
2. 用一句话写清本次改动范围和验收条件。
3. 小步修改，保持接口兼容；不要一次重写整条链路。
4. 为每个新行为补测试（单测或接口级 mock 测试）。
5. 运行验证：
   - `.venv/Scripts/python.exe -m pytest -q`
   - `.venv/Scripts/python.exe -m compileall -q .`
   - `.venv/Scripts/python.exe scripts/evaluate_outputs.py`
6. 有真实 API 调用风险的操作只允许最小化冒烟，禁止压测。

## 禁止事项

- 禁止调用付费 API 做常规测试；测试一律用 monkeypatch / mock。
- 禁止提交 `.env`、API Key、真实简历、日志或运行产物。
- 禁止把 Mock 或接口壳描述成真实服务已接通。
- 未通过验证前，不得描述任务为完成。

## 最终汇报格式

- 修改了哪些文件，每个文件为什么改
- 新增了哪些测试
- 三个验证命令的实际结果（测试数量、编译、评测）
- 是否有风险或未完成项
- 是否已提交（未提交时明确说明）
