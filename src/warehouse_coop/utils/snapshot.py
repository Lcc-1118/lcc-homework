"""故障只读快照与去重补齐（REQ-5，证据 f35）。

接口中断时：继续使用带时间戳的上一份只读快照，界面显示「暂未更新」；
重连后按业务编号去重补齐，不反复触发同一待办。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Snapshot:
    """带时间戳的只读快照。"""

    timestamp: str
    data: Dict[str, Any]
    stale: bool = False  # True 表示超过更新周期，标「待刷新」（f34）

    def display_banner(self) -> str:
        if self.stale:
            return "暂未更新（已超过更新周期，请以人工复核为准）"
        return "暂未更新"


class DedupBuffer:
    """按业务编号去重补齐，避免重复触发同一待办（f35）。"""

    def __init__(self) -> None:
        self._seen: set = set()

    def is_duplicate(self, biz_no: str) -> bool:
        return biz_no in self._seen

    def mark_seen(self, biz_no: str) -> None:
        self._seen.add(biz_no)

    def add_if_missing(self, biz_no: str, payload: Any) -> bool:
        """若业务编号未处理过则补齐并标记；否则忽略（去重）。"""
        if self.is_duplicate(biz_no):
            return False
        self.mark_seen(biz_no)
        return True


def snapshot_latest(data: Dict[str, Any], timestamp: str) -> Snapshot:
    """生成一份带时间戳的只读快照。"""
    return Snapshot(timestamp=timestamp, data=data)
