import streamlit as st
import feedparser
import urllib.parse
from datetime import datetime, timedelta

# --- 1. 설정 및 디자인 ---
st.set_page_config(page_title="News Today", layout="wide")
st.markdown("<style>.stApp { background-color: #f8f9fa; }</style>", unsafe_allow_html=True)

CATEGORIES = {
    "관계사": {
        "icon": "🏢", 
        "keywords": ["대성계전", "대성산업", "대성물류건설", "대성에너지", "대성홀딩스", "대성창투", "MCM"],
        "must_have": ["대성"] 
    },
    "도시가스": {"icon": "🔥", "keywords": ["서울도시가스", "도시가스", "SCNG", "GRM", "GRES", "SCGS", "SCGG", "SCGLAB", "가스앱", "에스씨지", "에너지톡"]},
    "정책 · 규제": {"icon": "⚖️", "keywords": ["산업부 정책", "전기요금", "가스요금", "탄소정책", "공정위", "금융위", "국회 입법", "내부거래", "부당거래", "일감 몰아주기"]},
    "에너지": {"icon": "⚡", "keywords": ["한전", "스마트그리드", "전력관리", "전력시장", "전력망", "ESS", "탄소", "전력 디지털", "에너지 관리 시스템", "태양광", "전기차 충전"]},
    "IT": {"icon": "💻", "keywords": ["AI", "IT", "로봇", "메타버스", "빅테크", "사물인터넷", "챗GPT", "플랫폼", "iot", "o2o", "SAAS", "데이터 분석", "최적화", "예측"]},
    "인적 네트워크": {
        "icon": "🤝", 
        "keywords": [
            "귀뚜라미", "교원", "대신증권", "동화약품", "미래앤서해에너지", 
            "성호전자", "삼천리", "예스코", "카카오", "아주호텔앤리조트", 
            "참프레", "쏘카", "씨앤시티", "JB", "참빛그룹", "중앙에너비스", "한유", "GS 엠비즈",
            "최성환", "장선하", "장동하", "양홍석", "김영진", "박성재", "이은선", "구본혁", "윤동희", "문윤회", "김재윤", "박재욱", "김영석", "이호웅", "한승희", "박원석"
        ]
    }
}

if 'global_seen_titles' not in st.session_state:
    st.session_state.global_seen_titles = set()

# --- 2. 뉴스 수집 함수 ---
def fetch_news(cat_name, keywords):
    now = datetime.now()
    today_08 = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # 인적 네트워크는 데이터 확보를 위해 3일치 검색
    days_to_search = 3 if cat_name == "인적 네트워크" else 1
    yesterday_08 = today_08 - timedelta(days=days_to_search)
    
    query = " OR ".join(keywords)
    encoded_query = urllib.parse.quote(f"({query}) after:{yesterday_08.strftime('%Y-%m-%d')} before:{today_08.strftime('%Y-%m-%d')}")
    
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko")
    news_items = []

    for e in feed.entries:
        try:
            pub_time = datetime(*e.published_parsed[:6]) + timedelta(hours=9)
            if yesterday_08 <= pub_time < today_08:
                full_title = e.title.rsplit(' - ', 1)[0].strip()
                clean_title = "".join(full_title.split())
                
                if cat_name != "관계사":
                    if any(word in full_title for word in CATEGORIES["관계사"]["must_have"]):
                        continue 

                if clean_title not in st.session_state.global_seen_titles:
                    news_items.append({"title": full_title, "link": e.link, "source": e.source.get('title', '언론사'), "time": pub_time})
                    st.session_state.global_seen_titles.add(clean_title)
        except: continue
    return sorted(news_items, key=lambda x: x['time'], reverse=True)

# --- 3. 화면 출력 ---
st.title("📰 News Today")
st.markdown(f"### 📅 {datetime.now().strftime('%Y년 %m월 %d일')} ({['월','화','수','목','금','토','일'][datetime.now().weekday()]}요일)")
st.write("---")

# 주요 경제 지표 섹션 (추가된 부분)
st.markdown("#### 📈 주요 경제 지표 (실시간 링크)")
m_cols = st.columns(4)
market_links = {
    "📉 KOSPI": "https://finance.naver.com/sise/sise_index.nhn?code=KOSPI",
    "🇺🇸 S&P 500": "https://finance.naver.com/world/sise.naver?symbol=SPI@SPX",
    "🛢️ 국제유가(WTI)": "https://finance.naver.com/marketindex/worldDailyQuote.naver?marketindexCd=OIL_CL&fdtc=2",
    "💵 원/달러 환율": "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
}

for i, (name, url) in enumerate(market_links.items()):
    with m_cols[i]:
        st.link_button(name, url, use_container_width=True)

st.write("")

# 카테고리별 출력
st.session_state.global_seen_titles = set()
display_order = [["도시가스", "정책 · 규제", "에너지"], ["IT", "인적 네트워크", "관계사"]]

# 관계사 선행 수집
pre_fetched = {"관계사": fetch_news("관계사", CATEGORIES["관계사"]["keywords"])}

for row in display_order:
    cols = st.columns(3)
    for i, cat_name in enumerate(row):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"#### {CATEGORIES[cat_name]['icon']} {cat_name}")
                with st.spinner(f'{cat_name} 수집 중...'):
                    res = pre_fetched["관계사"] if cat_name == "관계사" else fetch_news(cat_name, CATEGORIES[cat_name]['keywords'])
                
                with st.expander(f"📌 총 {len(res)}건의 소식", expanded=False):
                    if res:
                        for news in res:
                            st.markdown(f"**· [{news['title']}]({news['link']})**")
                            st.caption(f"출처: {news['source']} | {news['time'].strftime('%H:%M')}")
                            st.write("")
                    else:
                        st.info("기사가 없습니다.")