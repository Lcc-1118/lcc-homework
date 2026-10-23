"""取消订单拦截（REQ-1，证据 f11、f44、f31、f20）。

拣货员与安全主管均提到：取消订单已进波次、拣完后仍被装车、到站才发现，
说明波次分配后到装车扫码之间缺少取消事件的强制拦截点。
本模块在指定核验节点（复核 / 装车扫码）检出波次中已取消订单，
返回「拦截 + 转人工」，不自动放行（f44）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class InterceptDecision:
    """一笔波次/订单的取消拦截判定。"""

    business_no: str            # 业务编号（波次或订单）
    action: str                 # "block" | "pass"
    cancelled_orders: List[str] = field(default_factory=list)
    node: str = "review"        # 核验节点：review（复核）/ load（装车扫码）
    human_review: bool = True   # 一律转人工（f44）
    reason: str = ""


class CancelInterceptor:
    """在波次与装车之间拦截取消订单。

    :param cancel_events: 取消事件列表，每项含 order_no。
    :param sync_delay_min: 取消事件同步延迟（证据 f31 为 12 分钟）。
    """

    def __init__(self, cancel_events: List[Dict], sync_delay_min: int = 12,
                 node: str = "review", order_key: str = "order_no"):
        self.cancelled = {e[order_key] for e in cancel_events}
        self.sync_delay_min = sync_delay_min
        self.node = node
        self.order_key = order_key

    def check_wave(self, wave: Dict) -> InterceptDecision:
        """检查一个波次中的订单是否有已取消的。"""
        orders = wave.get("orders", [])
        cancelled_in_wave = [o for o in orders if o in self.cancelled]
        if cancelled_in_wave:
            return InterceptDecision(
                business_no=wave.get("wave_no", "?"),
                action="block",
                cancelled_orders=cancelled_in_wave,
                node=self.node,
                human_review=True,
                reason=(
                    f"取消订单已进波次（同步延迟约 {self.sync_delay_min} 分钟，f31），"
                    "需波次计划员核对后转人工（f15、f44）"
                ),
            )
        return InterceptDecision(
            business_no=wave.get("wave_no", "?"),
            action="pass",
            node=self.node,
            human_review=False,
            reason="波次中无取消订单",
        )
