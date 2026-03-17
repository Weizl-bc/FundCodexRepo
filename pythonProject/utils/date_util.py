from datetime import datetime, timedelta


def get_last_year_date():
    """
    获取前一年的日期（365天前）

    Returns:
        str: 日期字符串，格式 yyyymmdd
    """
    today = datetime.today()
    last_year = today - timedelta(days=365)
    return last_year.strftime("%Y%m%d")

