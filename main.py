import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import unicodedata
from pathlib import Path
import io
import time

# -----------------------------------------------------------------------------
# 0. 전역 설정 (모던한 컬러 팔레트로 수정)
# -----------------------------------------------------------------------------
SCHOOLS_CONFIG = {
    "송도고": {"ec": 1.0, "color": "#94A3B8", "desc": "Control Group (저농도)"},
    "하늘고": {"ec": 2.0, "color": "#10B981", "desc": "Optimal Zone (가설)"}, # 최적 강조색
    "아라고": {"ec": 4.0, "color": "#0EA5E9", "desc": "High Concentration"},
    "동산고": {"ec": 8.0, "color": "#6366F1", "desc": "Extreme Stress"}
}

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 UI 스타일 (고급스러운 다크 & 화이트 믹스)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="극지식물 연구 대시보드", page_icon="🌿", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Pretendard', sans-serif;
}
/* 메인 타이틀 스타일 */
.main-title { 
    font-size: 32px; font-weight: 700; color: #1E293B; 
    padding-bottom: 20px; border-bottom: 2px solid #F1F5F9; margin-bottom: 30px;
}
/* 카드 스타일링 */
[data-testid="stMetric"] {
    background-color: #F8FAFC; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0;
}
/* 탭 폰트 */
.stTabs [data-baseweb="tab-list"] button { font-size: 18px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

def get_font_dict():
    return dict(family="Pretendard, sans-serif", size=13, color="#475569")

# -----------------------------------------------------------------------------
# 2. 데이터 로딩 (NFC/NFD 대응)
# -----------------------------------------------------------------------------
@st.cache_data
def load_all_data():
    base_path = Path("data")
    if not base_path.exists(): return None, None

    def get_safe_path(keyword, ext):
        target = unicodedata.normalize("NFC", keyword)
        for p in base_path.iterdir():
            if p.suffix == ext and target in unicodedata.normalize("NFC", p.name):
                return p
        return None

    env_list, growth_list = [], []

    for name in SCHOOLS_CONFIG.keys():
        path = get_safe_path(f"{name}_환경데이터", ".csv")
        if path:
            df = pd.read_csv(path)
            df.columns = [c.strip().lower() for c in df.columns]
            if 'time' in df.columns: df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df['school'], df['target_ec'] = name, SCHOOLS_CONFIG[name]['ec']
            env_list.append(df)

    growth_path = get_safe_path("4개교_생육결과데이터", ".xlsx")
    if growth_path:
        xls = pd.ExcelFile(growth_path)
        for sheet in xls.sheet_names:
            sheet_nfc = unicodedata.normalize("NFC", sheet)
            matched = next((s for s in SCHOOLS_CONFIG if s in sheet_nfc), None)
            if matched:
                df_s = pd.read_excel(xls, sheet_name=sheet)
                df_s['school'], df_s['target_ec'] = matched, SCHOOLS_CONFIG[matched]['ec']
                growth_list.append(df_s)

    return pd.concat(env_list, ignore_index=True), pd.concat(growth_list, ignore_index=True)

# -----------------------------------------------------------------------------
# 3. 애플리케이션 실행
# -----------------------------------------------------------------------------
def main():
    st.markdown('<div class="main-title">🌿 극지식물 최적 양액 농도(EC) 연구</div>', unsafe_allow_html=True)
    
    env_df, growth_df = load_all_data()
    if env_df is None or growth_df.empty:
        st.error("데이터 로드 실패")
        return

    # 사이드바 (차분한 색상)
    st.sidebar.markdown("### 🛠 분석 필터")
    sel_school = st.sidebar.selectbox("학교별 상세 보기", ["전체"] + list(SCHOOLS_CONFIG.keys()))
    
    f_env = env_df if sel_school == "전체" else env_df[env_df['school'] == sel_school]
    f_growth = growth_df if sel_school == "전체" else growth_df[growth_df['school'] == sel_school]

    tab1, tab2, tab3 = st.tabs(["📖 연구 개요", "🌡️ 환경 분석", "📊 생육 성과"])

    # --- Tab 1: 개요 (고급스러운 레이아웃) ---
    with tab1:
        c1, c2 = st.columns([1.3, 0.7])
        with c1:
            st.subheader("📌 연구 프로젝트 배경")
            st.markdown("""
            본 대시보드는 **극지 식물의 스마트 재배 시스템** 구축을 위해 수집된 데이터를 시각화합니다. 
            식물의 대사 활동을 극대화하는 **최적의 EC(Electrical Conductivity)** 농도를 찾는 것이 본 연구의 핵심 과제입니다.
            """)
            
            st.markdown("#### 🧪 주요 처리구 설계")
            summary_cols = st.columns(4)
            for i, (name, info) in enumerate(SCHOOLS_CONFIG.items()):
                with summary_cols[i]:
                    st.markdown(f"""
                    <div style="background-color:{info['color']}22; border-left:5px solid {info['color']}; padding:10px; border-radius:5px;">
                        <strong style="color:{info['color']}">{name}</strong><br>
                        <small>EC {info['ec']} dS/m</small>
                    </div>
                    """, unsafe_allow_html=True)
        with c2:
            st.subheader("💡 Key Metrics")
            st.metric("총 분석 샘플", f"{len(growth_df)} 개체")
            st.metric("최적 후보군", "하늘고", "EC 2.0")

    # --- Tab 2: 환경 (Plotly 컬러 테마 적용) ---
    with tab2:
        st.subheader("🌡️ 수집 환경 통계")
        e_mean = env_df.groupby('school').mean(numeric_only=True).reset_index()
        
        # 차트 색상 리스트 생성
        chart_colors = [SCHOOLS_CONFIG[s]['color'] for s in e_mean['school']]

        fig_env = make_subplots(rows=1, cols=3, subplot_titles=("평균 온도", "평균 습도", "EC 정밀도"))
        fig_env.add_trace(go.Bar(x=e_mean['school'], y=e_mean['temperature'], marker_color=chart_colors), 1, 1)
        fig_env.add_trace(go.Bar(x=e_mean['school'], y=e_mean['humidity'], marker_color=chart_colors), 1, 2)
        fig_env.add_trace(go.Scatter(x=e_mean['school'], y=e_mean['ec'], mode='markers+lines', line=dict(color='#334155')), 1, 3)
        
        fig_env.update_layout(height=400, font=get_font_dict(), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_env, use_container_width=True)

    # --- Tab 3: 생육 (최적값 강조 차트) ---
    with tab3:
        st.subheader("📊 생육 데이터 분석")
        
        g_mean = growth_df.groupby('school').mean(numeric_only=True).reindex(SCHOOLS_CONFIG.keys()).reset_index()
        chart_colors_g = [SCHOOLS_CONFIG[s]['color'] for s in g_mean['school']]

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**1. 평균 생중량 (g) - 성장의 핵심 지표**")
            fig_g1 = px.bar(g_mean, x='school', y='생중량(g)', color='school', color_discrete_map={k:v['color'] for k,v in SCHOOLS_CONFIG.items()})
            fig_g1.update_layout(showlegend=False, font=get_font_dict(), margin=dict(t=10))
            st.plotly_chart(fig_g1, use_container_width=True)
            
        with col_g2:
            st.markdown("**2. 지상부 길이 대비 생중량 상관관계**")
            fig_g2 = px.scatter(growth_df, x='지상부 길이(mm)', y='생중량(g)', color='school', trendline="ols",
                               color_discrete_map={k:v['color'] for k,v in SCHOOLS_CONFIG.items()})
            fig_g2.update_layout(font=get_font_dict(), margin=dict(t=10))
            st.plotly_chart(fig_g2, use_container_width=True)

        st.info("💡 **Tip:** 에메랄드 색상으로 표시된 **하늘고(EC 2.0)** 데이터가 전반적으로 우수한 생장 곡선을 보이고 있습니다.")

if __name__ == "__main__":
    main()
