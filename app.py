import OpenDartReader
from pykrx import stock
import streamlit as st
from datetime import datetime
import datetime as dt
from pytz import timezone, utc
import bs4
import requests
import json
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def post_beautiful_soup(url, payload):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return bs4.BeautifulSoup(requests.post(url, headers=headers, data=payload).text, "lxml")

# 전종목 기본정보
def KRX_12005():
    df_result = pd.DataFrame()
 
    url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'

    df_result = pd.DataFrame()

    payload = {'bld': 'dbms/MDC/STAT/standard/MDCSTAT01901',
               'mktId': 'ALL',
               'share': '1',
               'csvxls_isNo': 'false'
    }
    MktData = post_beautiful_soup(url, payload)

    data = json.loads(MktData.text)
    #display(pd.DataFrame(data['block1']))

    df_result = pd.DataFrame(data['OutBlock_1'])

    return df_result   

# 시가총액
def get_market_cap(end_dd, quote):
    isu_cd = KRX_12005()
    quote1 = isu_cd[(isu_cd['ISU_SRT_CD']==quote)]['ISU_CD'].values[0]

    url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
 
    strt_dd = (datetime.now() - relativedelta(days=7)).strftime("%Y%m%d")
    payload = {'bld': 'dbms/MDC/STAT/standard/MDCSTAT01701',
               'isuCd': quote1,
               'isuCd2': quote1,
               'param1isuCd_finder_stkisu0_7': 'ALL',
               'strtDd': strt_dd,
               'endDd': end_dd,
               'adjStkPrc_check': 'Y',
               'adjStkPrc': '2',
               'share': '1',
               'money': '1',
               'csvxls_isNo': 'false'
              }
 
    MktData = post_beautiful_soup(url, payload)
 
    data = json.loads(MktData.text)
    #display(data['output'])
    df_result = pd.DataFrame(data['output'])[['TRD_DD', 'TDD_CLSPRC', 'MKTCAP', 'LIST_SHRS']]
    df_result['MKTCAP'] = df_result['MKTCAP'].str.replace(',', '').astype(float)
    df_result['LIST_SHRS'] = df_result['LIST_SHRS'].str.replace(',', '').astype(float)
    df_result.rename(columns = {'MKTCAP':'시가총액', 'LIST_SHRS':'상장주식수'}, inplace=True)
 
    return df_result


# ==== 0. 객체 생성 ====
# 객체 생성 (API KEY 지정) 
api_key = st.secrets["api_key"]

dart = OpenDartReader(api_key) 

#today = datetime.now().strftime("%Y%m%d")
KST = timezone('Asia/Seoul')
now = datetime.utcnow()
today = utc.localize(now).astimezone(KST).strftime("%Y%m%d")

day1wkago = (utc.localize(now).astimezone(KST) - dt.timedelta(days=7)).strftime("%Y%m%d")

allTickers = stock.get_market_price_change(day1wkago, today, market="ALL").reset_index()[['티커', '종목명']]

tickers = allTickers['종목명'].tolist()

stocknm = st.sidebar.selectbox("종목명", options=tickers, index=tickers.index('삼성전자'))
bsns_year = st.sidebar.number_input("연도", value=2023)
bsns_qtr = st.sidebar.number_input("분기", value=1)

# 종목명(stocknm)을 ticker(stockcd) 로 변경
stockcd = allTickers[(allTickers['종목명'] == stocknm)]['티커'].values[0]

dict_qtr = {1:'11013', 2:'11012', 3:'11014', 4:'11011'}

try:
    # 전년도말 재무제표
    fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='CFS', reprt_code='11011') 
except:
    # 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
    fs_Prev_Yr = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year-1}', fs_div='OFS', reprt_code='11011') 

try:
    # 가장 최근 분기, 그에 따라 reprt_code 가 변경되어야 함
    # reprt_code - 1분기보고서 : 11013 반기보고서 : 11012 3분기보고서 : 11014 사업보고서 : 11011
    fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='CFS', reprt_code=dict_qtr[bsns_qtr]) 
except:
    # 연결재무제표가 없는 경우에는 개별재무제표 읽어옴
    fs_YQ = dart.finstate_all(corp=stockcd, bsns_year=f'{bsns_year}', fs_div='OFS', reprt_code=dict_qtr[bsns_qtr]) 

