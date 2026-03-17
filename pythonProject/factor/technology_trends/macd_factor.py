def calculate_macd_factor(df):
    df = df.copy()

    price = df["单位净值"]  # 如果是ETF改成 df["收盘"]

    ema12 = price.ewm(span=12, adjust=False).mean()
    ema26 = price.ewm(span=26, adjust=False).mean()

    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()

    macd = 2 * (dif - dea)

    dif_now = dif.iloc[-1]
    dea_now = dea.iloc[-1]
    dif_prev = dif.iloc[-2]
    dea_prev = dea.iloc[-2]

    # 判断金叉死叉
    if dif_prev < dea_prev and dif_now > dea_now:
        score = 90   # 金叉
    elif dif_now > dea_now:
        score = 75   # 多头
    elif dif_now < dea_now:
        score = 40   # 空头
    else:
        score = 60

    return score