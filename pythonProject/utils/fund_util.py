import akshare as ak

def is_etf_fund(fund_code: str) -> bool:
    """
    判断是否是ETF基金
    :param fund_code:   基金code
    :return:    是否是ETF基金
    """
    df = ak.fund_name_em()
    row = df[df["基金代码"] == fund_code]

    if row.empty:
        raise ValueError(f"未找到基金代码: {fund_code}")

    fund_type = str(row.iloc[0]["基金类型"])
    return "ETF" in fund_type.upper()