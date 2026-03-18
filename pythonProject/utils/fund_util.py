from functools import lru_cache

import akshare as ak


@lru_cache(maxsize=1)
def get_fund_name_df():
    """
    获取基金基础信息列表。

    该方法统一封装 `ak.fund_name_em()`，并在当前进程内缓存结果，
    避免多个模块重复请求同一份基金基础数据。

    Returns:
        pandas.DataFrame: 基金基础信息表，通常包含 `基金代码`、`基金简称`、`基金类型`。
    """
    df = ak.fund_name_em().copy()
    df["基金代码"] = df["基金代码"].astype(str).str.zfill(6)
    return df

@lru_cache(maxsize=512)
def get_fund_row(fund_code: str):
    """
    根据基金代码获取单只基金的基础信息。

    Args:
        fund_code: 六位基金代码。

    Returns:
        pandas.Series: 对应基金的单行基础信息。

    Raises:
        ValueError: 当基金代码不存在时抛出。
    """
    normalized_code = str(fund_code).strip().zfill(6)
    df = get_fund_name_df()
    row = df[df["基金代码"] == normalized_code]

    if row.empty:
        raise ValueError(f"未找到基金代码: {normalized_code}")

    return row.iloc[0]


@lru_cache(maxsize=512)
def get_fund_base_info(fund_code: str) -> dict:
    """
    获取基金基础信息的轻量字典。

    Args:
        fund_code: 六位基金代码。

    Returns:
        dict: 包含 `fund_code`、`fund_name`、`fund_type` 三个字段。
    """
    row = get_fund_row(fund_code)
    return {
        "fund_code": str(row["基金代码"]).zfill(6),
        "fund_name": row.get("基金简称"),
        "fund_type": row.get("基金类型"),
    }


def is_pure_etf_fund(fund_code: str) -> bool:
    """
    判断是否为纯 ETF 基金。

    纯 ETF 不包含 ETF 联接基金，因为两者后续使用的数据接口通常不同。

    Args:
        fund_code: 六位基金代码。

    Returns:
        bool: 纯 ETF 返回 True，否则返回 False。
    """
    fund_row = get_fund_row(fund_code)
    fund_name = str(fund_row["基金简称"]).upper()
    fund_type = str(fund_row["基金类型"]).upper()

    return "ETF" in fund_name and "联接" not in fund_name and "ETF联接" not in fund_type


def is_etf_related_fund(fund_code: str) -> bool:
    """
    判断是否为 ETF 相关基金。

    ETF 相关基金包含纯 ETF 和 ETF 联接基金，适合用于宽口径分类判断。

    Args:
        fund_code: 六位基金代码。

    Returns:
        bool: ETF 或 ETF 联接返回 True，否则返回 False。
    """
    fund_row = get_fund_row(fund_code)
    fund_name = str(fund_row["基金简称"]).upper()
    fund_type = str(fund_row["基金类型"]).upper()

    return "ETF" in fund_name or "ETF" in fund_type


def get_fund_type_label(fund_code: str) -> str:
    """
    返回统一的基金类型标签。

    当前只区分两类：
    - `ETF`: 场内纯 ETF
    - `OPEN`: 普通开放式基金或 ETF 联接基金

    Args:
        fund_code: 六位基金代码。

    Returns:
        str: `ETF` 或 `OPEN`。
    """
    return "ETF" if is_pure_etf_fund(fund_code) else "OPEN"


def is_etf_fund(fund_code: str) -> bool:
    """
    兼容旧方法名。

    该方法语义等同于 `is_pure_etf_fund`，保留它是为了不影响现有调用方。

    Args:
        fund_code: 六位基金代码。

    Returns:
        bool: 是否为纯 ETF。
    """
    return is_pure_etf_fund(fund_code)