# white space 가 간혹 존재하여 에러가 발생하는 문제가 있어서, 이를 0 처리함 (20230515)
fs_YQ['thstrm_amount'] = fs_YQ['thstrm_amount'].apply(lambda x: 0 if x == '' else x)

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
    if bsns_qtr != 4:
        profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'frmtrm_add_amount' if bsns_qtr != 4 else 'frmtrm_amount'].replace(",", "")) # 당기순이익
    else:
        profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'frmtrm_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLossAttributableToOwnersOfParent']), 'thstrm_add_amount' if bsns_qtr != 4 else 'thstrm_amount'].replace(",", "")) # 당기순이익

    grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'frmtrm_add_amount' if bsns_qtr != 4 else 'frmtrm_amount'].replace(",", "")) # 매출총이익
    # 전년도말 금액
    grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_amount'].replace(",", "")) # 매출총이익
    # 가장 최근 분기 금액
    grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_add_amount' if bsns_qtr != 4 else 'thstrm_amount'].replace(",", "")) # 매출총이익

    ocf_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_CashFlowsFromUsedInOperatingActivities']), 'thstrm_amount'].replace(",", ""))
    try:
        # 가장 최근 분기 금액
        capex_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['유형자산의 취득']), 'thstrm_amount'].replace(",", "")) \
                      + int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['무형자산의 취득']), 'thstrm_amount'].replace(",", ""))
        fcf_2_Curr_YQ = 0
    except:
        fcf_2_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['영업활동현금흐름']), 'thstrm_amount'].replace(",", "")) \
                      - int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['투자활동현금흐름']), 'thstrm_amount'].replace(",", ""))
        capex_Curr_YQ = 0

except:
    # 전년도 당분기 누적금액
    profit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'frmtrm_add_amount' if bsns_qtr != 4 else 'frmtrm_amount'].replace(",", "")) # 당기순이익
    # 전년도말 금액
    profit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_amount'].replace(",", "")) # 당기순이익
    # 가장 최근 분기 금액
    profit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_ProfitLoss']), 'thstrm_add_amount' if bsns_qtr != 4 else 'thstrm_amount'].replace(",", "")) # 당기순이익

    # 가장 최근 분기 금액
    ocf_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_id'].isin(['ifrs-full_CashFlowsFromUsedInOperatingActivities']), 'thstrm_amount'].replace(",", ""))
    try:
        capex_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['유형자산의 취득']), 'thstrm_amount'].replace(",", "")) \
                      + int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['무형자산의 취득']), 'thstrm_amount'].replace(",", ""))
        fcf_2_Curr_YQ = 0
    except:
        fcf_2_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['영업활동현금흐름']), 'thstrm_amount'].replace(",", "")) \
                      - int(fs_YQ.loc[fs_YQ['sj_div'].isin(['CF']) & fs_YQ['account_nm'].isin(['투자활동현금흐름']), 'thstrm_amount'].replace(",", ""))
        capex_Curr_YQ = 0

    try:
        # 전년도 당분기 누적금액
        grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'frmtrm_add_amount' if bsns_qtr != 4 else 'frmtrm_amount'].replace(",", "")) # 매출총이익
        # 전년도말 금액
        grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_amount'].replace(",", "")) # 매출총이익
        # 가장 최근 분기 금액
        grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_GrossProfit']), 'thstrm_add_amount' if bsns_qtr != 4 else 'thstrm_amount'].replace(",", "")) # 매출총이익

    except:
        # 매출총이익이 없고 영업수익이 있는 회사에 대한 예외처리(NAVER)
        # 전년도 당분기 누적금액
        grossprofit_Prev_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_Revenue']), 'frmtrm_add_amount' if bsns_qtr != 4 else 'frmtrm_amount'].replace(",", "")) # 영업수익
        # 전년도말 금액
        grossprofit_Prev_Yr = int(fs_Prev_Yr.loc[fs_Prev_Yr['sj_div'].isin(['IS', 'CIS']) & fs_Prev_Yr['account_id'].isin(['ifrs-full_Revenue']), 'thstrm_amount'].replace(",", "")) # 영업수익
        # 가장 최근 분기 금액
        grossprofit_Curr_YQ = int(fs_YQ.loc[fs_YQ['sj_div'].isin(['IS', 'CIS']) & fs_YQ['account_id'].isin(['ifrs-full_Revenue']), 'thstrm_add_amount' if bsns_qtr != 4 else 'thstrm_amount'].replace(",", "")) # 영업수익


