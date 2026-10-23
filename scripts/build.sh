#!/usr/bin/env bash
# build.sh — 构建/安装脚本（本地开发模式）
set -euo pipefail

# 在项目根目录执行：bash scripts/build.sh
cd "$(dirname "$0")/.."

echo "[build] 安装本地开发模式（-e editable）"
python -m pip install -e .

echo "[build] 校验 import 与版本"
python -c "import warehouse_coop; print('warehouse_coop', warehouse_coop.__version__)"

echo "[build] 完成。运行示例：python examples/demo.py"
