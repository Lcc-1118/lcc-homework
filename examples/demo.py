"""可运行示例：跑内置合成样本，走完整核验流程。

用法：
    python examples/demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

from warehouse_coop.core.metrics import MetricsConfig
from warehouse_coop.core.pipeline import Task, WarehouseCoopAssistant

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_wave.json"


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    wave = data["wave"]
    task = Task(
        wave_no=wave["wave_no"],
        orders=wave["orders"],
        cancel_events=data.get("cancel_events", []),
        sku_adjacency=data.get("sku_adjacency", {}),
        records=data.get("records", []),
    )
    metrics_config = MetricsConfig(
        denominator=data["metrics"]["denominator"],
        exclude_rules=data["metrics"]["exclude_rules"],
        period=data["metrics"]["period"],
        reporter=data["metrics"]["reporter"],
        confirmed=data["metrics"]["confirmed"],
    )

    assistant = WarehouseCoopAssistant(node="review")
    result = assistant.run(task, metrics_config)

    print("=" * 60)
    print(f"仓内拣选与装车核验 · 协同助手 — 波次 {task.wave_no}")
    print("=" * 60)

    v = result.validation
    print(f"\n[1] 数据口径校验（REQ-5）")
    print(f"    检查 {v.checked} 条，通过 {v.ok} 条，进人工修复队列 {len(v.repair_queue)} 条")
    for issue in v.repair_queue:
        print(f"    - [{issue.issue_type}] {issue.source}: {issue.detail}")

    it = result.intercept
    print(f"\n[2] 取消订单拦截（REQ-1）@ {it.node}")
    print(f"    结果: {it.action.upper()} | 取消单: {it.cancelled_orders or '无'}")
    print(f"    转人工: {it.human_review} | 原因: {it.reason}")

    print(f"\n[3] 相似 SKU 错配提醒（REQ-2）")
    for r in result.reminders:
        if r.action == "remind":
            print(f"    - {r.sku} → 提醒: {r.similar_skus} | {r.note}")
        else:
            print(f"    - {r.sku} → 放行")

    print(f"\n[4] 交接清单（REQ-6）— 待确认 {len(result.handover.pending())} 项")
    for it in result.handover.pending():
        print(f"    - {it.business_no} [{it.status}] owner={it.owner} | {it.open_items}")

    m = result.metrics
    print(f"\n[5] 口径核算（REQ-3）")
    print(f"    错发率: {m.misplace_rate} | 漏扫: {m.missing_scans} | 漏扫为零: {m.miss_scan_zero}")
    print(f"    口径已书面固定: {m.config.confirmed}（未固定前验收不可签字，f42）")

    print(f"\n[6] 审计留痕（REQ-4）— {len(result.audit.entries())} 条")
    print(result.audit.to_json())
    print("\n提示：输出仅提示 + 人工确认，不自动放行、不写入业务系统（f05、f32、f41、f52）。")


if __name__ == "__main__":
    main()
