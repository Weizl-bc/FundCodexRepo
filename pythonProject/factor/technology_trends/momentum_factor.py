def calculate_momentum_factor(df):
    """
    动量因子
    计算公式：momentum_5d = (today_price - price_5_days_ago) / price_5_days_ago
    :df
        普通基金：ak.fund_open_fund_info_em(fund="017641",indicator="单位净值走势")
        etf基金：ak.fund_etf_hist_em(fund="017641",indicator="单位净值走势")
    :return: 分数，满分100分
    """
    df["momentum_5"] = df["单位净值"].pct_change(5)

    m = df.iloc[-1]["momentum_5"]

    if m < -0.05:
        return 20
    elif m < -0.02:
        return 40
    elif m < 0.01:
        return 60
    elif m < 0.04:
        return 80
    elif m < 0.07:
        return 90
    elif m < 0.10:
        return 85
    else:
        return 70
