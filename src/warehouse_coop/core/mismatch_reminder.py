"""相似包装 SKU 错配提醒（REQ-2，证据 f10、f14、f52、f33、f21）。

拣货员明确相似包装 SKU 相邻货位、新员工常拿错规格（f10），
关键说明未随单据交接（f14）。范围限定为扫码解释和错配提醒，
不自动操作叉车或盘盈盘亏（f52）。必须显示对应原记录与待确认字段（f15）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Reminder:
    """一条扫码错配提醒。"""

    sku: str
    action: str                    # "remind" | "pass"
    similar_skus: List[str] = field(default_factory=list)
    show_original: bool = True     # 显示原记录（f15）
    show_pending_fields: bool = True  # 显示待确认字段（f15）
    auto_operate: bool = False     # 不自动操作叉车/盘盈盘亏（f52）
    note: str = ""


class MismatchReminder:
    """根据货位相邻关系给出相似 SKU 扫码解释与错配提醒。

    :param adjacency: {sku: [similar_sku...]} 相邻货位的相似 SKU 映射。
    """

    def __init__(self, adjacency: Dict[str, List[str]]):
        self.adjacency = adjacency

    def scan(self, sku: str) -> Reminder:
        similar = self.adjacency.get(sku, [])
        if similar:
            return Reminder(
                sku=sku, action="remind", similar_skus=similar,
                note="相似包装 SKU 位于相邻货位，请核对规格（f10）",
            )
        return Reminder(sku=sku, action="pass", note="无相邻相似 SKU")
