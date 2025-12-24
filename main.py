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
# 0. 전역 설정 (학교별 연구 조건 및 테마 컬러)
# -----------------------------------------------------------------------------
SCHOOLS_CONFIG = {
    "송도고": {"ec": 1.0, "color": "#1f77b4", "desc": "대조군 (저농도 양액)"},
    "하늘고": {"ec": 2.0, "color": "#2ca02c", "desc": "실험군 (가설상 최적 농도)"},
    "아라고": {"ec": 4.0, "color": "#ff7f0e", "desc": "실험군 (고농도 양액)"},
    "동산고": {"ec": 8.0, "color": "#d62728", "desc": "실험군 (과농도 스트레스)"}
}

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 폰트 스타일
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구 대시보드",
    page_icon="🌱",
    layout="wide"
)

# Streamlit UI 한글 폰트 적용
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}
.main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 1rem; }
.sub-text { color: #4B5563; font-size: 1.1rem; }
[data-testid="stMetricValue"] { font-family: 'Noto Sans KR', sans-serif; }
</style>
""", unsafe_allow_html=True)

def get_font_dict():
    return dict(family="Noto Sans KR, Malgun Gothic, sans-serif", size=12)

# -----------------------------------------------------------------------------
# 2. 데이터 로딩 시스템 (NFC/NFD 정규화 지원)
# -----------------------------------------------------------------------------
@st.cache_data
def load_all_data():
    base_path = Path("data")
    if not base_path.exists():
        return None, None

    # 파일 매칭 유틸리티 (NFC 정규화 비교)
    def get_safe_path(keyword, ext):
        target = unicodedata.normalize("NFC", keyword)
        for p in base_path.iterdir():
            if p.suffix == ext and target in unicodedata.normalize("NFC", p.name):
                return p
        return None

    env_list = []
    growth_list = []

    # 1) 환경 데이터 로드
    for name in SCHOOLS_CONFIG.keys():
        path = get_safe_path(f"{name}_환경데이터", ".csv")
        if path:
            try:
                df = pd.read_csv(path)
                df.columns = [c.strip().lower() for c in df.columns]
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'], errors='coerce')
                df['school'] = name
                df['target_ec'] = SCHOOLS_CONFIG[name]['ec']
                env_list.append(df)
            except Exception as e:
                st.error(f"{name} 환경 데이터 처리 중 오류: {e}")

    # 2) 생육 결과 데이터 로드 (XLSX)
    growth_path = get_safe_path("4개교_생육결과데이터", ".xlsx")
    if growth_path:
        try:
            xls = pd.ExcelFile(growth_path)
            for sheet in xls.sheet_names:
                sheet_nfc = unicodedata.normalize("NFC", sheet)
                matched = next((s for s in SCHOOLS_CONFIG if s in sheet_nfc), None)
                if matched:
                    df_s = pd.read_excel(xls, sheet_name=sheet)
                    df_s['school'] = matched
                    df_s['target_ec'] = SCHOOLS_CONFIG[matched]['ec']
                    growth_list.append(df_s)
        except Exception as e:
            st.error(f"생육 데이터 로드 실패: {e}")

    full_env = pd.concat(env_list, ignore_index=True) if env_list else pd.DataFrame()
    full_growth = pd.concat(growth_list, ignore_index=True) if growth_list else pd.DataFrame()
    
    return full_env, full_growth

# -----------------------------------------------------------------------------
# 3. 메인 애플리케이션 구조
# -----------------------------------------------------------------------------
def main():
    st.markdown('<p class="main-title">🌱 극지식물 최적 EC 농도 연구 대시보드</p>', unsafe_allow_html=True)
    
    with st.spinner("연구 데이터를 분석하는 중입니다..."):
        env_df, growth_df = load_all_data()
        time.sleep(0.5)

    if env_df.empty or growth_df.empty:
        st.error("데이터 파일을 찾을 수 없습니다. 'data/' 폴더 내의 파일명과 형식을 확인해주세요.")
        return

    # 사이드바 필터
    st.sidebar.header("📋 데이터 필터링")
    school_options = ["전체"] + sorted(list(growth_df['school'].unique()))
    sel_school = st.sidebar.selectbox("대상 학교 선택", school_options)

    # 데이터 필터링 적용
    f_env = env_df if sel_school == "전체" else env_df[env_df['school'] == sel_school]
    f_growth = growth_df if sel_school == "전체" else growth_df[growth_df['school'] == sel_school]

    tab1, tab2, tab3 = st.tabs(["📖 실험 개요 및 가설", "🌡️ 실시간 환경 분석", "📊 생육 결과 연구"])

    # --- Tab 1: 실험 개요 ---
    with tab1:
        st.subheader("🔬 연구 배경 및 목적")
        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            st.markdown(f"""
            **1. 연구의 필요성** 급격한 기후 변화로 인해 극지 식물(Deschampsia antarctica 등)의 자생지가 위협받고 있습니다. 본 연구는 이러한 식물들을 인공 환경에서 보존하고 대량 증식하기 위한 **정밀 농업 기술(Smart Farming)**의 기초 데이터를 수집하는 데 목적이 있습니다.

            **2. EC(전기전도도) 농도 변인 설정** 식물은 양액의 이온 농도에 따라 수분 흡수 효율이 달라집니다. 본 실험은 **{', '.join([str(v['ec']) for v in SCHOOLS_CONFIG.values()])} dS/m**의 4가지 처리구를 설정하여, 극지 식물에 가장 적합한 '생육 골든존'을 탐색합니다.

            **3. 핵심 가설** > "극지 식물은 일반 관상식물 대비 저온 적응성이 높으므로, 중간 농도인 **EC 2.0(하늘고)** 처리구에서 생중량 및 지상부 길이 성장이 가장 우수할 것이다."
            """)
        with c2:
            st.info(f"""
            **🗓️ 연구 수행 정보**
            - **공동 참여:** 송도고, 하늘고, 아라고, 동산고
            - **통제 변인:** 온도(15~18℃), 광원(LED 12h), 배지 종류
            - **데이터 규모:** 총 {len(growth_df)}개체 분석 완료
            """)

        st.divider()
        st.subheader("💡 연구 핵심 지표 (KPI)")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("총 분석 개체수", f"{len(growth_df)} 장")
        k2.metric("평균 재배 온도", f"{env_df['temperature'].mean():.1f} ℃")
        k3.metric("평균 습도", f"{env_df['humidity'].mean():.1f} %")
        best_s = growth_df.groupby('school')['생중량(g)'].mean().idxmax()
        k4.metric("최적 성과 학교", best_s, f"EC {SCHOOLS_CONFIG[best_s]['ec']}")

        st.divider()
        st.subheader("🏫 참여 학교별 처리 조건")
        cond_df = pd.DataFrame([{"학교명": k, "목표 EC": v['ec'], "특이사항": v['desc']} for k, v in SCHOOLS_CONFIG.items()])
        st.table(cond_df)

    # --- Tab 2: 환경 데이터 ---
    with tab2:
        st.subheader("🌡️ 수집 환경 모니터링 분석")
        
        # 2x2 서브플롯
        e_mean = env_df.groupby('school').mean(numeric_only=True).reset_index()
        fig_e = make_subplots(rows=2, cols=2, subplot_titles=("평균 온도 (℃)", "평균 습도 (%)", "평균 pH", "목표 vs 실측 EC"))
        
        fig_e.add_trace(go.Bar(x=e_mean['school'], y=e_mean['temperature'], name="온도", marker_color='#fb8500'), 1, 1)
        fig_e.add_trace(go.Bar(x=e_mean['school'], y=e_mean['humidity'], name="습도", marker_color='#219ebc'), 1, 2)
        fig_e.add_trace(go.Bar(x=e_mean['school'], y=e_mean['ph'], name="pH", marker_color='#8ecae6'), 2, 1)
        fig_e.add_trace(go.Bar(x=e_mean['school'], y=e_mean['target_ec'], name="목표 EC", marker_color='#023047', opacity=0.4), 2, 2)
        fig_e.add_trace(go.Bar(x=e_mean['school'], y=e_mean['ec'], name="실측 EC", marker_color='#023047'), 2, 2)

        fig_e.update_layout(height=600, font=get_font_dict(), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

        st.subheader(f"📈 {sel_school} 상세 시계열 추이")
        if not f_env.empty:
            c_env = px.line(f_env, x='time', y=['temperature', 'humidity', 'ec'], color='school', title="시간대별 환경 변화")
            c_env.update_layout(font=get_font_dict())
            st.plotly_chart(c_env, use_container_width=True)
            
            with st.expander("📥 환경 원본 데이터 확인"):
                st.write(f_env)
                st.download_button("CSV 다운로드", f_env.to_csv(index=False).encode('utf-8-sig'), "env_data.csv", "text/csv")

    # --- Tab 3: 생육 결과 ---
    with tab3:
        st.subheader("📊 EC 농도에 따른 생육 성과 분석")
        
        # 성과 하이라이트
        avg_w = growth_df.groupby('school')['생중량(g)'].mean()
        best_school = avg_w.idxmax()
        st.success(f"🎊 분석 결과: **{best_school} (EC {SCHOOLS_CONFIG[best_school]['ec']})** 조건에서 평균 생중량 {avg_w.max():.2f}g으로 가장 뛰어난 성장을 보였습니다.")

        # 2x2 생육 지표
        g_mean = growth_df.groupby('school').mean(numeric_only=True).reindex(SCHOOLS_CONFIG.keys()).reset_index()
        fig_g = make_subplots(rows=2, cols=2, subplot_titles=("평균 생중량 (g)", "평균 잎 수 (장)", "평균 지상부 길이 (mm)", "평균 지하부 길이 (mm)"))
        
        colors = [v['color'] for v in SCHOOLS_CONFIG.values()]
        fig_g.add_trace(go.Bar(x=g_mean['school'], y=g_mean['생중량(g)'], marker_color=colors), 1, 1)
        fig_g.add_trace(go.Bar(x=g_mean['school'], y=g_mean['잎 수(장)'], marker_color=colors), 1, 2)
        fig_g.add_trace(go.Bar(x=g_mean['school'], y=g_mean['지상부 길이(mm)'], marker_color=colors), 2, 1)
        fig_g.add_trace(go.Bar(x=g_mean['school'], y=g_mean['지하부길이(mm)'], marker_color=colors), 2, 2)
        
        fig_g.update_layout(height=700, font=get_font_dict(), showlegend=False)
        st.plotly_chart(fig_g, use_container_width=True)

        # 분포 및 상관관계
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**🌱 학교별 생중량 분포 (Violin)**")
            fig_v = px.violin(growth_df, x='school', y='생중량(g)', color='school', box=True, color_discrete_map={k: v['color'] for k, v in SCHOOLS_CONFIG.items()})
            fig_v.update_layout(font=get_font_dict(), showlegend=False)
            st.plotly_chart(fig_v, use_container_width=True)
        with sc2:
            st.markdown("**🔗 주요 생육 지표 상관관계 (지상부 vs 생중량)**")
            fig_s = px.scatter(growth_df, x='지상부 길이(mm)', y='생중량(g)', color='school', trendline="ols", color_discrete_map={k: v['color'] for k, v in SCHOOLS_CONFIG.items()})
            fig_s.update_layout(font=get_font_dict())
            st.plotly_chart(fig_s, use_container_width=True)

        with st.expander("📥 생육 결과 데이터 다운로드 (XLSX)"):
            st.write(f_growth)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                f_growth.to_excel(writer, index=False)
            st.download_button("Excel 다운로드", buf.getvalue(), "growth_result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
