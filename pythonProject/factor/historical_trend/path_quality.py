import math
from functools import lru_cache
from typing import Dict, Any, Optional

import akshare as ak
import numpy as np
import pandas as pd


# =========================
# 工具函数
# =========================
def _clip(v, low=0, high=100):
    return max(low, min(high, float(v)))


def _safe_float(x, default=np.nan):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def _annualize_vol(daily_returns: pd.Series, trading_days=252) -> float:
    if len(daily_returns) < 2:
        return np.nan
    return float(daily_returns.std(ddof=0) * np.sqrt(trading_days))


def _max_drawdown(price: pd.Series) -> float:
    """
    返回最大回撤（负数）
    """
    if len(price) < 2:
        return np.nan
    cummax = price.cummax()
    dd = price / cummax - 1
    return float(dd.min())


def _path_smoothness(price: pd.Series) -> float:
    """
    路径平滑度：直线距离 / 实际路径距离，范围 (0, 1]
    越接近1，说明越平滑。
    """
    if len(price) < 3:
        return np.nan

    arr = price.values.astype(float)
    if np.any(~np.isfinite(arr)):
        return np.nan

    start = arr[0]
    end = arr[-1]
    if start <= 0:
        return np.nan

    # 用对数净值更稳
    logp = np.log(arr)
    direct = abs(logp[-1] - logp[0])
    path = np.sum(np.abs(np.diff(logp)))

    if path == 0:
        return 1.0
    return float(direct / path)


def _downside_vol(returns: pd.Series, mar=0.0, trading_days=252) -> float:
    """
    下行波动率（只统计低于 mar 的收益）
    """
    if len(returns) < 2:
        return np.nan
    downside = np.minimum(returns - mar, 0.0)
    return float(np.sqrt(np.mean(np.square(downside))) * np.sqrt(trading_days))


def _calc_return(price: pd.Series, window: int) -> float:
    if len(price) < window + 1:
        return np.nan
    return float(price.iloc[-1] / price.iloc[-window - 1] - 1.0)


def _score_return(ret_20, ret_60, ret_120):
    """
    收益分：近期、中期、半年兼顾。
    不追求暴涨，而是奖励“持续向上”。
    """
    vals = [ret_20, ret_60, ret_120]
    weights = [0.35, 0.40, 0.25]
    score = 0.0

    for r, w in zip(vals, weights):
        if pd.isna(r):
            continue

        # 分段映射，避免暴涨导致失真
        if r <= -0.15:
            s = 10
        elif r <= -0.08:
            s = 25
        elif r <= -0.03:
            s = 40
        elif r <= 0:
            s = 50
        elif r <= 0.03:
            s = 60
        elif r <= 0.08:
            s = 75
        elif r <= 0.15:
            s = 88
        else:
            s = 95

        score += s * w

    return _clip(score)


def _score_drawdown(mdd_120, mdd_250):
    """
    回撤分：越小越好
    """
    vals = [mdd_120, mdd_250]
    weights = [0.45, 0.55]
    score = 0.0

    for dd, w in zip(vals, weights):
        if pd.isna(dd):
            continue

        # dd 为负数，比如 -0.12 表示回撤12%
        abs_dd = abs(dd)
        if abs_dd <= 0.03:
            s = 95
        elif abs_dd <= 0.05:
            s = 88
        elif abs_dd <= 0.08:
            s = 78
        elif abs_dd <= 0.12:
            s = 65
        elif abs_dd <= 0.18:
            s = 50
        elif abs_dd <= 0.25:
            s = 35
        else:
            s = 15

        score += s * w

    return _clip(score)


def _score_vol(vol_60, vol_120):
    """
    年化波动分：越低越好
    对基金来说，过高波动通常意味着路径质量较差。
    """
    vals = [vol_60, vol_120]
    weights = [0.45, 0.55]
    score = 0.0

    for v, w in zip(vals, weights):
        if pd.isna(v):
            continue

        if v <= 0.08:
            s = 95
        elif v <= 0.12:
            s = 88
        elif v <= 0.18:
            s = 75
        elif v <= 0.24:
            s = 62
        elif v <= 0.32:
            s = 45
        else:
            s = 20

        score += s * w

    return _clip(score)


