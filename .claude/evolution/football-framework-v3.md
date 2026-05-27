# 园中园足彩分析框架 v3.0

> 融合 2026 年 9 篇前沿论文 + 175 个精选 skill 的全系统重建

## v2 → v3 关键升级

| v2 (六维评分) | v3 (层次概率推断) | 依据 |
|--------------|------------------|------|
| D1 赔率区间 1.72-1.85 黄金区 | OO-EPC 概率转换——赔率→真实概率 | Goto et al. (2026), 90,014场验证 |
| D2 盘口变化人工观察 | Market-Calibrated AFT 自动校准 | arXiv 2605.16066, 4.5% ROI |
| D4 欧亚交叉二值判断 | Hybrid 1X2+AH 概率层融合 | desports.com.cn (2026) |
| D5 凯利>1.1 阈值 | Kelly-Bayesian 模型评估——收益=可信度 | Beuoy (2026), arXiv 2602.09982 |
| D6 主任恐惧 gap>0.20 | 不确定性量化 MC Dropout + 可信区间 | MDPI Information 17(1), 2026 |
| 无 | Favourite-Longshot Bias 校正 | Whelan & Hegarty (Oxford, 2026) |
| 无 | 层次 Dixon-Coles Poisson 模型 | 0xNadr/wc2026, 55-58%准确率 |
| 赛后人工校准 | Kelly Bench 基准 + 自动回测 | Grady et al. (2026), arXiv 2604.27865 |
| 无 | 赛中 4.5% ROI 探索层 | Market-Calibrated AFT |

---

## Layer 1: 概率推断核心 (替换 D1+D4+D5)

### 1.1 OO-EPC 赔率→概率转换

```
输入: 百家欧赔 52 家公司即时赔率
输出: 主胜/平局/客胜真实概率

算法:
1. 对齐庄家盈利目标 (Equal Profitability)
2. 扣除庄家抽水 (overround)
3. 输出校准后的三元概率 p_home, p_draw, p_away
4. 52 家公司取中位数 → 市场共识概率
```

### 1.2 层次 Dixon-Coles Poisson 模型

```
log(λ_home) = α + β_home + att[team_h] - def[team_a] + γ * home
log(λ_away) = α + β_away + att[team_a] - def[team_h]

att[i] ~ N(μ_att, σ_att)    # 零和约束
def[i] ~ N(μ_def, σ_def)    # 零和约束

τ-修正: 0-0, 1-0, 0-1, 1-1 四个低分格特殊处理

PyMC + NUTS 采样 → 50,000 后验样本
输出: 进球分布 → 比分概率 → 胜平负概率 + 95% 可信区间
```

### 1.3 市场校准层

```
OO-EPC 概率 (市场共识)
    ↕ 融合 (贝叶斯加权平均)
Poisson 概率 (模型推断)

融合权重 = 模型可信度 / (模型可信度 + 市场效率)
模型可信度 = 近期 Kelly 收益增长率
```

### 1.4 Favourite-Longshot Bias 校正

```
if p_home > 0.65 (强队):
    OO-EPC 概率 * (1 - FL_bias_correction)
    FL_bias_correction = 0.02~0.05 (联赛特定)
    
亚盘市场: FL_bias_correction = 0 (无偏差)
```

---

## Layer 2: 不确定性量化 (替换 D6)

### 2.1 MC Dropout + 可信区间

```
50,000 次 NUTS 后验采样
→ 主胜概率后验分布
→ 95% 高密度区间 (HDI)
→ 区间宽度 = 不确定性度量

if HDI_width > 0.15:
    信号不可靠 → 跳过
elif HDI_width < 0.08:
    高置信度 → 可决策
```

### 2.2 Fractional-Kelly 投注决策

```
f* = (p * b - q) / b    # Kelly 公式
f = f* / divisor         # Fractional (divisor=4→quarter-Kelly)

p = 模型概率
b = 赔率(十进制)
q = 1 - p

if f < 0: 跳过 (无正期望)
if f > 0.25: 上限=0.25 (风控)
```

