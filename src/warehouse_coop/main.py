"""程序入口：warehouse_coop CLI。

用法示例：
    python -m warehouse_coop run --input data/sample_wave.json
    python -m warehouse_coop verify --wave WAVE-20261023-042 --input data/sample_wave.json
    python -m warehouse_coop metrics --input data/sample_wave.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from warehouse_coop.core.metrics import MetricsConfig
from warehouse_coop.core.pipeline import Task, WarehouseCoopAssistant


def _load(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"找不到输入文件：{p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _build_task(data: Dict[str, Any], node: str) -> Task:
    wave = data.get("wave", {})
    return Task(
        wave_no=wave.get("wave_no", "WAVE-?"),
        orders=wave.get("orders", []),
        cancel_events=data.get("cancel_events", []),
        sku_adjacency=data.get("sku_adjacency", {}),
        records=data.get("records", []),
    )


def _metrics_config(data: Dict[str, Any]) -> MetricsConfig:
    m = data.get("metrics", {})
    return MetricsConfig(
        denominator=m.get("denominator", "ship_orders"),
        exclude_rules=m.get("exclude_rules", []),
        period=m.get("period", "trial"),
        reporter=m.get("reporter", ""),
        confirmed=bool(m.get("confirmed", False)),
    )


def _pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def cmd_run(args: argparse.Namespace) -> int:
    data = _load(args.input)
    task = _build_task(data, args.node)
    assistant = WarehouseCoopAssistant(node=args.node)
    result = assistant.run(task, _metrics_config(data))
    print(_pretty(WarehouseCoopAssistant.to_summary(result)))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    data = _load(args.input)
    task = _build_task(data, args.node)
    assistant = WarehouseCoopAssistant(node=args.node)
    result = assistant.run(task, _metrics_config(data))
    # 按业务编号筛出交接清单
    items = result.handover.items
    matched = [i for i in items if i.business_no == args.wave] or items
    out = [
        {"business_no": i.business_no, "version": i.version,
         "status": i.status, "open_items": i.open_items,
         "owner": i.owner, "acknowledged": i.acknowledged}
        for i in matched
    ]
    print(_pretty(out))
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    data = _load(args.input)
    task = _build_task(data, args.node)
    assistant = WarehouseCoopAssistant(node=args.node)
    result = assistant.run(task, _metrics_config(data))
    m = result.metrics
    print(_pretty({
        "denominator": m.config.denominator,
        "period": m.config.period,
        "reporter": m.config.reporter,
        "config_confirmed": m.config.confirmed,
        "misplace_rate": m.misplace_rate,
        "missing_scans": m.missing_scans,
        "miss_scan_zero": m.miss_scan_zero,
        "note": "口径未书面固定前，验收不可签字（f42、f53）" if not m.config.confirmed else "",
    }))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warehouse_coop",
        description="仓内拣选与装车核验 · 协同助手（FDE 合成业务场景）",
    )
    parser.add_argument("--version", action="version",
                        version="warehouse_coop 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    def _common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--input", default="data/sample_wave.json",
                       help="输入 JSON 数据文件路径")
        p.add_argument("--node", default="review",
                       choices=["review", "load"],
                       help="取消拦截核验节点：review（复核）/ load（装车扫码）")

    r = sub.add_parser("run", help="跑完整核验流程")
    _common(r)

    v = sub.add_parser("verify", help="查看某笔任务的交接清单")
    _common(v)
    v.add_argument("--wave", default="WAVE-20261023-042",
                   help="业务编号（波次）")

    m = sub.add_parser("metrics", help="口径对齐演练（错发率/漏扫）")
    _common(m)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "verify":
        return cmd_verify(args)
    if args.command == "metrics":
        return cmd_metrics(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
