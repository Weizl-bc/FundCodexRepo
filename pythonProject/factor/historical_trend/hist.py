import akshare as ak
import pandas as pd
import numpy as np

from utils.date_util import get_today_str


def _clip_score(score: float, min_score: float = 0, max_score: float = 100) -> float:
    """
    限制分数范围
    """
    return round(max(min_score, min(max_score, score)), 2)


def get_fund_hist_df(code: str, start_date: str = "20220101", end_date: str = "20260318") -> pd.DataFrame:
    """
    获取基金历史净值数据
    返回字段统一为：日期、收盘
    """
    df = ak.fund_open_fund_info_em(
        symbol=code,
        indicator="单位净值走势"
    )

    if df is None or df.empty:
        raise ValueError(f"未获取到基金 {code} 的历史数据")

    df = df.copy()
    df["净值日期"] = pd.to_datetime(df["净值日期"])
    df = df.sort_values("净值日期").reset_index(drop=True)

    df = df[(df["净值日期"] >= pd.to_datetime(start_date)) & (df["净值日期"] <= pd.to_datetime(end_date))]

    if df.empty:
        raise ValueError(f"基金 {code} 在指定时间区间内无数据")

    df = df.rename(columns={
        "净值日期": "日期",
        "单位净值": "收盘"
    })

    df["收盘"] = pd.to_numeric(df["收盘"], errors="coerce")
    df = df.dropna(subset=["收盘"]).reset_index(drop=True)

    if len(df) < 30:
        raise ValueError(f"基金 {code} 数据太少，至少需要 30 条，当前仅 {len(df)} 条")

    return df[["日期", "收盘"]]


def calculate_trend_persistence_factor(
        df: pd.DataFrame,
        short_window: int = 5,
        long_window: int = 20,
        vol_window: int = 20
) -> pd.Series:
    """
    历史走势持续性因子：
    趋势强 + 波动适中/较小 = 因子高

    因子定义：
    factor = (20日收益 * 0.7 + 5日收益 * 0.3) / 20日波动率
    """
    data = df.copy()

    data["ret_1"] = data["收盘"].pct_change()
    data["ret_5"] = data["收盘"].pct_change(short_window)
    data["ret_20"] = data["收盘"].pct_change(long_window)
    data["vol_20"] = data["ret_1"].rolling(vol_window).std()

    data["trend_factor"] = (data["ret_20"] * 0.7 + data["ret_5"] * 0.3) / (data["vol_20"] + 1e-8)

    return data["trend_factor"]


def build_factor_dataset(
        df: pd.DataFrame,
        future_days: int = 3,
        short_window: int = 5,
        long_window: int = 20,
        vol_window: int = 20
) -> pd.DataFrame:
    """
    构造因子验证数据集
    """
    data = df.copy()

    data["factor"] = calculate_trend_persistence_factor(
        data,
        short_window=short_window,
        long_window=long_window,
        vol_window=vol_window
    )

    # 未来N天收益
    data["future_return"] = data["收盘"].shift(-future_days) / data["收盘"] - 1

    # 未来是否上涨
    data["future_up"] = (data["future_return"] > 0).astype(int)

    data = data.dropna(subset=["factor", "future_return"]).reset_index(drop=True)
    return data


def evaluate_factor_effectiveness(data: pd.DataFrame, quantiles: int = 5) -> dict:
    """
    评估因子有效性
    """
    if data.empty:
        raise ValueError("因子数据为空，无法评估")

    result = {}

    # 1. 因子与未来收益的相关性（IC）
    ic = data["factor"].corr(data["future_return"])
    result["ic"] = None if pd.isna(ic) else round(float(ic), 4)

    # 2. 因子与未来上涨的相关性
    up_corr = data["factor"].corr(data["future_up"])
    result["up_corr"] = None if pd.isna(up_corr) else round(float(up_corr), 4)

    # 3. 分桶统计
    temp = data.copy()
    temp["bucket"] = pd.qcut(temp["factor"], q=quantiles, labels=False, duplicates="drop")

    bucket_stats = temp.groupby("bucket").agg(
        样本数=("factor", "count"),
        平均未来收益=("future_return", "mean"),
        上涨概率=("future_up", "mean"),
        因子均值=("factor", "mean")
    ).reset_index()

    bucket_list = []
    for _, row in bucket_stats.iterrows():
        bucket_list.append({
            "bucket": int(row["bucket"]),
            "sample_count": int(row["样本数"]),
            "factor_mean": round(float(row["因子均值"]), 4),
            "avg_future_return": round(float(row["平均未来收益"]), 4),
            "up_probability": round(float(row["上涨概率"]), 4),
        })

    result["bucket_stats"] = bucket_list

    if len(bucket_list) >= 2:
        low_bucket = bucket_list[0]
        high_bucket = bucket_list[-1]

        result["high_bucket_up_probability"] = high_bucket["up_probability"]
        result["low_bucket_up_probability"] = low_bucket["up_probability"]
        result["high_bucket_avg_return"] = high_bucket["avg_future_return"]
        result["low_bucket_avg_return"] = low_bucket["avg_future_return"]

        effective = (
            high_bucket["up_probability"] > low_bucket["up_probability"]
            and high_bucket["avg_future_return"] > low_bucket["avg_future_return"]
        )
        result["is_effective"] = effective
    else:
        result["high_bucket_up_probability"] = None
        result["low_bucket_up_probability"] = None
        result["high_bucket_avg_return"] = None
        result["low_bucket_avg_return"] = None
        result["is_effective"] = False

    return result