def _score_smooth(smooth_60, smooth_120):
    """
    路径平滑分：越平滑越好
    """
    vals = [smooth_60, smooth_120]
    weights = [0.45, 0.55]
    score = 0.0

    for sm, w in zip(vals, weights):
        if pd.isna(sm):
            continue

        if sm >= 0.85:
            s = 95
        elif sm >= 0.72:
            s = 85
        elif sm >= 0.58:
            s = 72
        elif sm >= 0.45:
            s = 58
        elif sm >= 0.32:
            s = 42
        else:
            s = 20

        score += s * w

    return _clip(score)


def _score_winrate(win_20, win_60):
    """
    胜率分：上涨日占比越高越好，但不极端奖励
    """
    vals = [win_20, win_60]
    weights = [0.40, 0.60]
    score = 0.0

    for wr, w in zip(vals, weights):
        if pd.isna(wr):
            continue

        if wr >= 0.70:
            s = 95
        elif wr >= 0.62:
            s = 85
        elif wr >= 0.56:
            s = 75
        elif wr >= 0.50:
            s = 62
        elif wr >= 0.44:
            s = 48
        else:
            s = 28

        score += s * w

    return _clip(score)


def _score_trend(ma20, ma60, ma120, last_price):
    """
    趋势分：均线多头排列 + 当前价格在中长期均线上方
    """
    if any(pd.isna(x) for x in [ma20, ma60, ma120, last_price]):
        return np.nan

    score = 0
    if last_price > ma20:
        score += 20
    if last_price > ma60:
        score += 25
    if last_price > ma120:
        score += 25
    if ma20 > ma60:
        score += 15
    if ma60 > ma120:
        score += 15

    return _clip(score)


def _score_stability(ret_20, ret_60, ret_120, vol_20, vol_60, vol_120):
    """
    稳定改善分：
    - 最近20日收益不能明显弱于60/120日
    - 最近20日波动不要显著恶化
    """
    score = 50.0

    # 收益改善
    if not pd.isna(ret_20) and not pd.isna(ret_60):
        if ret_20 > ret_60 / 3:
            score += 10
        if ret_20 > 0:
            score += 8

    if not pd.isna(ret_20) and not pd.isna(ret_120):
        if ret_20 > ret_120 / 6:
            score += 8

    # 波动改善
    if not pd.isna(vol_20) and not pd.isna(vol_60):
        if vol_20 <= vol_60 * 1.05:
            score += 12
        elif vol_20 > vol_60 * 1.30:
            score -= 12

    if not pd.isna(vol_20) and not pd.isna(vol_120):
        if vol_20 <= vol_120 * 1.05:
            score += 12
        elif vol_20 > vol_120 * 1.35:
            score -= 12

    return _clip(score)


def _score_downside(down_60, down_120):
    """
    下行风险分：越低越好
    """
    vals = [down_60, down_120]
    weights = [0.45, 0.55]
    score = 0.0

    for d, w in zip(vals, weights):
        if pd.isna(d):
            continue

        if d <= 0.05:
            s = 95
        elif d <= 0.08:
            s = 86
        elif d <= 0.12:
            s = 74
        elif d <= 0.18:
            s = 58
        elif d <= 0.25:
            s = 40
        else:
            s = 20

        score += s * w

    return _clip(score)


def _fund_type_map(fund_code: str) -> Optional[str]:
    """
    读取基金大类
    """
    try:
        df = ak.fund_name_em()
        row = df[df["基金代码"].astype(str) == str(fund_code)]
        if row.empty:
            return None
        return str(row.iloc[0]["基金类型"])
    except Exception:
        return None


