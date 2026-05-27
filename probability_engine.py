"""
概率推断引擎 — 融合OO-EPC + 层次Poisson + Kelly评估 + FL偏差校正
基于2026年9篇前沿论文
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import json, math
from typing import Dict, List, Tuple, Optional

# ============================================================
# 模块 1: OO-EPC 赔率→概率转换 (Goto et al., 2026)
# ============================================================

def oo_epc_convert(odds_list: List[Tuple[float, float, float]]) -> Dict[str, float]:
    """
    Odds-Only Equal Profitability Confidence 概率转换

    Args:
        odds_list: [(主胜赔率, 平局赔率, 客胜赔率), ...] 来自多家公司

    Returns:
        {"home": 概率, "draw": 概率, "away": 概率, "overround": 抽水率}
    """
    if not odds_list:
        return {"home": 0.33, "draw": 0.34, "away": 0.33, "overround": 0.0}

    # 1. 每家公司独立转换
    all_probs = []
    for h, d, a in odds_list:
        # 计算隐含概率
        imp_h = 1.0 / h if h > 0 else 0
        imp_d = 1.0 / d if d > 0 else 0
        imp_a = 1.0 / a if a > 0 else 0

        # 庄家抽水 (overround)
        overround = imp_h + imp_d + imp_a

        # 去除抽水，归一化
        if overround > 0:
            prob_h = imp_h / overround
            prob_d = imp_d / overround
            prob_a = imp_a / overround
        else:
            prob_h = prob_d = prob_a = 1/3

        all_probs.append((prob_h, prob_d, prob_a))

    # 2. 取中位数 (市场共识)
    n = len(all_probs)
    sorted_h = sorted(p[0] for p in all_probs)
    sorted_d = sorted(p[1] for p in all_probs)
    sorted_a = sorted(p[2] for p in all_probs)

    median_h = sorted_h[n // 2]
    median_d = sorted_d[n // 2]
    median_a = sorted_a[n // 2]

    # 3. 归一化
    total = median_h + median_d + median_a
    avg_overround = sum(1/h + 1/d + 1/a for h,d,a in odds_list) / n - 1.0

    return {
        "home": round(median_h / total, 4),
        "draw": round(median_d / total, 4),
        "away": round(median_a / total, 4),
        "overround": round(avg_overround, 4)
    }


# ============================================================
# 模块 2: Favourite-Longshot 偏差校正 (Whelan & Hegarty, 2026)
# ============================================================

def correct_fl_bias(prob: float, is_asian_handicap: bool = False) -> float:
    """
    Favourite-Longshot bias 校正

    Args:
        prob: 原始概率
        is_asian_handicap: 是否亚盘市场 (亚盘无FL偏差)

    Returns:
        校正后概率
    """
    if is_asian_handicap:
        return prob  # 亚盘市场无FL偏差

    if prob > 0.65:  # 强队 (favourite)
        # 高估校正: 热门方被系统性低估赔率
        correction = 0.03  # 联赛通用, 可后续联赛特定校准
        return prob * (1 - correction)
    elif prob < 0.30:  # 弱队 (longshot)
        # 低估校正: 冷门方被系统性高估赔率
        correction = 0.05
        return prob * (1 + correction)

    return prob


# ============================================================
# 模块 3: Fractional-Kelly 投注决策 (Beuoy, 2026 + Grady, 2026)
# ============================================================

def kelly_fraction(
    prob: float,
    odds: float,
    divisor: int = 4,
    ev_threshold: float = 0.02
) -> Dict:
    """
    Fractional-Kelly 投注决策

    Args:
        prob: 模型概率
        odds: 十进制赔率
        divisor: Kelly除数 (4=quarter-Kelly)
        ev_threshold: 期望值阈值

    Returns:
        {"kelly_fraction": 投注比例, "ev": 期望值, "decision": "bet"/"skip"}
    """
    q = 1 - prob
    b = odds - 1  # 净赔率

    # Kelly公式
    f_star = (prob * b - q) / b if b > 0 else -1
    f = f_star / divisor

    # 期望值
    ev = prob * b - q

    # 决策
    if f <= 0 or ev < ev_threshold:
        decision = "skip"
    elif f > 0.25:
        f = 0.25  # 风控上限
        decision = "bet_capped"
    else:
        decision = "bet"

    return {
        "kelly_fraction": round(f, 4),
        "full_kelly": round(f_star, 4),
        "expected_value": round(ev, 4),
        "decision": decision
    }


# ============================================================
# 模块 4: 概率融合 (市场共识 + 模型推断)
# ============================================================

def fuse_probabilities(
    market_prob: float,
    model_prob: Optional[float],
    model_credibility: float = 1.0
) -> float:
    """
    贝叶斯加权平均融合

    Args:
        market_prob: OO-EPC市场共识概率
        model_prob: 模型推断概率 (None→纯市场)
        model_credibility: Kelly收益比 (1.0=基准)

    Returns:
        融合概率
    """
    if model_prob is None:
        return market_prob

    # 贝叶斯加权: 可信度越高, 模型权重越大
    w_model = model_credibility / (model_credibility + 1.0)
    w_market = 1.0 / (model_credibility + 1.0)

    fused = w_model * model_prob + w_market * market_prob
    return round(fused, 4)


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    # 模拟: KFUM奥斯陆 vs 罗森博格 的百家欧赔
    test_odds = [
        (1.85, 3.50, 4.20),  # 竞彩
        (1.90, 3.40, 4.00),  # Pinnacle
        (1.88, 3.45, 4.10),  # 澳门
    ] * 17  # 模拟51家

    result = oo_epc_convert(test_odds)
    print("=" * 50)
    print("OO-EPC 概率转换测试")
    print("=" * 50)
    print(f"市场共识: 主{result['home']:.3f} 平{result['draw']:.3f} 客{result['away']:.3f}")
    print(f"庄家抽水: {result['overround']:.3%}")

    # FL校正
    p_home_corrected = correct_fl_bias(result['home'])
    print(f"\nFL校正: {result['home']:.3f} → {p_home_corrected:.3f}")

    # Kelly决策
    k = kelly_fraction(p_home_corrected, 1.85)
    print(f"\nKelly决策:")
    print(f"  Full Kelly: {k['full_kelly']:.4f}")
    print(f"  Quarter Kelly: {k['kelly_fraction']:.4f}")
    print(f"  期望值: {k['expected_value']:.4f}")
    print(f"  决策: {k['decision']}")