def calc_prediction_score(
        latest_factor: float,
        latest_bucket: int,
        bucket_count: int,
        history_up_probability: float,
        history_avg_future_return: float,
        ic: float | None,
        is_effective: bool
) -> dict:
    """
    计算买入分数（满分100）
    分数越高，越值得买

    设计思路：
    1. 历史上涨概率：权重最高
    2. 历史平均未来收益：第二重要
    3. 当前桶位置：桶越高越好
    4. IC：因子整体有效性补充
    5. is_effective：整体有效再加分
    """

    # 1) 历史上涨概率得分（0~45）
    # 50% 视为中性；80%接近高分
    up_prob_score = history_up_probability * 45

    # 2) 历史平均收益得分（0~30）
    # 以 future_return 为比例，如 0.03 = 3%
    # 这里做个线性映射，[-3%, +5%] 映射到 [0, 30]
    min_ret = -0.03
    max_ret = 0.05
    clipped_ret = min(max(history_avg_future_return, min_ret), max_ret)
    ret_score = (clipped_ret - min_ret) / (max_ret - min_ret) * 30

    # 3) 当前所在分桶得分（0~15）
    if bucket_count <= 1:
        bucket_score = 7.5
    else:
        bucket_score = latest_bucket / (bucket_count - 1) * 15

    # 4) IC得分（0~5）
    if ic is None:
        ic_score = 2.5
    else:
        # 把 [-0.1, 0.1] roughly 映射到 [0, 5]
        clipped_ic = min(max(ic, -0.1), 0.1)
        ic_score = (clipped_ic + 0.1) / 0.2 * 5

    # 5) 因子整体是否有效（0 或 5）
    effective_score = 5 if is_effective else 0

    total_score = up_prob_score + ret_score + bucket_score + ic_score + effective_score
    total_score = _clip_score(total_score)

    # 给出买入建议
    if total_score >= 85:
        buy_signal = "强烈买入"
    elif total_score >= 70:
        buy_signal = "可以买入"
    elif total_score >= 55:
        buy_signal = "可以关注"
    elif total_score >= 40:
        buy_signal = "暂不建议买入"
    else:
        buy_signal = "不建议买入"

    return {
        "score": total_score,
        "buy_signal": buy_signal,
        "score_detail": {
            "up_prob_score": round(up_prob_score, 2),
            "ret_score": round(ret_score, 2),
            "bucket_score": round(bucket_score, 2),
            "ic_score": round(ic_score, 2),
            "effective_score": round(effective_score, 2),
        }
    }