profit = (profit_Prev_Yr-profit_Prev_YQ) + profit_Curr_YQ
grossprofit = (grossprofit_Prev_Yr-grossprofit_Prev_YQ) + grossprofit_Curr_YQ
ocf = ocf_Curr_YQ
capex = capex_Curr_YQ
if fcf_2_Curr_YQ == 0:
    fcf = ocf - capex
else:
    fcf = fcf_2_Curr_YQ

compName = stock.get_market_ticker_name(stockcd)

# 여기서부터 출력
tab1, tab2 = st.tabs(["Summary", "Short Selling"])

with tab1:
    st.markdown(f"# {compName} ({stockcd})")

    st.markdown(f"자본금: {equity:,.0f}<br>직전 4분기 당기순익: {profit:,.0f}<br>ROE: {profit/equity:,.1%}", unsafe_allow_html=True)

    # st.write(stock.get_market_cap(day1wkago, today, stockcd))

    # mktcap = stock.get_market_cap(day1wkago, today, stockcd)['시가총액'].tail(1).values[0]
    # numstk = stock.get_market_cap(day1wkago, today, stockcd)['상장주식수'].tail(1).values[0]

    mktcap = get_market_cap(today, stockcd)['시가총액'].tail(1).values[0]
    numstk = get_market_cap(today, stockcd)['상장주식수'].tail(1).values[0]

    st.write(f"시가총액: {mktcap:,.0f} 원")
    st.write(f"주식수: {numstk:,.0f}")
    st.write(f"주당자산: {assets/numstk:,.0f} 원")
    st.write(f"주당이익: {profit/numstk:,.0f} 원")
    st.write(f"주가: {mktcap/numstk:,.0f} 원")
    st.write(f"PER: {mktcap/profit:,.2f}")
    st.write(f"PBR: {mktcap/assets:,.2f}")
    st.write(f"ROA: {profit/assets:,.1%}")
    st.write(f"GP/A: {grossprofit/assets:,.1%}")
    st.write(f"FCF/Equity: {fcf/equity:,.1%}")

    # 부채비율
    # 현금및현금성자산비율
    # 영업이익률
    # FCF = OCF - CAPEX
    # OCF = ifrs-full_CashFlowsFromUsedInOperatingActivities(영업활동을 통해 유입된 현금흐름)
    # CAPEX = ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities(유형자산의 취득) + ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities(무형자산의 취득)

    # FCF = CFO - CFI
    # CFO: 영업활동현금흐름
    # CFI: 투자활동현금흐름

    # asset 금액을 직전 4분기 평균이나 최근분기와 작년동기와의 평균값으로 사용
    # 배당수익률 추가
    # SKC 와 같이 유형자산의 취득, 무형자산의 취득 항목이 별도로 있지 않고 개별항목으로 재무제표 작성되어있는 회사들이 있어서 별도 처리 필요

with tab2:
    # 공매도(short sell) 추세를 표시해볼까?

    short_yr = st.selectbox("Select year", [1,2,3,4,5])

    e_date = today
    s_date = (datetime.strptime(e_date, '%Y%m%d') - relativedelta(years=short_yr)).strftime('%Y%m%d')

    df_short = stock.get_shorting_balance_by_date(s_date, e_date, stockcd).reset_index()
    df_price = stock.get_market_ohlcv(s_date, e_date, stockcd).reset_index()

    df_short = pd.merge(df_short, df_price, on="날짜")

    # st.dataframe(df_short)
    fig_short = make_subplots(specs=[[{"secondary_y": True}]])

    fig_short.add_trace(
        go.Scatter(x=df_short['날짜'], y=df_short['비중'], name="공매도비중"),
        secondary_y=False,
    )

    fig_short.add_trace(
        go.Scatter(x=df_short['날짜'], y=df_short['종가'], name="일자별종가"),
        secondary_y=True,
    )
    st.plotly_chart(fig_short)