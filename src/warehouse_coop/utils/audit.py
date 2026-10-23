"""审计留痕（REQ-4，证据 f41、f45、f22）。

每次建议保留业务编号、资料版本、事实引用、建议结果、人工改动和签核人，
审计时能重建本次处理；不记录账号口令或不必要个人信息。
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class AuditEntry:
    """一条审计记录。"""

    req: str                # 需求编号，如 REQ-1
    business_no: str        # 业务编号
    version: str            # 资料版本
    fact_refs: List[str]    # 证据引用，如 ["logistics-warehouse-f11"]
    result: str             # 建议结果
    human_edit: str = ""    # 人工改动（可空）
    signer: str = ""        # 签核人
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditLog:
    """可重建处理链的审计日志。"""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def find_by_business_no(self, business_no: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.business_no == business_no]

    def to_json(self) -> str:
        return json.dumps(
            {"audit": [e.to_dict() for e in self._entries]},
            ensure_ascii=False, indent=2,
        )
