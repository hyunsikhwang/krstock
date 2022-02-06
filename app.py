import OpenDartReader
from pykrx import stock
import streamlit as st


# ==== 0. 객체 생성 ====
# 객체 생성 (API KEY 지정) 
api_key = st.secrets["api_key"]

dart = OpenDartReader(api_key) 

stockcd = "005930"
bsns_year = 2021
bsns_qtr = 3

stockcd = st.text_input("주식종목코드", value="005930")

dict_qtr = {1:11013, 2:11012, 3:11014, 4:11011}

fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='CFS', reprt_code=dict_qtr[bsns_qtr]) 
# 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
if fs_Prev_Yr is None:
    fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='OFS', reprt_code=dict_qtr[bsns_qtr]) 

# 가장 최근 분기, 그에 따라 reprt_code 가 변경되어야 함
# reprt_code - 1분기보고서 : 11013 반기보고서 : 11012 3분기보고서 : 11014 사업보고서 : 11011
fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='CFS', reprt_code=11014) 
# 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
if fs_YQ is None:
    fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='OFS', reprt_code=11014) 

# 자본
fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Equity']), ]
# 부채
fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Liabilities']), ]
# 당기순익
# 연결재무제표
fs_YQ.loc[fs_YQ['sj_div'].isin(['IS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent', 'ifrs-full_ProfitLoss']), ]
# 개별재무제표
fs_YQ.loc[fs_YQ['sj_div'].isin(['IS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), ]

# 자본과 부채는 재무상태표에서 당기금액('thstrm_amount') 값을 가져오면 됨
equity = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Equity']), 'thstrm_amount'].replace(",", "")) # 당기자본(자본총계)
liability = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['BS']) & fs_YQ['account_id'].isin(['ifrs-full_Liabilities']), 'thstrm_amount'].replace(",", "")) # 당기부채(부채총계)
assets = equity + liability # 자산총계

# 전년도 당분기 금액
try:
    profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'frmtrm_add_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_add_amount'].replace(",", "")) # 당기순이익
    # 직전 4분기 누적 순익
except:
    profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'frmtrm_add_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_add_amount'].replace(",", "")) # 당기순이익
    # 직전 4분기 누적 순익

profit = (profit_Prev_Yr-profit_Prev_YQ) + profit_Curr_YQ

st.markdown(f"자본금: {equity:,.0f}<br>직전 4분기 당기순익: {profit:,.0f}<br>ROE: {profit/equity:,.1%}", unsafe_allow_html=True)

mktcap = stock.get_market_cap("20220204", "20220204", stockcd)['시가총액'].head(1).values[0]
numstk = stock.get_market_cap("20220204", "20220204", stockcd)['상장주식수'].head(1).values[0]

st.write(mktcap)
st.write(numstk)
st.write(assets/numstk)
st.write(profit/numstk)
st.write(mktcap/numstk)
st.write(profit/assets*100)