# =========================
# 数据获取
# =========================
@lru_cache(maxsize=256)
def get_fund_history(fund_code: str, start_date: str = "20200101", end_date: str = "21000101") -> pd.DataFrame:
    """
    尽量兼容 ETF / 场外开放式基金

    返回统一列：
    date, price
    """
    fund_code = str(fund_code)

    # 先尝试 ETF 历史行情
    try:
        etf_df = ak.fund_etf_hist_em(
            symbol=fund_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        if etf_df is not None and not etf_df.empty:
            df = etf_df.copy()
            # 兼容 AKShare 常见字段
            date_col = "日期"
            price_col = "收盘"

            if date_col in df.columns and price_col in df.columns:
                df = df[[date_col, price_col]].rename(columns={date_col: "date", price_col: "price"})
                df["date"] = pd.to_datetime(df["date"])
                df["price"] = pd.to_numeric(df["price"], errors="coerce")
                df = df.dropna().sort_values("date").reset_index(drop=True)
                if len(df) >= 60:
                    return df
    except Exception:
        pass

    # 再尝试开放式基金净值历史
    # 注：不同 AKShare 版本字段略有差异，这里尽量做兼容
    try:
        open_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
        if open_df is not None and not open_df.empty:
            df = open_df.copy()

            # 常见字段兼容
            possible_date_cols = ["净值日期", "日期", "x"]
            possible_price_cols = ["累计净值", "y", "单位净值"]

            date_col = next((c for c in possible_date_cols if c in df.columns), None)
            price_col = next((c for c in possible_price_cols if c in df.columns), None)

            if date_col and price_col:
                df = df[[date_col, price_col]].rename(columns={date_col: "date", price_col: "price"})
                df["date"] = pd.to_datetime(df["date"])
                df["price"] = pd.to_numeric(df["price"], errors="coerce")
                df = df.dropna().sort_values("date").reset_index(drop=True)

                # 截取时间
                start_ts = pd.to_datetime(start_date)
                end_ts = pd.to_datetime(end_date)
                df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].reset_index(drop=True)

                if len(df) >= 60:
                    return df
    except Exception:
        pass

    raise ValueError(f"无法获取基金 {fund_code} 的历史数据，请检查 code 是否正确，或升级 akshare 后重试。")


