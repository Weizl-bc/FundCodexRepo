from functools import lru_cache

import akshare as ak


def get_fund_name_df():
    """
    缓存基金基础信息列表，避免同一进程内重复请求
    :return: 基金基础信息 DataFrame
    """
    return ak.fund_name_em()

@lru_cache(maxsize=1)
def get_fund_row(fund_code: str):
    """
    根据基金代码获取基金基础信息
    :param fund_code: 基金 code
    :return: 基金行数据
    """
    df = get_fund_name_df()
    row = df[df["基金代码"] == fund_code]

    if row.empty:
        raise ValueError(f"未找到基金代码: {fund_code}")

    return row.iloc[0]


def is_pure_etf_fund(fund_code: str) -> bool:
    """
    判断是否是纯 ETF 基金，不包含 ETF 联接基金
    :param fund_code: 基金 code
    :return: 是否是纯 ETF 基金
    """
    fund_row = get_fund_row(fund_code)
    fund_name = str(fund_row["基金简称"]).upper()
    fund_type = str(fund_row["基金类型"]).upper()

    return "ETF" in fund_name and "联接" not in fund_name and "ETF联接" not in fund_type


def is_etf_related_fund(fund_code: str) -> bool:
    """
    判断是否是 ETF 相关基金，包含纯 ETF 和 ETF 联接基金
    :param fund_code: 基金 code
    :return: 是否是 ETF 相关基金
    """
    fund_row = get_fund_row(fund_code)
    fund_name = str(fund_row["基金简称"]).upper()
    fund_type = str(fund_row["基金类型"]).upper()

    return "ETF" in fund_name or "ETF" in fund_type


def is_etf_fund(fund_code: str) -> bool:
    """
    兼容旧方法名。
    这里的 ETF 指纯 ETF 基金，不包含 ETF 联接基金。
    :param fund_code: 基金 code
    :return: 是否是纯 ETF 基金
    """
    return is_pure_etf_fund(fund_code)
