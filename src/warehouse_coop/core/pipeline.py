"""协同助手编排（主流程）。

围绕一笔合成拣选—装车任务，按「波次 → 拣选 → 复核 → 装车」流程：
1. 数据口径校验（REQ-5）：主编号/版本/事件时间，歧义进人工修复队列；
2. 取消订单拦截（REQ-1）：复核/装车节点检出取消单 → 转人工；
3. 相似 SKU 错配提醒（REQ-2）：扫码解释与提醒，不自动操作；
4. 交接清单（REQ-6）：生成待人工复核的交接草稿；
5. 审计留痕（REQ-4）：每条建议记录来源与签核人。

输出后进入人工确认：不自动放行、不写入业务系统（f05、f32、f41、f52）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from warehouse_coop.core.cancel_interceptor import CancelInterceptor, InterceptDecision
from warehouse_coop.core.handover import HandoverItem, HandoverList
from warehouse_coop.core.metrics import MetricsConfig, MetricsResult, compute_metrics
from warehouse_coop.core.mismatch_reminder import MismatchReminder, Reminder
from warehouse_coop.utils.audit import AuditEntry, AuditLog
from warehouse_coop.utils.validation import ValidationResult, validate_all


@dataclass
class Task:
    """一笔核验任务（一个波次）。"""

    wave_no: str
    orders: List[str]
    cancel_events: List[Dict] = field(default_factory=list)
    sku_adjacency: Dict[str, List[str]] = field(default_factory=dict)
    records: List[Dict] = field(default_factory=list)  # 待校验数据


@dataclass
class RunResult:
    """一次完整核验的运行结果。"""

    validation: ValidationResult
    intercept: InterceptDecision
    reminders: List[Reminder]
    handover: HandoverList
    audit: AuditLog
    metrics: MetricsResult


class WarehouseCoopAssistant:
    """仓内拣选与装车核验 · 协同助手。"""

    def __init__(self, node: str = "review"):
        self.node = node

    def run(self, task: Task, metrics_config: MetricsConfig,
            reporter_edits: Dict[str, str] | None = None) -> RunResult:
        """执行一笔任务的完整核验。reporter_edits 记录人工改动（审计留痕）。"""
        reporter_edits = reporter_edits or {}

        # 1) 数据口径校验（REQ-5）
        validation = validate_all(task.records, source="wave")

        # 2) 取消订单拦截（REQ-1）
        interceptor = CancelInterceptor(task.cancel_events, node=self.node)
        intercept = interceptor.check_wave({"wave_no": task.wave_no, "orders": task.orders})

        # 3) 相似 SKU 错配提醒（REQ-2）
        reminder = MismatchReminder(task.sku_adjacency)
        reminders = [reminder.scan(o) for o in task.orders]

        # 4) 交接清单（REQ-6）
        handover = HandoverList()
        for o in task.orders:
            open_items = "取消单需波次计划员核对" if o in interceptor.cancelled else "待复核"
            handover.add(HandoverItem(
                business_no=o, version="v0.1", status="pending",
                open_items=open_items, owner="波次计划员",
            ))

        # 5) 审计留痕（REQ-4）
        audit = AuditLog()
        if intercept.action == "block":
            audit.record(AuditEntry(
                req="REQ-1", business_no=intercept.business_no, version="v0.1",
                fact_refs=["logistics-warehouse-f11", "logistics-warehouse-f44",
                           "logistics-warehouse-f31"],
                result="block_cancelled",
                human_edit=reporter_edits.get(intercept.business_no, ""),
                signer="波次计划员",
            ))
        for r in reminders:
            if r.action == "remind":
                audit.record(AuditEntry(
                    req="REQ-2", business_no=r.sku, version="v0.1",
                    fact_refs=["logistics-warehouse-f10", "logistics-warehouse-f14"],
                    result="remind", signer="拣货员",
                ))

        # 6) 口径核算（REQ-3）
        metrics = compute_metrics(
            shipped=len(task.orders),
            misplaced=len(intercept.cancelled_orders),
            scanned=len(task.records),
            total_lines=len(task.orders),
            config=metrics_config,
        )

        return RunResult(
            validation=validation, intercept=intercept, reminders=reminders,
            handover=handover, audit=audit, metrics=metrics,
        )

    @staticmethod
    def to_summary(result: RunResult) -> Dict[str, Any]:
        """把结果压成可打印的摘要。"""
        return {
            "validation": {
                "checked": result.validation.checked,
                "ok": result.validation.ok,
                "repair_queue": len(result.validation.repair_queue),
            },
            "cancel_intercept": {
                "business_no": result.intercept.business_no,
                "action": result.intercept.action,
                "cancelled_orders": result.intercept.cancelled_orders,
                "node": result.intercept.node,
                "human_review": result.intercept.human_review,
                "reason": result.intercept.reason,
            },
            "mismatch_reminders": [
                {"sku": r.sku, "action": r.action, "similar": r.similar_skus}
                for r in result.reminders
            ],
            "handover_pending": [
                {"business_no": it.business_no, "status": it.status,
                 "owner": it.owner, "open_items": it.open_items}
                for it in result.handover.pending()
            ],
            "metrics": {
                "misplace_rate": result.metrics.misplace_rate,
                "missing_scans": result.metrics.missing_scans,
                "miss_scan_zero": result.metrics.miss_scan_zero,
                "config_confirmed": result.metrics.config.confirmed,
            },
            "audit": json.loads(result.audit.to_json()),
        }
