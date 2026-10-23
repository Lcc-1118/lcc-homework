"""核心逻辑单元测试。

可用标准库 unittest 运行：
    python -m unittest discover -s tests
或用 pytest：
    python -m pytest tests/ -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from warehouse_coop.core.cancel_interceptor import CancelInterceptor
from warehouse_coop.core.handover import HandoverItem, HandoverList
from warehouse_coop.core.metrics import MetricsConfig, compute_metrics
from warehouse_coop.core.mismatch_reminder import MismatchReminder
from warehouse_coop.core.pipeline import Task, WarehouseCoopAssistant
from warehouse_coop.utils.audit import AuditEntry, AuditLog
from warehouse_coop.utils.snapshot import DedupBuffer
from warehouse_coop.utils.validation import validate_all


class TestCancelInterceptor(unittest.TestCase):
    def test_block_cancelled_wave(self):
        ic = CancelInterceptor([{"order_no": "O2"}], node="review")
        d = ic.check_wave({"wave_no": "W1", "orders": ["O1", "O2"]})
        self.assertEqual(d.action, "block")
        self.assertEqual(d.cancelled_orders, ["O2"])
        self.assertTrue(d.human_review)

    def test_pass_clean_wave(self):
        ic = CancelInterceptor([{"order_no": "O9"}], node="load")
        d = ic.check_wave({"wave_no": "W2", "orders": ["O1"]})
        self.assertEqual(d.action, "pass")


class TestMismatchReminder(unittest.TestCase):
    def test_remind_adjacent(self):
        r = MismatchReminder({"SKU-A500": ["SKU-A500L"]})
        out = r.scan("SKU-A500")
        self.assertEqual(out.action, "remind")
        self.assertFalse(out.auto_operate)  # 不自动操作叉车（f52）

    def test_pass_nonadjacent(self):
        r = MismatchReminder({"SKU-A500": ["SKU-A500L"]})
        self.assertEqual(r.scan("SKU-X1").action, "pass")


class TestHandover(unittest.TestCase):
    def test_acknowledge_required(self):
        hl = HandoverList()
        hl.add(HandoverItem(business_no="O1", version="v1", status="pending",
                            open_items="待复核", owner="波次计划员"))
        self.assertEqual(len(hl.pending()), 1)
        self.assertTrue(hl.acknowledge("O1"))
        self.assertEqual(len(hl.pending()), 0)  # 确认接手才结束待办（f23）


class TestMetrics(unittest.TestCase):
    def test_miss_scan_zero_hard_gate(self):
        cfg = MetricsConfig(denominator="ship_orders", confirmed=False)
        res = compute_metrics(shipped=10, misplaced=1, scanned=10, total_lines=10,
                              config=cfg)
        self.assertEqual(res.missing_scans, 0)
        self.assertTrue(res.miss_scan_zero)
        self.assertAlmostEqual(res.misplace_rate, 0.1)

    def test_confirmed_flag(self):
        cfg = MetricsConfig(denominator="ship_orders", confirmed=False)
        res = compute_metrics(10, 1, 10, 10, cfg)
        self.assertFalse(res.config.confirmed)  # 未固定前不可签字（f42）


class TestValidation(unittest.TestCase):
    def test_missing_version_goes_to_repair(self):
        res = validate_all([{"id": "R1", "scan_at": "t"}], source="wave")
        self.assertGreaterEqual(len(res.repair_queue), 1)
        self.assertNotEqual(res.ok, res.checked)


class TestDedup(unittest.TestCase):
    def test_no_repeat(self):
        db = DedupBuffer()
        self.assertTrue(db.add_if_missing("O1", {}))
        self.assertFalse(db.add_if_missing("O1", {}))  # 去重（f35）


class TestAudit(unittest.TestCase):
    def test_audit_reconstruct(self):
        log = AuditLog()
        log.record(AuditEntry(req="REQ-1", business_no="W1", version="v1",
                              fact_refs=["logistics-warehouse-f11"], result="block",
                              signer="波次计划员"))
        self.assertEqual(len(log.find_by_business_no("W1")), 1)


class TestPipeline(unittest.TestCase):
    def test_full_run(self):
        task = Task(
            wave_no="W1", orders=["O1", "O2"],
            cancel_events=[{"order_no": "O2"}],
            sku_adjacency={"SKU-A": ["SKU-AL"]},
            records=[{"id": "R1", "version": "v1", "scan_at": "t"}],
        )
        assistant = WarehouseCoopAssistant()
        res = assistant.run(task, MetricsConfig(denominator="ship_orders"))
        self.assertEqual(res.intercept.action, "block")
        summary = WarehouseCoopAssistant.to_summary(res)
        self.assertIn("audit", summary)


if __name__ == "__main__":
    unittest.main()
