def calculate_volume_factor(df):
    df = df.copy()

    if "成交量" not in df.columns:
        return 50  # 没有成交量就返回中性

    volume = df["成交量"]
    close = df["收盘"]

    avg_volume = volume.rolling(5).mean()

    volume_ratio = volume.iloc[-1] / avg_volume.iloc[-1]

    price_change = close.iloc[-1] - close.iloc[-2]

    if price_change > 0 and volume_ratio > 1.5:
        score = 90
    elif price_change > 0:
        score = 75
    elif price_change < 0 and volume_ratio > 1.5:
        score = 30
    else:
        score = 60

    return score