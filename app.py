import OpenDartReader
from pykrx import stock
import streamlit as st
from datetime import datetime
import datetime as dt


# ==== 0. 객체 생성 ====
# 객체 생성 (API KEY 지정) 
api_key = st.secrets["api_key"]

dart = OpenDartReader(api_key) 

bsns_year = 2021
bsns_qtr = 3

today = datetime.now().strftime("%Y%m%d")
day1wkago = (datetime.now() - dt.timedelta(days=7)).strftime("%Y%m%d")

allTickers = stock.get_market_price_change(day1wkago, today, market="ALL").reset_index()[['티커', '종목명']]

tickers = allTickers['종목명'].tolist()

stocknm = st.sidebar.selectbox("종목명", options=tickers, index=tickers.index('삼성전자'))
bsns_year = st.sidebar.number_input("연도", value=2021)
bsns_qtr = st.sidebar.number_input("분기", value=3)

# 종목명(stocknm)을 ticker(stockcd) 로 변경
stockcd = allTickers[(allTickers['종목명'] == stocknm)]['티커'].values[0]

dict_qtr = {1:11013, 2:11012, 3:11014, 4:11011}

# 전년도말 재무제표
fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='CFS', reprt_code=11011) 
# 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
if fs_Prev_Yr is None:
    fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='OFS', reprt_code=11011) 

# 가장 최근 분기, 그에 따라 reprt_code 가 변경되어야 함
# reprt_code - 1분기보고서 : 11013 반기보고서 : 11012 3분기보고서 : 11014 사업보고서 : 11011
fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='CFS', reprt_code=dict_qtr[bsns_qtr]) 
# 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
if fs_YQ is None:
    fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='OFS', reprt_code=dict_qtr[bsns_qtr]) 

# 자본
#fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Equity']), ]

# 부채
#fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Liabilities']), ]

# 당기순익

# 연결재무제표
#fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent', 'ifrs-full_ProfitLoss']), ]

# 개별재무제표
#fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), ]

# 자본과 부채는 재무상태표에서 당기금액('thstrm_amount') 값을 가져오면 됨
equity = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Equity']), 'thstrm_amount'].replace(",", "")) # 당기자본(자본총계)
liability = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Liabilities']), 'thstrm_amount'].replace(",", "")) # 당기부채(부채총계)
assets = equity + liability # 자산총계

try:
    # 전년도 당분기 누적금액
    profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'frmtrm_add_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_add_amount'].replace(",", "")) # 당기순이익

    grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'frmtrm_add_amount'].replace(",", "")) # 매출총이익
    # 전년도말 금액
    grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_amount'].replace(",", "")) # 매출총이익
    # 가장 최근 분기 금액
    grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_add_amount'].replace(",", "")) # 매출총이익

    # 가장 최근 분기 금액
    ocf_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_CashFlowsFromUsedInOperatingActivities']), 'thstrm_amount'].replace(",", ""))
    capex_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities']), 'thstrm_amount'].replace(",", "")) \
                  - int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities']), 'thstrm_amount'].replace(",", ""))

except:
    # 전년도 당분기 누적금액
    profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'frmtrm_add_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_add_amount'].replace(",", "")) # 당기순이익

    # 가장 최근 분기 금액
    ocf_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_CashFlowsFromUsedInOperatingActivities']), 'thstrm_amount'].replace(",", ""))
    capex_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities']), 'thstrm_amount'].replace(",", "")) \
                  - int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities']), 'thstrm_amount'].replace(",", ""))

    try:
        # 전년도 당분기 누적금액
        grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'frmtrm_add_amount'].replace(",", "")) # 매출총이익
        # 전년도말 금액
        grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_amount'].replace(",", "")) # 매출총이익
        # 가장 최근 분기 금액
        grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_add_amount'].replace(",", "")) # 매출총이익

    except:
        # 매출총이익이 없고 영업수익이 있는 회사에 대한 예외처리(NAVER)
        # 전년도 당분기 누적금액
        grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_Revenue']), 'frmtrm_add_amount'].replace(",", "")) # 영업수익
        # 전년도말 금액
        grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_Revenue']), 'thstrm_amount'].replace(",", "")) # 영업수익
        # 가장 최근 분기 금액
        grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_Revenue']), 'thstrm_add_amount'].replace(",", "")) # 영업수익


profit = (profit_Prev_Yr-profit_Prev_YQ) + profit_Curr_YQ
grossprofit = (grossprofit_Prev_Yr-grossprofit_Prev_YQ) + grossprofit_Curr_YQ
ocf = ocf_Curr_YQ
capex = capex_Curr_YQ
fcf = ocf - capex

compName = stock.get_market_ticker_name(stockcd)

st.markdown(f"# {compName} ({stockcd})")

st.markdown(f"자본금: {equity:,.0f}<br>직전 4분기 당기순익: {profit:,.0f}<br>ROE: {profit/equity:,.1%}", unsafe_allow_html=True)


mktcap = stock.get_market_cap(day1wkago, today, stockcd)['시가총액'].tail(1).values[0]
numstk = stock.get_market_cap(day1wkago, today, stockcd)['상장주식수'].tail(1).values[0]

st.write(f"시가총액: {mktcap:,.0f} 원")
st.write(f"주식수: {numstk:,.0f}")
st.write(f"주당자산: {assets/numstk:,.0f} 원")
st.write(f"주당이익: {profit/numstk:,.0f} 원")
st.write(f"주가: {mktcap/numstk:,.0f} 원")
st.write(f"ROA: {profit/assets:,.1%}")
st.write(f"GP/A: {grossprofit/assets:,.1%}")
st.write(f"FCF/Equity: {fcf/equity:,.1%}")

# 부채비율
# 현금및현금성자산비율
# 영업이익률
# FCF: OCF - CAPEX
# OCF: ifrs-full_CashFlowsFromUsedInOperatingActivities(영업활동을 통해 유입된 현금흐름)
# CAPEX: ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities(유형자산의 취득) - ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities(무형자산의 취득)