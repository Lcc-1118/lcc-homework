# 接口说明（CLI / Python API）

## CLI 用法

```bash
python -m warehouse_coop run    --input <file> [--node review|load]
python -m warehouse_coop verify --wave <biz_no> --input <file> [--node ...]
python -m warehouse_coop metrics --input <file> [--node ...]
```

- `--input`：JSON 数据文件（默认 `data/sample_wave.json`）。
- `--node`：取消拦截核验节点，`review`（复核）/ `load`（装车扫码）。
- `--wave`：`verify` 子命令的业务编号（波次）。

### 输出结构

`run` 输出 `to_summary(RunResult)` 的 JSON：

```json
{
  "validation": {"checked": 4, "ok": 2, "repair_queue": 2},
  "cancel_intercept": {"business_no": "...", "action": "block",
                       "cancelled_orders": ["..."], "node": "review",
                       "human_review": true, "reason": "..."},
  "mismatch_reminders": [{"sku": "...", "action": "remind", "similar": [...]}],
  "handover_pending": [{"business_no": "...", "status": "pending",
                        "owner": "波次计划员", "open_items": "..."}],
  "metrics": {"misplace_rate": 0.5, "missing_scans": 0,
              "miss_scan_zero": true, "config_confirmed": false},
  "audit": {"audit": [{"req": "REQ-1", "business_no": "...", ...}]}
}
```

## Python API

```python
from warehouse_coop.core.metrics import MetricsConfig
from warehouse_coop.core.pipeline import Task, WarehouseCoopAssistant

task = Task(wave_no="W1", orders=["O1"], cancel_events=[{"order_no":"O1"}],
            sku_adjacency={}, records=[])
assistant = WarehouseCoopAssistant(node="review")
result = assistant.run(task, MetricsConfig(denominator="ship_orders"))
print(WarehouseCoopAssistant.to_summary(result))
```

## 数据输入契约（`data/sample_wave.json`）

| 顶层字段 | 说明 |
|---|---|
| `wave.wave_no` | 波次编号（业务编号） |
| `wave.orders` | 波次内订单号列表 |
| `cancel_events[].order_no` | 取消事件订单号（源 OMS，延迟约 12 分钟 `f31`） |
| `sku_adjacency` | `{sku: [相似 sku...]}` 相邻货位相似 SKU 映射 |
| `records[]` | 待校验数据：需含 `id`（主编号）、`version`、`scan_at`/`recorded_at` |
| `metrics` | 口径配置：denominator / exclude_rules / period / reporter / confirmed |

## 错误与故障

- 接口中断：使用带时间戳只读快照，界面显示「暂未更新」（`f35`）；
- 重连后按业务编号去重补齐（`utils.snapshot.DedupBuffer`）；
- 主编号/版本/事件时间歧义 → 进人工修复队列（`f33`）。

## 安全边界

- 不写入业务系统、不自动批准（`f32`、`f41`）；
- 不自动操作叉车/盘盈盘亏（`f52`）；
- 审计不记录账号口令或无关个人信息（`f45`）。
