# CHANGELOG

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 SemVer。

## [0.2.0] - 2026-09-06
### Added
- 新增 `strategy.py`：设备可达性执行策略方案选择状态层（`list/get/set/temp/clear`），支持全局默认 + 单次任务临时覆盖，状态存外部 `strategy.json`（删 Skill 不丢）。
- 方案状态持久化：默认 `auto`（智能混合择优），用户可选 p1~p5，选中后记住直到下次更改。
- 经验库 `exp.py` 新增 **方案归类维度**（`strategy` 列）：支持 `p1~p5` 单值、逗号多值（如 `p1,p3`）、`auto` 不限；`add/query/list/report/seed/import` 全链路带方案。
- `exp.py` 新增 `strat <id> <策略>`：事后改经验方案归类。
- `SKILL.md` 新增【九、方案选择机制与归类纪律】章节。

### Changed
- `exp.py` 归档逻辑兼容 `strategy` 列，存量经验自动迁移为 `auto`（不逐条改判）。
- `strategy` 与既有 `type`(通用/个人) **双维并存、互不设限**：方案选择不限制经验采集归类。

### Notes
- 版本判定：新增完整功能集且向后兼容 → MINOR → 0.2.0。
- 本包升级需同步源 `skill-data/` 与生效 `skills/` 两处 `SKILL.md`。

## [0.1.0] - 2026-09-05
### Added
- 初始化 smart-screen-nav：uiautomator 动态取坐标 + 每步截图确认 + 命令直达优先。
- 经验库(exp.py / pbook.py / env.py)+ 通用/个人分类 + Playbook 免思考层 + 版本指纹。
