import re
from functools import lru_cache
from typing import List, Dict, Optional

import akshare as ak
import pandas as pd

from outer.qwen.qwen import call_qwen
from utils.fund_util import get_fund_base_info, get_fund_name_df


def build_prompt(fund_code: str) -> str:
    return f"""
你是一个基金“同类基金代码检索器”。

任务：
根据我提供的基金代码，找出可用于“相对收益比较”的同类基金代码。

输入基金代码：
{fund_code}

请你完成：
1. 识别该基金的：
   - 基金类型（股票型/混合型/债券型/QDII/货币等）
   - 是否指数基金
   - 是否ETF / ETF联接 / LOF
   - 投资行业/主题（如电力、公用事业、医药、半导体、消费等）
   - 跟踪指数或投资方向

同类基金筛选规则：
1. 基金大类必须一致
2. 行业/主题优先匹配
3. 窄行业基金不能混入宽基
4. ETF联接基金可匹配同主题ETF或指数基金
5. 不要输出目标基金本身
6. 不确定的不要输出

输出要求：
只输出基金代码，一行一个，不要任何解释。

基金代码：{fund_code}
"""


def _normalize_code(code: str) -> str:
    return str(code).strip().zfill(6)


def _extract_fund_codes(text: str) -> List[str]:
    """
    从大模型输出中提取 6 位基金代码
    """
    if not text:
        return []

    codes = re.findall(r"\b\d{6}\b", str(text))
    codes = [_normalize_code(c) for c in codes]

    # 去重并保持顺序
    seen = set()
    result = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def fetch_relative_fund_codes_by_qwen(fund_code: str, limit: int = 20) -> List[str]:
    """
    调用 Qwen 获取同类基金代码
    """
    fund_code = _normalize_code(fund_code)
    prompt = build_prompt(fund_code)
    result = call_qwen(prompt)

    if result is None:
        return []

    codes = _extract_fund_codes(str(result))
    codes = [c for c in codes if c != fund_code]

    if limit > 0:
        codes = codes[:limit]
    return codes


def fetch_relative_fund(fund_code: str, limit: int = 20) -> pd.DataFrame:
    """
    调用Qwen模型获取同类基金，并返回带名称/类型的 DataFrame
    """
    fund_code = _normalize_code(fund_code)
    codes = fetch_relative_fund_codes_by_qwen(fund_code, limit=limit)

    if not codes:
        return pd.DataFrame(columns=["基金代码", "基金简称", "基金类型"])

    all_funds = get_fund_name_df()
    result_df = all_funds[all_funds["基金代码"].isin(codes)].copy()

    # 防止 Qwen 给出的代码不在 fund_name_em 中
    missing_codes = [c for c in codes if c not in set(result_df["基金代码"].tolist())]
    if missing_codes:
        missing_df = pd.DataFrame({
            "基金代码": missing_codes,
            "基金简称": [None] * len(missing_codes),
            "基金类型": [None] * len(missing_codes),
        })
        result_df = pd.concat([result_df, missing_df], ignore_index=True)

    # 按 Qwen 返回顺序排序
    code_order = {code: i for i, code in enumerate(codes)}
    result_df["__order"] = result_df["基金代码"].map(code_order)
    result_df = result_df.sort_values("__order").drop(columns="__order").reset_index(drop=True)

    return result_df


@lru_cache(maxsize=512)
def get_fund_nav_history(fund_code: str) -> pd.DataFrame:
    """
    获取单只基金历史净值
    优先使用开放式基金净值接口
    返回:
    date, nav
    """
    fund_code = _normalize_code(fund_code)

    # 尝试开放式基金净值
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df is not None and not df.empty:
            df = df.copy()
            # 常见列: 净值日期 / 单位净值
            date_col = None
            nav_col = None

            for col in df.columns:
                if str(col) in ["净值日期", "x", "日期"]:
                    date_col = col
                if str(col) in ["单位净值", "y", "净值"]:
                    nav_col = col

            if date_col is None:
                for col in df.columns:
                    if "日期" in str(col):
                        date_col = col
                        break

            if nav_col is None:
                for col in df.columns:
                    if "净值" in str(col):
                        nav_col = col
                        break

            if date_col is not None and nav_col is not None:
                out = df[[date_col, nav_col]].copy()
                out.columns = ["date", "nav"]
                out["date"] = pd.to_datetime(out["date"])
                out["nav"] = pd.to_numeric(out["nav"], errors="coerce")
                out = out.dropna(subset=["date", "nav"]).sort_values("date").reset_index(drop=True)
                return out
    except Exception:
        pass

    # 如果开放式接口失败，再尝试 ETF 行情接口
    try:
        df = ak.fund_etf_hist_em(symbol=fund_code, period="daily", adjust="")
        if df is not None and not df.empty:
            df = df.copy()

            date_col = None
            price_col = None

            for col in df.columns:
                if str(col) in ["日期"]:
                    date_col = col
                if str(col) in ["收盘", "单位净值", "净值"]:
                    price_col = col

            if date_col is not None and price_col is not None:
                out = df[[date_col, price_col]].copy()
                out.columns = ["date", "nav"]
                out["date"] = pd.to_datetime(out["date"])
                out["nav"] = pd.to_numeric(out["nav"], errors="coerce")
                out = out.dropna(subset=["date", "nav"]).sort_values("date").reset_index(drop=True)
                return out
    except Exception:
        pass

    return pd.DataFrame(columns=["date", "nav"])


