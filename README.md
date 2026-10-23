# warehouse-coop · 仓内拣选与装车核验协同助手

围绕「仓内拣选与装车核验」的 FDE（Forward Deployed Engineering）训练项目产物。本仓库将需求发现阶段的访谈事实（`logistics-warehouse-f00` ~ `f55`）落成一个**可运行的 Python 命令行协同助手**：对一笔合成拣选—装车任务，自动完成**取消订单拦截**、**相似包装 SKU 错配提醒**、**交接清单生成**与**审计留痕**，并在不可逆动作前转入人工确认。

> 合成业务场景训练项目：仅处理本项目授权合成样本，不写入真实业务系统、不自动批准、不自动操作叉车或盘盈盘亏。真实接口与业务验收需另行核实。

## 它解决什么

远川物流在「仓内拣选与装车核验」上投入了大量人力，核心瓶颈（详见 `00-项目证据与需求发现报告.md`）：

| 需求 | 问题 | 证据 |
|---|---|---|
| REQ-1 | 取消订单已进波次、拣完仍被装车、到站才发现 | `f11`、`f44`、`f31` |
| REQ-2 | 相似包装 SKU 相邻货位，新员工常拿错规格 | `f10`、`f14`、`f52` |
| REQ-3 | 错发率/漏扫口径不定则验收无法签字 | `f00`、`f42`、`f53` |
| REQ-4 | AI 提示最终放行责任与审批矩阵未定 | `f41`、`f22` |
| REQ-5 | 数据口径与接口治理，故障期需人工兜底 | `f30`~`f35` |
| REQ-6 | 跨岗交接需绑定原业务编号与资料版本 | `f23`、`f25`、`f54`、`f55` |

## 快速开始

### 环境要求

- Python 3.10+
- 无第三方运行时依赖（标准库即可运行；`requirements.txt` 仅为开发/测试占位）

### 安装

```bash
# 1. 克隆
git clone https://github.com/Lcc-1118/lcc-homework.git
cd lcc-homework

# 2.（可选）创建虚拟环境
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. 安装（本地开发模式）
pip install -e .
```

### 运行 Demo

```bash
# 跑内置合成样本，走完整「波次 → 拣选 → 复核 → 装车」核验流程
python -m warehouse_coop run --input data/sample_wave.json

# 只看某一笔任务的交接清单
python -m warehouse_coop verify --wave WAVE-20261023-042 --input data/sample_wave.json

# 口径对齐演练（错发率/漏扫，同批数据两岗可复算）
python -m warehouse_coop metrics --input data/sample_wave.json
```

也可以直接运行示例脚本（效果一致）：

```bash
python examples/demo.py
```

## 测试

```bash
# 运行全部单元测试
python -m pytest tests/ -v

# 或无需 pytest（标准库 unittest）
python -m unittest discover -s tests
```

## 目录结构

```
warehouse-coop/
├── README.md               # 本文件：项目门面
├── LICENSE                 # MIT 许可证
├── .gitignore              # 忽略依赖/缓存/密钥
├── CHANGELOG.md            # 版本更新记录
├── CONTRIBUTING.md         # 贡献指南
├── requirements.txt        # 依赖清单
├── src/
│   └── warehouse_coop/
│       ├── __init__.py     # 包入口
│       ├── main.py         # CLI 程序入口
│       ├── core/           # 核心业务逻辑（拦截/提醒/交接/审计/口径）
│       └── utils/          # 通用工具（校验/快照/去重/日志）
├── docs/                   # 设计说明、接口说明
│   ├── design.md
│   └── api.md
├── tests/                  # 测试代码
├── examples/               # 可运行示例
├── scripts/                # 构建/部署脚本
├── config/                 # 非机密配置
├── data/                   # 样例数据
└── .github/                # CI/CD 与模板
```

## 边界说明（不做什么）

- **不自动操作叉车**、不做盘盈盘亏（`f05`、`f52`）；
- **不写入业务系统**、不自动批准（`f32`、`f41`）；
- 取消单/资料缺依据/版本冲突/系统不可用时**转人工**，标注触发原因、接手人、确认时间（`f44`）；
- 波次计划员不代替安全主管完成专业签核（`f22`）。

## License

[MIT](LICENSE)

---

本项目为 FDE 训练中心合成业务场景产物，方法框架参考 [fde-simulation](https://github.com/kalyvask/fde-simulation)。
