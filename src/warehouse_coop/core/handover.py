"""交接清单生成（REQ-6，证据 f23、f25、f54、f55）。

交接至少包含：业务编号、当前版本、处理状态、未解决事项和接手人；
对方确认接手才结束本岗待办，仅发消息不算完成（f23）。
异常先分派给实际处理人、超时升级仓储经理、跨岗须明确下一责任人（f25）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class HandoverItem:
    """一条交接记录。"""

    business_no: str
    version: str
    status: str            # pending / in_progress / completed
    open_items: str
    owner: str             # 接手人
    acknowledged: bool = False  # 对方确认接手才结束本岗待办（f23）


@dataclass
class HandoverList:
    """一份交接清单。"""

    items: List[HandoverItem] = field(default_factory=list)

    def add(self, item: HandoverItem) -> None:
        self.items.append(item)

    def acknowledge(self, business_no: str) -> bool:
        """接手人确认，结束本岗待办。"""
        for it in self.items:
            if it.business_no == business_no:
                it.acknowledged = True
                it.status = "completed"
                return True
        return False

    def pending(self) -> List[HandoverItem]:
        return [it for it in self.items if not it.acknowledged]