def build_nav_matrix(target_code: str, peer_codes: List[str], min_history: int = 80) -> pd.DataFrame:
    """
    构建净值矩阵:
    index = date
    columns = fund_code
    values = nav
    """
    target_code = _normalize_code(target_code)
    all_codes = [target_code] + [_normalize_code(c) for c in peer_codes if _normalize_code(c) != target_code]

    series_list = []
    valid_codes = []

    for code in all_codes:
        hist = get_fund_nav_history(code)
        if hist.empty:
            continue
        if len(hist) < min_history:
            continue

        s = hist.set_index("date")["nav"].rename(code)
        series_list.append(s)
        valid_codes.append(code)

    if not series_list:
        return pd.DataFrame()

    nav_df = pd.concat(series_list, axis=1).sort_index()

    # 对齐日期，允许前值填充
    nav_df = nav_df.ffill()

    # 删除缺失太多的列
    valid_cols = [c for c in nav_df.columns if nav_df[c].notna().sum() >= min_history]
    nav_df = nav_df[valid_cols]

    return nav_df


def _clip_score(score: float, min_score: float = 0, max_score: float = 100) -> float:
    return float(max(min_score, min(max_score, score)))


def _safe_rank_pct(series: pd.Series, target_code: str) -> float:
    """
    获取目标基金在一个截面上的分位排名，范围 [0, 1]
    """
    series = pd.to_numeric(series, errors="coerce").dropna()
    if target_code not in series.index or len(series) < 2:
        return 0.5
    ranked = series.rank(pct=True)
    return float(ranked[target_code])


def _safe_value(series: pd.Series, target_code: str, default: float = 0.0) -> float:
    if target_code not in series.index:
        return default
    val = pd.to_numeric(pd.Series([series[target_code]]), errors="coerce").iloc[0]
    if pd.isna(val):
        return default
    return float(val)


def calculate_relative_return_score_from_nav(
    nav_df: pd.DataFrame,
    target_code: str,
) -> Dict:
    """
    根据净值矩阵计算目标基金相对收益评分

    核心逻辑：
    1. 先算每日收益率
    2. 计算相对收益 = 该基金收益 - 同类平均收益
    3. 分别计算 5 / 20 / 60 日滚动平均相对收益
    4. 用横截面排名转成 0~100 分
    5. 叠加 IR（稳定性）评分
    """
    target_code = _normalize_code(target_code)

    if nav_df.empty or target_code not in nav_df.columns:
        return {
            "code": target_code,
            "score": 50.0,
            "signal": "neutral",
            "detail": {},
            "reason": "净值数据不足，无法计算相对收益评分",
        }

    # 收益率矩阵
    returns = nav_df.pct_change()

    # 至少保留一定样本
    if returns.dropna(how="all").shape[0] < 30:
        return {
            "code": target_code,
            "score": 50.0,
            "signal": "neutral",
            "detail": {},
            "reason": "历史收益数据不足，无法计算相对收益评分",
        }

    # 横截面同类均值收益
    peer_mean = returns.mean(axis=1)

    # 相对收益矩阵
    rel = returns.sub(peer_mean, axis=0)

    # 多周期相对收益
    rel_5 = rel.rolling(5).mean()
    rel_20 = rel.rolling(20).mean()
    rel_60 = rel.rolling(60).mean()

    # 稳定性：信息比率 IR = mean / std
    ir_20 = rel.rolling(20).mean() / rel.rolling(20).std()

    # 最新截面
    latest_rel5 = rel_5.iloc[-1].dropna()
    latest_rel20 = rel_20.iloc[-1].dropna()
    latest_rel60 = rel_60.iloc[-1].dropna()
    latest_ir20 = ir_20.iloc[-1].replace([float("inf"), float("-inf")], pd.NA).dropna()

    # 目标值
    target_rel5 = _safe_value(latest_rel5, target_code, 0.0)
    target_rel20 = _safe_value(latest_rel20, target_code, 0.0)
    target_rel60 = _safe_value(latest_rel60, target_code, 0.0)
    target_ir20 = _safe_value(latest_ir20, target_code, 0.0)

    # 横截面分位排名
    rank5 = _safe_rank_pct(latest_rel5, target_code)
    rank20 = _safe_rank_pct(latest_rel20, target_code)
    rank60 = _safe_rank_pct(latest_rel60, target_code)
    ir_rank = _safe_rank_pct(latest_ir20, target_code)

    # 综合评分
    score = (
        0.30 * rank5 +
        0.40 * rank20 +
        0.20 * rank60 +
        0.10 * ir_rank
    ) * 100

    score = round(_clip_score(score), 2)

    # 简单信号
    if score >= 80:
        signal = "strong_bullish"
    elif score >= 60:
        signal = "bullish"
    elif score >= 40:
        signal = "neutral"
    elif score >= 20:
        signal = "bearish"
    else:
        signal = "strong_bearish"

    return {
        "code": target_code,
        "score": score,
        "signal": signal,
        "detail": {
            "peer_count": int(len(nav_df.columns) - 1),
            "sample_days": int(nav_df.shape[0]),
            "rel_5": round(target_rel5, 6),
            "rel_20": round(target_rel20, 6),
            "rel_60": round(target_rel60, 6),
            "ir_20": round(target_ir20, 6),
            "rank5_pct": round(rank5, 4),
            "rank20_pct": round(rank20, 4),
            "rank60_pct": round(rank60, 4),
            "ir_rank_pct": round(ir_rank, 4),
        },
        "reason": "基于同类基金横截面相对收益、多周期动量和稳定性(IR)生成评分",
    }


