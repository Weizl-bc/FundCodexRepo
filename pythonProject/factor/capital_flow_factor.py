import re
from typing import Optional, Dict, Any

import akshare as ak
import pandas as pd

from utils.fund_util import get_fund_type_label


def _safe_float(value, default=0.0) -> float:
    """安全转 float"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "")
        if text in ("", "nan", "None", "--"):
            return default
        return float(text)
    except Exception:
        return default


def _parse_scale_to_yi(text: str) -> float:
    """
    把类似 '27.30亿'、'8500万'、'123456份' 转成“亿”单位
    """
    if text is None:
        return 0.0

    s = str(text).strip().replace(",", "")
    if not s or s in ("--", "nan", "None"):
        return 0.0

    match = re.search(r"([-+]?\d*\.?\d+)", s)
    if not match:
        return 0.0

    num = float(match.group(1))

    if "亿" in s:
        return num
    if "万" in s:
        return num / 10000
    if "份" in s:
        # 1 亿份 = 100000000 份
        return num / 100000000
    return num


def _clip_score(score: float) -> int:
    """裁剪到 0~100，并转 int"""
    return max(0, min(100, int(round(score))))


def _get_fund_type(code: str) -> str:
    """
    统一通过 fund_util 判断基金类型。

    返回值只保留业务层需要的两类：
    - ETF: 场内纯 ETF
    - OPEN: 普通开放式基金或 ETF 联接基金
    """
    return get_fund_type_label(code)


def _score_by_thresholds(value: float, thresholds: list[tuple[float, int]]) -> int:
    """
    thresholds: [(阈值下限, 分数)]，按从高到低传入
    """
    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return thresholds[-1][1]


def etf_capital_flow_score(code: str,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    ETF 资金流评分（0~100）
    逻辑：
    1. 用近 20 个交易日历史行情
    2. 结合 成交额放大倍数 + 收盘涨跌方向 + OBV 趋势
    3. 输出一个短线资金流评分

    :param code: ETF 代码，如 513100
    :param start_date: 可选，格式 YYYYMMDD
    :param end_date: 可选，格式 YYYYMMDD
    :return: dict
    """
    code = str(code).zfill(6)

    if end_date is None:
        end_date = pd.Timestamp.today().strftime("%Y%m%d")
    if start_date is None:
        # 多拉一点，确保计算均值和趋势足够
        start_date = (pd.Timestamp.today() - pd.Timedelta(days=90)).strftime("%Y%m%d")

    df = ak.fund_etf_hist_em(
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=""
    )

    if df.empty:
        raise ValueError(f"ETF {code} 未获取到历史行情数据")

    df = df.copy()
    df["收盘"] = pd.to_numeric(df["收盘"], errors="coerce")
    df["成交量"] = pd.to_numeric(df["成交量"], errors="coerce")
    df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
    df = df.dropna(subset=["收盘", "成交量", "成交额"]).reset_index(drop=True)

    if len(df) < 10:
        return {
            "code": code,
            "fund_type": "ETF",
            "score": 50,
            "reason": "历史数据不足，返回中性分"
        }

    # ---- 1) 成交额放大倍数 ----
    df["成交额MA5"] = df["成交额"].rolling(5).mean()
    turnover_ratio = df.iloc[-1]["成交额"] / max(df.iloc[-1]["成交额MA5"], 1e-8)

    # ---- 2) 价格方向（今天相对昨天）----
    price_change_pct = (df.iloc[-1]["收盘"] / df.iloc[-2]["收盘"] - 1) * 100

    # ---- 3) OBV 趋势（简化版）----
    # 上涨日 +成交量，下跌日 -成交量
    price_diff = df["收盘"].diff().fillna(0)
    df["OBV"] = 0.0
    df.loc[price_diff > 0, "OBV"] = df["成交量"]
    df.loc[price_diff < 0, "OBV"] = -df["成交量"]
    df["OBV"] = df["OBV"].cumsum()
    obv_slope = df["OBV"].iloc[-1] - df["OBV"].iloc[-6] if len(df) >= 6 else 0.0

    # ---- 各子项打分 ----
    turnover_score = _score_by_thresholds(turnover_ratio, [
        (2.0, 95),
        (1.5, 85),
        (1.2, 75),
        (1.0, 65),
        (0.8, 55),
        (0.0, 40),
    ])

    if price_change_pct >= 2.0:
        price_score = 90
    elif price_change_pct >= 1.0:
        price_score = 80
    elif price_change_pct >= 0.0:
        price_score = 70
    elif price_change_pct >= -1.0:
        price_score = 45
    else:
        price_score = 25

    if obv_slope > 0:
        obv_score = 80
    elif obv_slope == 0:
        obv_score = 60
    else:
        obv_score = 35

    # ---- 综合得分 ----
    # 成交额放量最重要，其次价格方向，再次OBV趋势
    score = turnover_score * 0.45 + price_score * 0.35 + obv_score * 0.20

    return {
        "code": code,
        "fund_type": "ETF",
        "score": _clip_score(score),
        "detail": {
            "turnover_ratio": round(turnover_ratio, 4),
            "price_change_pct": round(price_change_pct, 4),
            "obv_slope_5d": round(float(obv_slope), 4),
            "turnover_score": turnover_score,
            "price_score": price_score,
            "obv_score": obv_score,
        },
        "reason": "ETF 资金流评分基于成交额放量、价格方向、OBV 趋势综合计算"
    }