# =========================
# 主函数：路径质量因子
# =========================
def evaluate_path_quality(
    fund_code: str,
    start_date: str = "20200101",
    end_date: str = "21000101"
) -> Dict[str, Any]:
    """
    输入基金 code，输出路径质量因子结果
    """
    df = get_fund_history(fund_code, start_date=start_date, end_date=end_date).copy()

    if len(df) < 130:
        raise ValueError(f"基金 {fund_code} 历史数据不足，至少建议 130 个交易日以上，当前仅 {len(df)} 条。")

    df["ret"] = df["price"].pct_change()
    df = df.dropna().reset_index(drop=True)

    price = df["price"]
    ret = df["ret"]

    # 最近窗口
    p20 = price.iloc[-21:]
    p60 = price.iloc[-61:]
    p120 = price.iloc[-121:]
    p250 = price.iloc[-251:] if len(price) >= 251 else price.copy()

    r20 = ret.iloc[-20:]
    r60 = ret.iloc[-60:]
    r120 = ret.iloc[-120:]
    r250 = ret.iloc[-250:] if len(ret) >= 250 else ret.copy()

    # 收益
    ret_20 = _calc_return(price, 20)
    ret_60 = _calc_return(price, 60)
    ret_120 = _calc_return(price, 120)
    ret_250 = _calc_return(price, 250) if len(price) >= 251 else np.nan

    # 波动
    vol_20 = _annualize_vol(r20)
    vol_60 = _annualize_vol(r60)
    vol_120 = _annualize_vol(r120)
    vol_250 = _annualize_vol(r250) if len(r250) >= 2 else np.nan

    # 下行波动
    down_60 = _downside_vol(r60)
    down_120 = _downside_vol(r120)

    # 最大回撤
    mdd_60 = _max_drawdown(p60)
    mdd_120 = _max_drawdown(p120)
    mdd_250 = _max_drawdown(p250)

    # 平滑度
    smooth_60 = _path_smoothness(p60)
    smooth_120 = _path_smoothness(p120)

    # 胜率
    win_20 = float((r20 > 0).mean()) if len(r20) else np.nan
    win_60 = float((r60 > 0).mean()) if len(r60) else np.nan
    win_120 = float((r120 > 0).mean()) if len(r120) else np.nan

    # 均线趋势
    ma20 = float(price.rolling(20).mean().iloc[-1]) if len(price) >= 20 else np.nan
    ma60 = float(price.rolling(60).mean().iloc[-1]) if len(price) >= 60 else np.nan
    ma120 = float(price.rolling(120).mean().iloc[-1]) if len(price) >= 120 else np.nan
    last_price = float(price.iloc[-1])

    # 各子分数
    return_score = _score_return(ret_20, ret_60, ret_120)
    drawdown_score = _score_drawdown(mdd_120, mdd_250)
    vol_score = _score_vol(vol_60, vol_120)
    smooth_score = _score_smooth(smooth_60, smooth_120)
    winrate_score = _score_winrate(win_20, win_60)
    trend_score = _score_trend(ma20, ma60, ma120, last_price)
    stability_score = _score_stability(ret_20, ret_60, ret_120, vol_20, vol_60, vol_120)
    downside_score = _score_downside(down_60, down_120)

    # 最终总分：更偏重“回撤 + 平滑 + 趋势 + 下行风险”
    final_score = (
        return_score * 0.14 +
        drawdown_score * 0.20 +
        vol_score * 0.12 +
        smooth_score * 0.14 +
        winrate_score * 0.08 +
        trend_score * 0.14 +
        stability_score * 0.08 +
        downside_score * 0.10
    )

    final_score = _clip(round(final_score, 2))

    # 给出文本判断
    if final_score >= 85:
        suggestion = "路径质量优秀，可重点关注，适合偏积极买入/分批买入"
    elif final_score >= 75:
        suggestion = "路径质量较好，可考虑分批买入"
    elif final_score >= 65:
        suggestion = "路径质量中等，建议观察后再决定"
    elif final_score >= 50:
        suggestion = "路径质量偏弱，暂不建议重仓买入"
    else:
        suggestion = "路径质量较差，建议谨慎或暂时回避"

    return {
        "code": fund_code,
        "fund_type": _fund_type_map(fund_code),
        "score": final_score,
        "suggestion": suggestion,
        "detail": {
            # 收益
            "return_20d_pct": round(ret_20 * 100, 2) if not pd.isna(ret_20) else None,
            "return_60d_pct": round(ret_60 * 100, 2) if not pd.isna(ret_60) else None,
            "return_120d_pct": round(ret_120 * 100, 2) if not pd.isna(ret_120) else None,
            "return_250d_pct": round(ret_250 * 100, 2) if not pd.isna(ret_250) else None,

            # 风险
            "max_drawdown_60d_pct": round(mdd_60 * 100, 2) if not pd.isna(mdd_60) else None,
            "max_drawdown_120d_pct": round(mdd_120 * 100, 2) if not pd.isna(mdd_120) else None,
            "max_drawdown_250d_pct": round(mdd_250 * 100, 2) if not pd.isna(mdd_250) else None,

            "annual_vol_20d_pct": round(vol_20 * 100, 2) if not pd.isna(vol_20) else None,
            "annual_vol_60d_pct": round(vol_60 * 100, 2) if not pd.isna(vol_60) else None,
            "annual_vol_120d_pct": round(vol_120 * 100, 2) if not pd.isna(vol_120) else None,
            "annual_vol_250d_pct": round(vol_250 * 100, 2) if not pd.isna(vol_250) else None,

            "downside_vol_60d_pct": round(down_60 * 100, 2) if not pd.isna(down_60) else None,
            "downside_vol_120d_pct": round(down_120 * 100, 2) if not pd.isna(down_120) else None,

            # 质量
            "path_smooth_60d": round(smooth_60, 4) if not pd.isna(smooth_60) else None,
            "path_smooth_120d": round(smooth_120, 4) if not pd.isna(smooth_120) else None,
            "win_rate_20d_pct": round(win_20 * 100, 2) if not pd.isna(win_20) else None,
            "win_rate_60d_pct": round(win_60 * 100, 2) if not pd.isna(win_60) else None,
            "win_rate_120d_pct": round(win_120 * 100, 2) if not pd.isna(win_120) else None,

            # 趋势
            "latest_price": round(last_price, 4),
            "ma20": round(ma20, 4) if not pd.isna(ma20) else None,
            "ma60": round(ma60, 4) if not pd.isna(ma60) else None,
            "ma120": round(ma120, 4) if not pd.isna(ma120) else None,

            # 子分数
            "return_score": round(return_score, 2),
            "drawdown_score": round(drawdown_score, 2),
            "vol_score": round(vol_score, 2),
            "smooth_score": round(smooth_score, 2),
            "winrate_score": round(winrate_score, 2),
            "trend_score": round(trend_score, 2) if not pd.isna(trend_score) else None,
            "stability_score": round(stability_score, 2),
            "downside_score": round(downside_score, 2),
        }
    }


# =========================
# 示例
# =========================
if __name__ == "__main__":
    code = "016185"   # 示例：广发电力公用事业ETF联接A
    result = evaluate_path_quality(code)
    from pprint import pprint
    pprint(result)