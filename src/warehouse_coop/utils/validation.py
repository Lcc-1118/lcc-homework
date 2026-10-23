"""数据口径校验（REQ-5）。

对 SKU 图片、货位表、波次、复核、装车事件里的「主编号 / 事件时间 / 版本字段」
做校验，歧义记录进人工修复队列，不进入自动推荐样本（证据 f33、f30~f35）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# 事件时间口径：扫码时间 or 系统落库时间（待业务确认，f42）
EVENT_TIME_KEYS = ("scan_at", "recorded_at")


@dataclass
class ValidationIssue:
    """一条数据校验问题。"""

    record_id: str
    source: str          # 资料类型：sku / location / wave / review / load
    issue_type: str      # missing_key / version_conflict / master_key_conflict / bad_time
    detail: str
    # 校验通过？否则进人工修复队列
    recoverable: bool = True


@dataclass
class ValidationResult:
    """一次数据校验的整体结果。"""

    checked: int = 0
    ok: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    repair_queue: List[ValidationIssue] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        """无歧义记录、可直接进入自动推荐样本。"""
        return self.ok == self.checked and not self.repair_queue


def _has_key(rec: Dict[str, Any], keys: List[str]) -> bool:
    return any(k in rec for k in keys)


def validate_record(rec: Dict[str, Any], source: str,
                    master_key: str = "id",
                    version_key: str = "version") -> ValidationIssue | None:
    """校验单条记录的主编号、版本、事件时间字段。

    事件时间只要存在一个（scan_at 或 recorded_at）即视为可取；
    版本缺失或主编号缺失视为歧义，进人工修复队列。
    """
    has_master = _has_key(rec, [master_key])
    has_version = _has_key(rec, [version_key])
    has_time = _has_key(rec, list(EVENT_TIME_KEYS))

    if not has_master:
        return ValidationIssue(
            record_id=str(rec.get("_row", "?")), source=source,
            issue_type="master_key_conflict",
            detail=f"缺少主编号字段 '{master_key}'",
        )
    if not has_version:
        return ValidationIssue(
            record_id=str(rec[master_key]), source=source,
            issue_type="version_conflict",
            detail=f"缺少版本字段 '{version_key}'",
        )
    if not has_time:
        return ValidationIssue(
            record_id=str(rec[master_key]), source=source,
            issue_type="bad_time",
            detail=f"缺少事件时间字段（{EVENT_TIME_KEYS}）",
        )
    return None


def validate_all(records: List[Dict[str, Any]], source: str) -> ValidationResult:
    """批量校验一组记录。"""
    result = ValidationResult()
    result.checked = len(records)
    for rec in records:
        issue = validate_record(rec, source)
        if issue is None:
            result.ok += 1
        else:
            result.issues.append(issue)
            result.repair_queue.append(issue)  # 歧义进人工修复队列（f33）
    return result