### 2.3 EV 阈值门控

```
EV = p * (odds - 1) - (1 - p)
if EV < 0.02: 跳过 (期望收益<2%)
if EV > 0.05: 重点关注
```

---

## Layer 3: Kelly-Bayesian 模型评估 (替换赛后校准)

### 3.1 收益增长 = 模型可信度

```
每次预测后:
  if 正确: bankroll *= (1 + f * (odds - 1))
  if 错误: bankroll *= (1 - f)

模型可信度 = 当前bankroll / 初始bankroll

if 可信度 > 1.10: 模型优于随机 → 增加校准权重
if 可信度 < 0.95: 模型劣于随机 → 降低校准权重
```

### 3.2 Kelly Bench 基准

```
每个联赛维持独立 bankroll:
  - 挪超 bankroll
  - 英超 bankroll
  - ...

定期评比:
  - 哪条联赛模型的 bankroll 增长最快?
  - 联赛间参数可以迁移吗?
```

---

## Layer 4: 赛中探索层 (新)

### 4.1 Market-Calibrated AFT

```
Weibull AFT 模型:
  - 校准到 Betfair 开盘价 (捕获赛前市场信息)
  - PSxG 作为时变赛中协变量
  - 输出: 各比分实时概率 + ROI 预估
```

---

## Layer 5: 执行力层 (不变)

### 5.1 数据门禁 (保持)
```
竞彩官方在列表中 + 公司数≥10 + 关键字段完整
```

### 5.2 一致性门禁 (升级)
```
self_check.py 41项 + manuscript-provenance 溯源审计
每一步输出必须显式标注:
  - 哪个函数产生的这个数字
  - 哪个数据源支撑的
  - 什么时间采集的
```

### 5.3 进化反馈环 (新增)
```
赛后:
  evolve.sh snapshot → 记录预测 vs 实际
  dream.sh → 每 N 场整合模式
  
发现偏差 > 阈值:
  self-diagnose.sh → 诊断框架健康度
  chain-runner.sh thinking → 根因分析
  memory-extractor → 持久化教训
```

---

## Layer 6: 数据工程层 (新增)

### 6.1 数据采集管道
```
500.com HTML → parse_odds.py → data-transform → match-db.json
                                   ↓
                             data-engineer (管道自动化)
                                   ↓
                            exploratory-data-analysis (质量评估)
```

### 6.2 多源融合 (未来)
```
500.com (竞彩+百家欧赔+亚盘) → 主数据源
iSports API → 历史比赛数据 (未来)
Betfair Exchange → 市场价格校准 (未来)
```

---

## 技能协作映射

| 框架层 | 触发 Skill 链 |
|--------|-------------|
| 概率推断 | pymc-bayesian-modeling + statistical-analysis + sensitivity-analysis |
| 不确定性量化 | timesfm-forecasting + quant-analyst + estimate-calibrator |
| 模型评估 | backtesting-frameworks + risk-metrics-calculation + risk-manager |
| 赛中探索 | web-scraping + data-transform + exploratory-data-analysis |
| 执行力 | verification-gate + manuscript-provenance + self_check.py |
| 进化反馈 | evolve.sh + dream.sh + self-diagnose.sh + memory-extractor |
| 数据工程 | data-engineer + data-transform + data-validation-patterns |
| 安全防护 | security-review + input-validation (参数化查询) |

---

## 预期指标

| 指标 | v2 | v3 目标 | 依据 |
|------|-----|---------|------|
| 预测准确率 | 未系统测量 | 53-58% | Dixon-Coles 基准 |
| Brier Score | 未测量 | <0.58 | WC2026 Forecaster |
| Skip率 (跳过不买) | 80% | 70-90% | Kelly EV阈值门控 |
| 模型可信度 | 无 | >1.00 (不亏钱) | KellyBench 基准线 |
| ROI (模拟) | 无 | -5% ~ +2% | 赛中4.5% + 赛前-8%区间 |