def relative_return_score(
    fund_code: str,
    peer_limit: int = 20,
    min_peer_count: int = 3,
    min_history: int = 80,
) -> Dict:
    """
    对外主函数：
    1. 用Qwen找同类基金
    2. 构建净值矩阵
    3. 计算相对收益评分
    """
    fund_code = _normalize_code(fund_code)

    base_info = get_fund_base_info(fund_code)
    peer_df = fetch_relative_fund(fund_code, limit=peer_limit)

    peer_codes = peer_df["基金代码"].dropna().astype(str).str.zfill(6).tolist()
    peer_codes = [c for c in peer_codes if c != fund_code]

    if len(peer_codes) < min_peer_count:
        return {
            "code": fund_code,
            "fund_name": base_info.get("fund_name"),
            "fund_type": base_info.get("fund_type"),
            "score": 50.0,
            "signal": "neutral",
            "detail": {
                "peer_count": len(peer_codes),
                "peer_codes": peer_codes,
            },
            "reason": "同类基金数量不足，无法稳定计算相对收益评分",
        }

    nav_df = build_nav_matrix(
        target_code=fund_code,
        peer_codes=peer_codes,
        min_history=min_history,
    )

    if nav_df.empty or fund_code not in nav_df.columns:
        return {
            "code": fund_code,
            "fund_name": base_info.get("fund_name"),
            "fund_type": base_info.get("fund_type"),
            "score": 50.0,
            "signal": "neutral",
            "detail": {
                "peer_count": len(peer_codes),
                "peer_codes": peer_codes,
            },
            "reason": "目标基金或同类基金历史净值不足，无法计算评分",
        }

    # 如果最终有效基金太少，也不给强判断
    if nav_df.shape[1] - 1 < min_peer_count:
        return {
            "code": fund_code,
            "fund_name": base_info.get("fund_name"),
            "fund_type": base_info.get("fund_type"),
            "score": 50.0,
            "signal": "neutral",
            "detail": {
                "peer_count": int(nav_df.shape[1] - 1),
                "peer_codes": list(nav_df.columns),
            },
            "reason": "有效同类基金数量不足，评分稳定性不够",
        }

    score_result = calculate_relative_return_score_from_nav(nav_df, fund_code)
    score_result["fund_name"] = base_info.get("fund_name")
    score_result["fund_type"] = base_info.get("fund_type")
    score_result["detail"]["peer_codes"] = [c for c in nav_df.columns.tolist() if c != fund_code]

    return score_result

def calculate_relative_return_score(
    fund_code: str,
    peer_limit: int = 20
):
    return relative_return_score(
        fund_code=fund_code,
        peer_limit=peer_limit,
        min_peer_count=3,
        min_history=80,
    )

if __name__ == "__main__":
    code = "016185"
    print(calculate_relative_return_score(code)["score"])
    # 1. 看Qwen找出的同类基金
    # same_df = fetch_relative_fund(code, limit=15)
    # print("=== 同类基金 ===")
    # print(same_df)
    #
    # # 2. 计算相对收益评分
    # result = relative_return_score(
    #     fund_code=code,
    #     peer_limit=15,
    #     min_peer_count=3,
    #     min_history=80,
    # )
    #
    # print("\n=== 相对收益评分 ===")
    # print(result)
