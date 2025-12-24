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
# 1. 페이지 설정 및 스타일 (폰트 깨짐 방지)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    page_icon="🌱",
    layout="wide"
)

# 한글 폰트 적용 (Streamlit UI)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
/* 메트릭 값 폰트 조정 */
[data-testid="stMetricValue"] {
    font-family: 'Noto Sans KR', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# Plotly 차트 공통 폰트 설정
def get_font_dict():
    return dict(family="Noto Sans KR, Malgun Gothic, sans-serif")

# -----------------------------------------------------------------------------
# 2. 데이터 로딩 함수 (파일명 정규화 및 캐싱)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """
    데이터 폴더의 파일을 NFC/NFD 정규화를 통해 안전하게 찾고 로드합니다.
    """
    base_path = Path("data")
    
    # 데이터 폴더 확인
    if not base_path.exists():
        st.error(f"❌ 'data' 폴더를 찾을 수 없습니다. 현재 경로: {Path.cwd()}")
        return None, None

    # 파일 매칭 헬퍼 함수
    def find_file_in_dir(directory, keyword, extension):
        target_nfc = unicodedata.normalize("NFC", keyword)
        
        for file_path in directory.iterdir():
            if file_path.suffix != extension:
                continue
            
            # 파일명을 NFC로 정규화하여 비교
            file_name_nfc = unicodedata.normalize("NFC", file_path.name)
            
            if target_nfc in file_name_nfc:
                return file_path
        return None

    env_data = {}
    growth_df_list = []
    
    # 학교별 설정 (매핑 정보)
    schools = {
        "송도고": {"ec": 1.0, "color": "#1f77b4"},
        "하늘고": {"ec": 2.0, "color": "#2ca02c"}, # 최적
        "아라고": {"ec": 4.0, "color": "#ff7f0e"},
        "동산고": {"ec": 8.0, "color": "#d62728"}
    }

    # 1) 환경 데이터 로드 (CSV)
    for school_name in schools.keys():
        file_path = find_file_in_dir(base_path, f"{school_name}_환경데이터", ".csv")
        
        if file_path:
            try:
                df = pd.read_csv(file_path)
                # 컬럼명 공백 제거 및 소문자화 (안전장치)
                df.columns = [c.strip().lower() for c in df.columns]
                
                # 날짜 변환 (에러 방지)
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'], errors='coerce')
                
                df['school'] = school_name
                df['target_ec'] = schools[school_name]['ec']
                env_data[school_name] = df
            except Exception as e:
                st.error(f"❌ {school_name} 환경 데이터 로딩 실패: {e}")
        else:
            st.warning(f"⚠️ {school_name} 환경 데이터 파일을 찾을 수 없습니다.")

    # 2) 생육 결과 데이터 로드 (XLSX)
    growth_file = find_file_in_dir(base_path, "4개교_생육결과데이터", ".xlsx")
    
    if growth_file:
        try:
            # 시트 이름 하드코딩 없이 동적 로드
            xls = pd.ExcelFile(growth_file)
            for sheet_name in xls.sheet_names:
                # 시트 이름 정규화하여 학교명 매칭
                sheet_nfc = unicodedata.normalize("NFC", sheet_name)
                matched_school = next((s for s in schools if s in sheet_nfc), None)
                
                if matched_school:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet_name)
                    df_sheet['school'] = matched_school
                    df_sheet['target_ec'] = schools[matched_school]['ec']
                    growth_df_list.append(df_sheet)
        except Exception as e:
            st.error(f"❌ 생육 결과 데이터 로딩 실패: {e}")
    else:
        st.error("❌ '4개교_생육결과데이터.xlsx' 파일을 찾을 수 없습니다.")

    # 생육 데이터 병합
    growth_data = pd.concat(growth_df_list, ignore_index=True) if growth_df_list else pd.DataFrame()

    # 환경 데이터 병합
    env_data_combined = pd.concat(env_data.values(), ignore_index=True) if env_data else pd.DataFrame()
    
    return env_data_combined, growth_data

# -----------------------------------------------------------------------------
# 3. 앱 레이아웃 및 로직
# -----------------------------------------------------------------------------
def main():
    st.title("🌱 극지식물 최적 EC 농도 연구 대시보드")
    
    # 데이터 로딩 (스피너 적용)
    with st.spinner("데이터를 불러오고 분석 중입니다..."):
        env_df, growth_df = load_data()
        time.sleep(0.5) # UX를 위해 아주 짧은 대기

    if env_df.empty or growth_df.empty:
        st.warning("데이터가 로드되지 않았습니다. data 폴더와 파일명을 확인해주세요.")
        return

    # 사이드바 설정
    st.sidebar.header("🔍 필터 설정")
    school_list = ["전체"] + sorted(list(growth_df['school'].unique()))
    selected_school = st.sidebar.selectbox("학교 선택", school_list)

    # 필터링 로직
    if selected_school != "전체":
        filtered_env = env_df[env_df['school'] == selected_school]
        filtered_growth = growth_df[growth_df['school'] == selected_school]
    else:
        filtered_env = env_df
        filtered_growth = growth_df

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

    # --- Tab 1: 실험 개요 ---
    with tab1:
        st.header("연구 배경 및 조건")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            ### 📌 연구 목적
            **극지 식물의 스마트팜 재배를 위한 최적의 양액 농도(EC) 규명**
            
            - **대상:** 극지 식물 (Antarctic Flora Model)
            - **변인:** EC 농도 (1.0, 2.0, 4.0, 8.0 dS/m)
            - **가설:** EC 2.0 수준에서 생육 활성도가 가장 높을 것이다.
            """)
        
        with col2:
            st.markdown("### 🏫 학교별 EC 조건")
            # 조건 요약 테이블 생성
            summary = growth_df.groupby(['school', 'target_ec']).size().reset_index(name='개체수')
            summary.columns = ['학교명', '목표 EC (dS/m)', '실험 개체수']
            st.dataframe(summary, hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("🔎 주요 데이터 지표 (Global Metrics)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 실험 개체수", f"{len(growth_df):,}개")
        m2.metric("평균 재배 온도", f"{env_df['temperature'].mean():.1f} ℃")
        m3.metric("평균 습도", f"{env_df['humidity'].mean():.1f} %")
        # 최적 EC (생중량 기준)
        best_ec_row = growth_df.loc[growth_df['생중량(g)'].idxmax()]
        m4.metric("최고 생중량 기록 EC", f"EC {best_ec_row['target_ec']}", delta="Optimal")

    # --- Tab 2: 환경 데이터 ---
    with tab2:
        st.header("환경 데이터 분석")
        
        # 1. 환경 평균 비교 (2x2 Subplots)
        st.subheader("🏫 학교별 환경 평균 비교")
        env_mean = env_df.groupby('school')[['temperature', 'humidity', 'ph', 'ec', 'target_ec']].mean().reset_index()
        
        fig_env = make_subplots(
            rows=2, cols=2,
            subplot_titles=("평균 온도 (℃)", "평균 습도 (%)", "평균 pH", "목표 EC vs 실측 EC"),
            specs=[[{}, {}], [{}, {"secondary_y": False}]]
        )
        
        colors = px.colors.qualitative.Plotly

        # 온도
        fig_env.add_trace(go.Bar(x=env_mean['school'], y=env_mean['temperature'], name="온도", marker_color='#ff9f9b'), row=1, col=1)
        # 습도
        fig_env.add_trace(go.Bar(x=env_mean['school'], y=env_mean['humidity'], name="습도", marker_color='#a0ced9'), row=1, col=2)
        # pH
        fig_env.add_trace(go.Bar(x=env_mean['school'], y=env_mean['ph'], name="pH", marker_color='#c8a0d9'), row=2, col=1)
        
        # EC (이중 막대: 목표 vs 실측)
        fig_env.add_trace(go.Bar(x=env_mean['school'], y=env_mean['target_ec'], name="목표 EC", opacity=0.5, marker_color='gray'), row=2, col=2)
        fig_env.add_trace(go.Bar(x=env_mean['school'], y=env_mean['ec'], name="실측 EC", marker_color='green'), row=2, col=2)

        fig_env.update_layout(height=600, showlegend=True, font=get_font_dict())
        st.plotly_chart(fig_env, use_container_width=True)

        st.divider()

        # 2. 시계열 데이터
        st.subheader(f"📈 시계열 변화 ({selected_school})")
        
        # 시계열용 데이터 준비 (전체 선택 시 학교별로 색상 구분, 개별 선택 시 단일)
        ts_color = 'school' if selected_school == "전체" else None
        
        # 탭 안의 탭으로 구성하거나 컬럼으로 구성
        ts_tab1, ts_tab2, ts_tab3 = st.tabs(["온도 변화", "습도 변화", "EC 변화"])
        
        with ts_tab1:
            fig_ts_temp = px.line(filtered_env, x='time', y='temperature', color='school', title="시간별 온도 변화")
            fig_ts_temp.update_layout(font=get_font_dict())
            st.plotly_chart(fig_ts_temp, use_container_width=True)
            
        with ts_tab2:
            fig_ts_hum = px.line(filtered_env, x='time', y='humidity', color='school', title="시간별 습도 변화")
            fig_ts_hum.update_layout(font=get_font_dict())
            st.plotly_chart(fig_ts_hum, use_container_width=True)
            
        with ts_tab3:
            fig_ts_ec = px.line(filtered_env, x='time', y='ec', color='school', title="시간별 EC 변화")
            # 목표 EC 라인 추가 (개별 학교 선택 시에만 명확하게 보임)
            if selected_school != "전체":
                target_val = filtered_env['target_ec'].iloc[0]
                fig_ts_ec.add_hline(y=target_val, line_dash="dash", annotation_text="목표 EC", annotation_position="top right")
            fig_ts_ec.update_layout(font=get_font_dict())
            st.plotly_chart(fig_ts_ec, use_container_width=True)

        # 데이터 다운로드
        with st.expander("💾 환경 데이터 원본 및 다운로드"):
            st.dataframe(filtered_env)
            csv_buffer = filtered_env.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="CSV로 다운로드",
                data=csv_buffer,
                file_name="환경데이터_모음.csv",
                mime="text/csv"
            )

    # --- Tab 3: 생육 결과 ---
    with tab3:
        st.header("생육 결과 분석")
        
        # 핵심 결과 강조
        max_weight_school = growth_df.groupby('school')['생중량(g)'].mean().idxmax()
        max_weight_val = growth_df.groupby('school')['생중량(g)'].mean().max()
        
        st.info(f"🥇 분석 결과, **{max_weight_school}** (EC {schools[max_weight_school]['ec']}) 조건에서 평균 생중량이 **{max_weight_val:.2f}g**으로 가장 높게 나타났습니다.")

        # 1. 생육 지표 비교 (2x2)
        st.subheader("📊 EC 조건별 생육 지표 비교")
        
        # 집계
        growth_mean = growth_df.groupby('school')[['생중량(g)', '잎 수(장)', '지상부 길이(mm)', '지하부길이(mm)']].mean().reset_index()
        # EC 순서대로 정렬 (송도->하늘->아라->동산)
        sort_order = ["송도고", "하늘고", "아라고", "동산고"]
        growth_mean['school'] = pd.Categorical(growth_mean['school'], categories=sort_order, ordered=True)
        growth_mean = growth_mean.sort_values('school')

        fig_grow = make_subplots(
            rows=2, cols=2,
            subplot_titles=("평균 생중량 (g) ⭐", "평균 잎 수 (장)", "평균 지상부 길이 (mm)", "데이터 개체수 비교"),
            vertical_spacing=0.15
        )
        
        # 학교별 고정 컬러 매핑
        colors_map = [schools[s]['color'] for s in growth_mean['school']]

        # 생중량
        fig_grow.add_trace(go.Bar(x=growth_mean['school'], y=growth_mean['생중량(g)'], marker_color=colors_map, name="생중량"), row=1, col=1)
        # 잎 수
        fig_grow.add_trace(go.Bar(x=growth_mean['school'], y=growth_mean['잎 수(장)'], marker_color=colors_map, name="잎 수"), row=1, col=2)
        # 지상부 길이
        fig_grow.add_trace(go.Bar(x=growth_mean['school'], y=growth_mean['지상부 길이(mm)'], marker_color=colors_map, name="길이"), row=2, col=1)
        # 개체수 (Count)
        count_data = growth_df.groupby('school').size().reindex(sort_order).reset_index(name='count')
        fig_grow.add_trace(go.Bar(x=count_data['school'], y=count_data['count'], marker_color='gray', name="개체수"), row=2, col=2)

        fig_grow.update_layout(height=700, showlegend=False, font=get_font_dict())
        st.plotly_chart(fig_grow, use_container_width=True)

        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("🎻 생중량 분포 (Violin Plot)")
            fig_box = px.violin(
                growth_df, x="school", y="생중량(g)", color="school", 
                box=True, points="all",
                category_orders={"school": sort_order},
                color_discrete_map={k: v['color'] for k, v in schools.items()}
            )
            fig_box.update_layout(showlegend=False, font=get_font_dict())
            st.plotly_chart(fig_box, use_container_width=True)

        with col_b:
            st.subheader("🔗 상관관계 분석")
            # 탭으로 상관관계 선택
            corr_opt = st.radio("변수 선택", ["잎 수 vs 생중량", "지상부 길이 vs 생중량"], horizontal=True)
            
            x_val = '잎 수(장)' if corr_opt == "잎 수 vs 생중량" else '지상부 길이(mm)'
            
            fig_scatter = px.scatter(
                growth_df, x=x_val, y="생중량(g)", color="school",
                trendline="ols", # 회귀선 추가
                category_orders={"school": sort_order},
                color_discrete_map={k: v['color'] for k, v in schools.items()}
            )
            fig_scatter.update_layout(font=get_font_dict())
            st.plotly_chart(fig_scatter, use_container_width=True)

        # 엑셀 다운로드 (BytesIO 사용)
        with st.expander("💾 생육 데이터 원본 및 XLSX 다운로드"):
            st.dataframe(filtered_growth)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_growth.to_excel(writer, index=False, sheet_name='Combined_Data')
            buffer.seek(0)

            st.download_button(
                label="Excel 파일로 다운로드",
                data=buffer,
                file_name="전체_생육결과_데이터.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
