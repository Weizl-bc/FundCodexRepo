import akshare as ak

from factor.capital_flow_factor import fund_capital_flow_score
from factor.historical_trend.hist import analyze_fund_trend_persistence
from factor.historical_trend.path_quality import evaluate_path_quality
from factor.historical_trend.relative_return import calculate_relative_return_score
from factor.technology_trends.ma_factor import calculate_ma_factor
from factor.technology_trends.macd_factor import calculate_macd_factor
from factor.technology_trends.momentum_factor import calculate_momentum_factor
from factor.technology_trends.rsi_factor import calculate_rsi_factor
from factor.technology_trends.volume_factor import calculate_volume_factor
from utils.date_util import get_last_year_date
from utils.fund_util import is_etf_related_fund, is_pure_etf_fund, get_fund_row

fund_code = "008021"
pure_etf_fund = is_pure_etf_fund(fund_code)
etf_related_fund = is_etf_related_fund(fund_code)

# print("fund name", get_fund_row(fund_code))
# print("pure_etf_fund", pure_etf_fund)
# print("etf_related_fund", etf_related_fund)

if pure_etf_fund:
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

momentum_factor_score = calculate_momentum_factor(df)
ma_factor_score = calculate_ma_factor(df)
rsi_factor_score = calculate_rsi_factor(df)
macd_factor_score = calculate_macd_factor(df)
volume_factor_score = calculate_volume_factor(df)
capital_flow_score = fund_capital_flow_score(fund_code)["detail"]["scale_score"]
relative_return_score = calculate_relative_return_score(fund_code)["score"]
hist_score = analyze_fund_trend_persistence(fund_code)
path_quality = evaluate_path_quality(fund_code)

# print(df.head())
print("momentum_factor", momentum_factor_score)
print("ma_factor", ma_factor_score)
print("rsi_factor", rsi_factor_score)
print("macd_factor", macd_factor_score)
print("volume_factor", volume_factor_score)
print("capital_flow_score", capital_flow_score)
print("relative_return_score", relative_return_score)
print("hist_score", hist_score['prediction']['prediction_score'])
print("path_quality", path_quality["score"])
