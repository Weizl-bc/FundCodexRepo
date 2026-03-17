def calculate_rsi_factor(df, period=14):
    df = df.copy()

    if len(df) < period + 1:
        return 50

    delta = df["单位净值"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    # 防止除零
    rs = avg_gain / avg_loss.replace(0, 1e-8)
    rsi = 100 - (100 / (1 + rs))

    rsi_value = rsi.iloc[-1]

    if rsi_value < 25:
        score = 90
    elif rsi_value < 35:
        score = 80
    elif rsi_value < 50:
        score = 65
    elif rsi_value < 65:
        score = 75
    elif rsi_value < 75:
        score = 60
    else:
        score = 40

    return score