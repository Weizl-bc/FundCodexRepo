import akshare as ak

from factor.technology_trends.momentum_factor import calculate_momentum_factor
from utils.date_util import get_last_year_date
from utils.fund_util import is_etf_fund

fund_code = "019498"
etf_fund = False

etf_fund = is_etf_fund(fund_code)

if etf_fund:
    df = ak.fund_etf_hist_em(
        symbol=fund_code,
        period="daily",
        start_date=get_last_year_date(),
        adjust="qfq"
    )
else:
    df = ak.fund_open_fund_info_em(
        symbol=fund_code,
        indicator="单位净值走势",
        period="3年"
    )

print(df.head())
print(calculate_momentum_factor(df))