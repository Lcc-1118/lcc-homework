"""口径对齐与指标核算（REQ-3，证据 f00、f02、f42、f50、f53、f51）。

验收硬线：错发率下降且复核漏扫为零。仓库按出库算完成、配送站按正确收货算完成，
取消订单责任有分歧（f50、f53）。本模块用「固定分母、排除规则、统计周期、出数人」
的口径对同一批数据做可复算核算；分母/排除规则未书面固定前，结果标为待确认。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MetricsConfig:
    """统计口径配置（f42、f53）。"""

    denominator: str          # 分母口径：pick_lines / ship_orders / delivered_orders
    exclude_rules: List[str] = field(default_factory=list)  # 排除规则
    period: str = "trial"     # 统计周期：trial（整段试点）/ shift（单班次）
    reporter: str = ""        # 出数人（未定）
    confirmed: bool = False   # 口径是否已书面固定（未固定前不可签字）


@dataclass
class MetricsResult:
    """一次口径对齐核算结果。"""

    config: MetricsConfig
    shipped: int = 0          # 出库/装车笔数
    misplaced: int = 0        # 错发笔数
    scanned: int = 0          # 已复核扫码笔数
    missing_scans: int = 0    # 复核漏扫笔数
    total_lines: int = 0

    @property
    def misplace_rate(self) -> float | None:
        if self.shipped == 0:
            return None
        return self.misplaced / self.shipped

    @property
    def miss_scan_zero(self) -> bool:
        """漏扫为零是硬门槛（f02、f42）。"""
        return self.missing_scans == 0


def compute_metrics(shipped: int, misplaced: int,
                    scanned: int, total_lines: int,
                    config: MetricsConfig) -> MetricsResult:
    """按口径核算指标。"""
    result = MetricsResult(
        config=config, shipped=shipped, misplaced=misplaced,
        scanned=scanned, total_lines=total_lines,
    )
    result.missing_scans = total_lines - scanned if scanned <= total_lines else 0
    return result
