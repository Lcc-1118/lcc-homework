#!/usr/bin/env bash
# deploy.sh — 部署/推送脚本：发布到 GitHub main 分支
set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="${1:-main}"

echo "[deploy] 运行测试"
python -m unittest discover -s tests -v

echo "[deploy] 提交并推送至 origin/$BRANCH"
git add -A
git commit -m "chore(deploy): 更新 warehouse-coop 交付" || echo "[deploy] 无变更，跳过提交"
git push -u origin HEAD:"$BRANCH"

echo "[deploy] 完成 → https://github.com/Lcc-1118/lcc-homework"
