def calculate_ma_factor(df):
    """
    计算ma
    :param df: 需要包含单位净值，净值日期，可以采用ak.fund_etf_hist_em
    :return:
    """
    df = df.copy()
    df["MA5"] = df["单位净值"].rolling(5).mean()
    df["MA10"] = df["单位净值"].rolling(10).mean()
    df["MA20"] = df["单位净值"].rolling(20).mean()
    ma5 = df.iloc[-1]["MA5"]
    ma10 = df.iloc[-1]["MA10"]
    ma20 = df.iloc[-1]["MA20"]

    if ma5 > ma10 > ma20:
        score = 100
    elif ma5 > ma10:
        score = 80
    elif ma5 < ma10 < ma20:
        score = 20
    else:
        score = 60
    return score
