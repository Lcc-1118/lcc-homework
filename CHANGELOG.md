# Changelog

所有值得记录的变更都写在这里。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

## [0.1.0] - 2026-10-23

### Added

- 初始化仓库，按标准 Python 工程框架搭建（`src/`、`tests/`、`examples/`、`scripts/`、`config/`、`data/`、`docs/`、`.github/`）。
- `warehouse_coop` CLI 程序入口：`run` / `verify` / `metrics` 三个子命令。
- 核心业务逻辑：
  - 取消订单拦截（REQ-1，证据 `f11`、`f44`、`f31`）
  - 相似包装 SKU 错配提醒（REQ-2，证据 `f10`、`f14`、`f52`）
  - 交接清单生成（REQ-6，证据 `f23`、`f25`、`f54`）
  - 审计留痕（REQ-4，证据 `f41`、`f45`、`f22`）
  - 口径对齐演练（REQ-3，证据 `f42`、`f53`）
  - 数据主编号/版本校验、故障只读快照与去重补齐（REQ-5，证据 `f30`~`f35`）
- 单元测试 `tests/`、可运行示例 `examples/demo.py`、样例数据 `data/sample_wave.json`。
- GitHub Actions 持续集成（`.github/workflows/ci.yml`）、Issue/PR 模板。

### Security

- 所有输入均视为不可信：主编号/版本歧义记录进人工修复队列，不进自动推荐样本（`f33`）。
- 不写入业务系统、不自动批准、不自动操作叉车/盘盈盘亏（`f05`、`f32`、`f41`、`f52`）。
