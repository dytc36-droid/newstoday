import streamlit as st
import feedparser
import urllib.parse
from datetime import datetime, timedelta

# --- 1. 설정 및 디자인 ---
st.set_page_config(page_title="News Today", layout="wide")
st.markdown("<style>.stApp { background-color: #f8f9fa; }</style>", unsafe_allow_html=True)

CATEGORIES = {
    "도시가스": {"icon": "🔥", "keywords": ["서울도시가스", "도시가스", "SCNG", "GRM", "GRES", "SCGS", "SCGG", "SCGLAB", "가스앱", "에스씨지", "에너지톡"]},
    "정책 · 규제": {"icon": "⚖️", "keywords": ["산업부 정책", "전기요금", "가스요금", "탄소정책", "공정위", "금융위", "국회 입법", "내부거래", "부당거래", "일감 몰아주기"]},
    "에너지": {"icon": "⚡", "keywords": ["한전", "스마트그리드", "전력관리", "전력시장", "전력망", "ESS", "탄소", "전력 디지털", "에너지 관리 시스템", "태양광", "전기차 충전"]},
    "IT": {"icon": "💻", "keywords": ["AI", "IT", "로봇", "메타버스", "빅테크", "사물인터넷", "챗GPT", "플랫폼", "iot", "o2o", "SAAS", "데이터 분석", "최적화", "예측"]},
    "인적 네트워크": {"icon": "🤝", "keywords": ["귀뚜라미", "교원", "대신증권", "동화약품", "미래앤서해에너지", "성호전자", "삼천리", "예스코", "카카오", "아주호텔앤리조트", "참프레", "쏘카", "씨앤시티", "JB", "참빛그룹", "중앙에너비스", "한유", "GS 엠비즈", "최성환", "장선하", "장동하", "양홍석", "김영진", "박성재", "이은선", "구본혁", "윤동희", "문윤회", "김재윤", "박재욱", "김영석", "이호웅", "한승희", "박원석"]},
    "관계사": {
        "icon": "🏢", 
        "keywords": ["대성계전", "대성산업", "대성물류건설", "대성에너지", "대성홀딩스", "대성창투", "MCM"],
        "must_have": ["대성"]
    }
}

# --- 2. 세션 상태 초기화 (데이터 유지용) ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = {}
if 'global_seen' not in st.session_state:
    st.session_state.global_seen = set()

# --- 3. 뉴스 수집 함수 ---
def fetch_news(cat_name, keywords):
    now = datetime.now()
    today_08 = now.replace(hour=8, minute=0, second=0, microsecond=0)
    days = 3 if cat_name == "인적 네트워크" else 1
    yesterday_08 = today_08 - timedelta(days=days)
    
    query = " OR ".join(keywords)
    encoded_query = urllib.parse.quote(f"({query}) after:{yesterday_08.strftime('%Y-%m-%d')} before:{today_08.strftime('%Y-%m-%d')}")
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko")
    
    items = []
    for e in feed.entries:
        try:
            pub_time = datetime(*e.published_parsed[:6]) + timedelta(hours=9)
            if yesterday_08 <= pub_time < today_08:
                full_title = e.title.rsplit(' - ', 1)[0].strip()
                clean_title = "".join(full_title.split())
                
                if cat_name != "관계사" and any(word in full_title for word in CATEGORIES["관계사"]["must_have"]):
                    continue
                
                if clean_title not in st.session_state.global_seen:
                    items.append({"title": full_title, "link": e.link, "source": e.source.get('title', '언론사'), "time": pub_time})
                    st.session_state.global_seen.add(clean_title)
        except: continue
    return sorted(items, key=lambda x: x['time'], reverse=True)

# --- 4. 화면 구성 ---
st.title("📰 News Today")
st.markdown(f"### 📅 {datetime.now().strftime('%Y년 %m월 %d일')}")

# 사이드바: 관리자 도구
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_pw = st.text_input("편집 비밀번호를 입력하세요", type="password")
    is_admin = (admin_pw == "1234") # 실제 비밀번호로 변경하세요

    if st.button("🔄 전체 뉴스 새로고침"):
        st.session_state.news_data = {}
        st.session_state.global_seen = set()
        # 관계사 우선 수집
        st.session_state.news_data["관계사"] = fetch_news("관계사", CATEGORIES["관계사"]["keywords"])
        for cat in CATEGORIES:
            if cat != "관계사":
                st.session_state.news_data[cat] = fetch_news(cat, CATEGORIES[cat]['keywords'])
        st.rerun()

# --- 5. 뉴스 카테고리 출력 (편집 기능 포함) ---
display_order = [["도시가스", "정책 · 규제", "에너지"], ["IT", "인적 네트워크", "관계사"]]

for row in display_order:
    cols = st.columns(3)
    for i, cat_name in enumerate(row):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"#### {CATEGORIES[cat_name]['icon']} {cat_name}")
                
                if cat_name not in st.session_state.news_data:
                    st.info("새로고침을 눌러주세요.")
                    continue
                
                current_news = st.session_state.news_data[cat_name]
                with st.expander(f"📌 총 {len(current_news)}건", expanded=False):
                    # 기사 리스트 편집 로직
                    for idx, news in enumerate(current_news):
                        col_text, col_del = st.columns([0.85, 0.15])
                        with col_text:
                            st.markdown(f"**· [{news['title']}]({news['link']})**")
                            st.caption(f"{news['source']} | {news['time'].strftime('%H:%M')}")
                        with col_del:
                            # 관리자 비밀번호가 맞을 때만 삭제 버튼 표시
                            if is_admin:
                                if st.button("🗑️", key=f"del_{cat_name}_{idx}"):
                                    st.session_state.news_data[cat_name].pop(idx)
                                    st.rerun()
                        st.write("")