def predict_by_current_factor(data: pd.DataFrame, eval_result: dict, quantiles: int = 5) -> dict:
    """
    根据当前最新因子值，映射历史分桶结果，给出预测
    """
    if data.empty:
        raise ValueError("数据为空，无法预测")

    temp = data.copy()
    temp["bucket"] = pd.qcut(temp["factor"], q=quantiles, labels=False, duplicates="drop")

    latest_row = temp.iloc[-1]
    latest_factor = float(latest_row["factor"])
    latest_bucket = int(latest_row["bucket"])

    bucket_stats = temp.groupby("bucket").agg(
        平均未来收益=("future_return", "mean"),
        上涨概率=("future_up", "mean"),
        样本数=("factor", "count")
    ).reset_index()

    hit = bucket_stats[bucket_stats["bucket"] == latest_bucket]
    if hit.empty:
        raise ValueError("未找到当前因子对应分桶")

    avg_future_return = float(hit.iloc[0]["平均未来收益"])
    up_probability = float(hit.iloc[0]["上涨概率"])
    sample_count = int(hit.iloc[0]["样本数"])
    bucket_count = len(bucket_stats)

    # 中文预测结论
    if up_probability >= 0.65:
        signal = "较大概率上涨"
    elif up_probability >= 0.55:
        signal = "偏上涨"
    elif up_probability >= 0.45:
        signal = "震荡"
    elif up_probability >= 0.35:
        signal = "偏下跌"
    else:
        signal = "较大概率下跌"

    score_result = calc_prediction_score(
        latest_factor=latest_factor,
        latest_bucket=latest_bucket,
        bucket_count=bucket_count,
        history_up_probability=up_probability,
        history_avg_future_return=avg_future_return,
        ic=eval_result.get("ic"),
        is_effective=eval_result.get("is_effective", False)
    )

    return {
        "latest_factor": round(latest_factor, 4),
        "latest_bucket": latest_bucket,
        "history_up_probability": round(up_probability, 4),
        "history_avg_future_return": round(avg_future_return, 4),
        "sample_count": sample_count,
        "signal": signal,
        "prediction_score": score_result["score"],
        "buy_signal": score_result["buy_signal"],
        "score_detail": score_result["score_detail"]
    }


def analyze_fund_trend_persistence(
        code: str,
        start_date: str = "20220101",
        end_date: str = get_today_str(),
        future_days: int = 3,
        quantiles: int = 5
) -> dict:
    """
    主函数：
    输入基金 code，输出因子验证 + 当前预测结果 + 买入分数
    """
    df = get_fund_hist_df(code, start_date=start_date, end_date=end_date)

    dataset = build_factor_dataset(
        df=df,
        future_days=future_days,
        short_window=5,
        long_window=20,
        vol_window=20
    )

    eval_result = evaluate_factor_effectiveness(dataset, quantiles=quantiles)
    predict_result = predict_by_current_factor(dataset, eval_result=eval_result, quantiles=quantiles)

    return {
        "code": code,
        "data_count": len(dataset),
        "future_days": future_days,
        "factor_name": "历史走势持续性因子",
        "evaluation": eval_result,
        "prediction": predict_result
    }


if __name__ == "__main__":
    code = "018846"   # 换成你的基金代码

    result = analyze_fund_trend_persistence(
        code=code,
        start_date="20220101",
        future_days=3,
        quantiles=5
    )

    print("========== 分析结果 ==========")
    print(f"基金代码: {result['code']}")
    print(f"样本数: {result['data_count']}")
    print(f"预测未来天数: {result['future_days']}")
    print(f"因子名称: {result['factor_name']}")

    print("\n========== 因子有效性 ==========")
    print(f"IC: {result['evaluation']['ic']}")
    print(f"因子与未来上涨相关性: {result['evaluation']['up_corr']}")
    print(f"是否有效: {result['evaluation']['is_effective']}")
    print(f"最高分桶上涨概率: {result['evaluation']['high_bucket_up_probability']}")
    print(f"最低分桶上涨概率: {result['evaluation']['low_bucket_up_probability']}")
    print(f"最高分桶平均收益: {result['evaluation']['high_bucket_avg_return']}")
    print(f"最低分桶平均收益: {result['evaluation']['low_bucket_avg_return']}")

    print("\n========== 当前预测 ==========")
    print(f"当前因子值: {result['prediction']['latest_factor']}")
    print(f"当前所属分桶: {result['prediction']['latest_bucket']}")
    print(f"历史上涨概率: {result['prediction']['history_up_probability']}")
    print(f"历史平均未来收益: {result['prediction']['history_avg_future_return']}")
    print(f"样本数: {result['prediction']['sample_count']}")
    print(f"预测结论: {result['prediction']['signal']}")

    print("\n========== 买入评分 ==========")
    print(f"买入分数(满分100): {result['prediction']['prediction_score']}")
    print(f"买入建议: {result['prediction']['buy_signal']}")
    print("分数明细:")
    for k, v in result["prediction"]["score_detail"].items():
        print(f"  {k}: {v}")

    print("\n========== 分桶详情 ==========")
    for item in result["evaluation"]["bucket_stats"]:
        print(item)