def open_fund_capital_flow_score(code: str) -> Dict[str, Any]:
    """
    普通开放式基金“资金流代理评分”（0~100）
    注意：
    这不是严格的日净申购额，因为开放式基金没有像 ETF 那样的逐日成交量/成交额。
    这里用三个代理变量：
    1) 最新规模（fund_individual_basic_info_xq）
    2) 近 20 日单位净值动量（fund_open_fund_info_em）
    3) 申购/赎回状态（fund_purchase_em）

    :param code: 普通基金代码，如 017641
    :return: dict
    """
    code = str(code).zfill(6)

    # 1) 基金详情：读取最新规模
    basic_df = ak.fund_individual_basic_info_xq(symbol=code)
    scale_text = ""
    if not basic_df.empty and {"item", "value"}.issubset(basic_df.columns):
        scale_row = basic_df.loc[basic_df["item"] == "最新规模"]
        if not scale_row.empty:
            scale_text = str(scale_row.iloc[0]["value"])

    latest_scale_yi = _parse_scale_to_yi(scale_text)

    # 2) 历史净值：读取单位净值走势
    nav_df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
    if nav_df.empty:
        raise ValueError(f"普通基金 {code} 未获取到单位净值走势数据")

    nav_df = nav_df.copy()
    nav_df["单位净值"] = pd.to_numeric(nav_df["单位净值"], errors="coerce")
    nav_df = nav_df.dropna(subset=["单位净值"]).reset_index(drop=True)

    if len(nav_df) < 21:
        momentum_20 = 0.0
        momentum_5 = 0.0
    else:
        momentum_20 = (nav_df.iloc[-1]["单位净值"] / nav_df.iloc[-21]["单位净值"] - 1) * 100
        momentum_5 = (nav_df.iloc[-1]["单位净值"] / nav_df.iloc[-6]["单位净值"] - 1) * 100

    # 3) 申购/赎回状态：作为热度补充
    purchase_df = ak.fund_purchase_em()
    purchase_df["基金代码"] = purchase_df["基金代码"].astype(str).str.zfill(6)
    purchase_row = purchase_df.loc[purchase_df["基金代码"] == code]

    purchase_status = ""
    redeem_status = ""
    if not purchase_row.empty:
        purchase_status = str(purchase_row.iloc[0]["申购状态"])
        redeem_status = str(purchase_row.iloc[0]["赎回状态"])

    # ---- 子项打分 ----
    # A. 最新规模分：规模越大，说明历史资金承载越强；但不等于“最近日流入”
    scale_score = _score_by_thresholds(latest_scale_yi, [
        (100.0, 90),
        (50.0, 80),
        (20.0, 70),
        (10.0, 60),
        (5.0, 50),
        (0.0, 40),
    ])

    # B. 20日净值动量：作为“最近热度/资金偏好”的代理
    if momentum_20 >= 10:
        m20_score = 90
    elif momentum_20 >= 5:
        m20_score = 80
    elif momentum_20 >= 2:
        m20_score = 70
    elif momentum_20 >= 0:
        m20_score = 60
    elif momentum_20 >= -3:
        m20_score = 45
    else:
        m20_score = 30

    # C. 5日短动量：短线热度补充
    if momentum_5 >= 3:
        m5_score = 85
    elif momentum_5 >= 1:
        m5_score = 75
    elif momentum_5 >= 0:
        m5_score = 65
    elif momentum_5 >= -1:
        m5_score = 50
    else:
        m5_score = 35

    # D. 申购/赎回状态：开放申购一般更利于资金进入
    status_score = 60
    if "开放申购" in purchase_status:
        status_score += 10
    if "开放赎回" in redeem_status:
        status_score += 5
    if "暂停申购" in purchase_status:
        status_score -= 10

    status_score = _clip_score(status_score)

    # ---- 综合得分 ----
    # 这是“资金热度代理评分”，不是净流入额评分
    score = scale_score * 0.35 + m20_score * 0.35 + m5_score * 0.20 + status_score * 0.10

    return {
        "code": code,
        "fund_type": "OPEN",
        "score": _clip_score(score),
        "detail": {
            "latest_scale_text": scale_text,
            "latest_scale_yi": round(latest_scale_yi, 4),
            "momentum_20_pct": round(momentum_20, 4),
            "momentum_5_pct": round(momentum_5, 4),
            "purchase_status": purchase_status,
            "redeem_status": redeem_status,
            "scale_score": scale_score,
            "m20_score": m20_score,
            "m5_score": m5_score,
            "status_score": status_score,
        },
        "reason": "普通基金缺少逐日成交量/成交额，此处返回的是资金热度代理评分，不是严格净申购额"
    }


def fund_capital_flow_score(code: str) -> Dict[str, Any]:
    """
    自动识别基金类型并返回资金流评分
    """
    fund_type = _get_fund_type(code)

    if fund_type == "ETF":
        return etf_capital_flow_score(code)
    return open_fund_capital_flow_score(code)


if __name__ == "__main__":
    # ETF 示例
    try:
        result_etf = fund_capital_flow_score("513100")
        print("ETF 结果：")
        print(result_etf)
    except Exception as e:
        print("ETF 计算失败：", e)

    # 普通基金示例
    try:
        result_open = fund_capital_flow_score("017641")
        print("普通基金结果：")
        print(result_open)
    except Exception as e:
        print("普通基金计算失败：", e)
