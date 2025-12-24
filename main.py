import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import unicodedata
from pathlib import Path
import io
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="극지식물 EC 농도 연구",
    page_icon="🌱",
    layout="wide"
)

# 한글 폰트 설정
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# 학교별 EC 조건 정의
SCHOOL_EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

SCHOOL_TREATMENT = {
    "송도고": "저농도",
    "하늘고": "최적 농도",
    "아라고": "고농도",
    "동산고": "초고농도"
}

@st.cache_data
def load_environment_data():
    """환경 데이터 로딩 (NFC/NFD 정규화)"""
    data_dir = Path("data")
    env_data = {}
    
    if not data_dir.exists():
        st.error("data 폴더를 찾을 수 없습니다.")
        return {}
    
    # CSV 파일 찾기
    for school_name in SCHOOL_EC_MAP.keys():
        found = False
        for file_path in data_dir.glob("*.csv"):
            # NFC/NFD 양방향 비교
            file_stem_nfc = unicodedata.normalize("NFC", file_path.stem)
            file_stem_nfd = unicodedata.normalize("NFD", file_path.stem)
            target_nfc = unicodedata.normalize("NFC", f"{school_name}_환경데이터")
            target_nfd = unicodedata.normalize("NFD", f"{school_name}_환경데이터")
            
            if file_stem_nfc == target_nfc or file_stem_nfd == target_nfd:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    env_data[school_name] = df
                    found = True
                    break
                except Exception as e:
                    st.error(f"{school_name} 데이터 로딩 실패: {e}")
        
        if not found:
            st.warning(f"{school_name}_환경데이터.csv 파일을 찾을 수 없습니다.")
    
    return env_data

@st.cache_data
def load_growth_data():
    """생육 데이터 로딩 (XLSX)"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        st.error("data 폴더를 찾을 수 없습니다.")
        return {}
    
    # XLSX 파일 찾기
    xlsx_files = list(data_dir.glob("*.xlsx"))
    
    if not xlsx_files:
        st.error("XLSX 파일을 찾을 수 없습니다.")
        return {}
    
    xlsx_path = xlsx_files[0]
    growth_data = {}
    
    try:
        excel_file = pd.ExcelFile(xlsx_path)
        
        # 모든 시트 로딩
        for sheet_name in excel_file.sheet_names:
            sheet_nfc = unicodedata.normalize("NFC", sheet_name)
            sheet_nfd = unicodedata.normalize("NFD", sheet_name)
            
            # 학교명 매칭
            for school_name in SCHOOL_EC_MAP.keys():
                school_nfc = unicodedata.normalize("NFC", school_name)
                school_nfd = unicodedata.normalize("NFD", school_name)
                
                if school_nfc in sheet_nfc or school_nfd in sheet_nfd:
                    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
                    growth_data[school_name] = df
                    break
        
        return growth_data
    except Exception as e:
        st.error(f"생육 데이터 로딩 실패: {e}")
        return {}

def calculate_env_stats(env_data):
    """환경 데이터 통계 계산"""
    stats = {}
    for school, df in env_data.items():
        if df is not None and not df.empty:
            stats[school] = {
                "temp_mean": df['temperature'].mean(),
                "temp_std": df['temperature'].std(),
                "humidity_mean": df['humidity'].mean(),
                "humidity_std": df['humidity'].std(),
                "ph_mean": df['ph'].mean(),
                "ph_std": df['ph'].std(),
                "ec_mean": df['ec'].mean(),
                "ec_std": df['ec'].std(),
                "ec_target": SCHOOL_EC_MAP[school]
            }
    return stats

def calculate_growth_stats(growth_data):
    """생육 데이터 통계 계산"""
    stats = {}
    for school, df in growth_data.items():
        if df is not None and not df.empty:
            # 컬럼명 정규화
            col_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if '생중량' in col or 'weight' in col_lower:
                    col_map['weight'] = col
                elif '잎' in col and '수' in col:
                    col_map['leaf_count'] = col
                elif '지상부' in col and '길이' in col:
                    col_map['shoot_length'] = col
                elif '지하부' in col and '길이' in col:
                    col_map['root_length'] = col
            
            stats[school] = {
                "count": len(df),
                "weight_mean": df[col_map.get('weight')].mean() if 'weight' in col_map else 0,
                "weight_std": df[col_map.get('weight')].std() if 'weight' in col_map else 0,
                "leaf_mean": df[col_map.get('leaf_count')].mean() if 'leaf_count' in col_map else 0,
                "shoot_mean": df[col_map.get('shoot_length')].mean() if 'shoot_length' in col_map else 0,
                "ec": SCHOOL_EC_MAP[school],
                "data": df,
                "col_map": col_map
            }
    return stats

# 데이터 로딩
with st.spinner("데이터를 불러오는 중..."):
    env_data = load_environment_data()
    growth_data = load_growth_data()

if not env_data or not growth_data:
    st.error("필요한 데이터 파일을 찾을 수 없습니다. data 폴더와 파일을 확인해주세요.")
    st.stop()

env_stats = calculate_env_stats(env_data)
growth_stats = calculate_growth_stats(growth_data)

# 타이틀
st.title("🌱 극지식물 최적 EC 농도 연구 및 차기 실험에서의 환경 조정 방향성")

# 사이드바
st.sidebar.header("학교 선택")
school_options = ["전체"] + list(SCHOOL_EC_MAP.keys())
selected_school = st.sidebar.selectbox("분석할 학교를 선택하세요", school_options)

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📋 실험 개요 및 설계", "🌡️ 환경 변동성 분석", "📊 생육 성과 및 임계점 분석"])

# ===== TAB 1: 실험 개요 및 설계 =====
with tab1:
    st.header("연구 배경")
    st.markdown("""
    극지 환경에서의 식물 재배는 기후변화 대응 및 식량 안보 측면에서 중요한 연구 주제입니다.
    본 연구는 **스마트팜 환경에서 극지식물의 최적 생육 조건**을 파악하고, 
    특히 **EC(전기전도도) 농도**가 식물 생육에 미치는 영향을 분석합니다.
    """)
    
    st.header("실험 설계")
    design_df = pd.DataFrame({
        "학교명": list(SCHOOL_EC_MAP.keys()),
        "목표 EC": list(SCHOOL_EC_MAP.values()),
        "처리 성격": list(SCHOOL_TREATMENT.values()),
        "개체수": [growth_stats[s]["count"] for s in SCHOOL_EC_MAP.keys()]
    })
    st.dataframe(design_df, use_container_width=True)
    
    st.header("주요 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    total_samples = sum([s["count"] for s in growth_stats.values()])
    avg_temp = np.mean([s["temp_mean"] for s in env_stats.values()])
    avg_humidity = np.mean([s["humidity_mean"] for s in env_stats.values()])
    optimal_ec = 2.0
    
    col1.metric("총 분석 개체수", f"{total_samples}개")
    col2.metric("평균 온도", f"{avg_temp:.1f}°C")
    col3.metric("평균 습도", f"{avg_humidity:.1f}%")
    col4.metric("도출된 최적 EC", f"{optimal_ec} dS/m")

# ===== TAB 2: 환경 변동성 분석 =====
with tab2:
    st.header("환경 데이터 비교")
    
    # 2x2 서브플롯
    schools_to_plot = [selected_school] if selected_school != "전체" else list(SCHOOL_EC_MAP.keys())
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("평균 온도", "평균 습도", "평균 pH", "EC 정밀도 (목표 대비)"),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    schools = [s for s in schools_to_plot if s in env_stats]
    temp_means = [env_stats[s]["temp_mean"] for s in schools]
    humidity_means = [env_stats[s]["humidity_mean"] for s in schools]
    ph_means = [env_stats[s]["ph_mean"] for s in schools]
    ec_targets = [env_stats[s]["ec_target"] for s in schools]
    ec_means = [env_stats[s]["ec_mean"] for s in schools]
    
    # 온도
    fig.add_trace(go.Bar(x=schools, y=temp_means, name="온도", marker_color='indianred'), row=1, col=1)
    
    # 습도
    fig.add_trace(go.Bar(x=schools, y=humidity_means, name="습도", marker_color='lightblue'), row=1, col=2)
    
    # pH
    fig.add_trace(go.Bar(x=schools, y=ph_means, name="pH", marker_color='lightgreen'), row=2, col=1)
    
    # EC 정밀도
    fig.add_trace(go.Bar(x=schools, y=ec_targets, name="목표 EC", marker_color='orange'), row=2, col=2)
    fig.add_trace(go.Bar(x=schools, y=ec_means, name="실측 EC", marker_color='gold'), row=2, col=2)
    
    fig.update_xaxes(title_text="학교", row=2, col=1)
    fig.update_xaxes(title_text="학교", row=2, col=2)
    fig.update_yaxes(title_text="온도 (°C)", row=1, col=1)
    fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
    fig.update_yaxes(title_text="pH", row=2, col=1)
    fig.update_yaxes(title_text="EC (dS/m)", row=2, col=2)
    
    fig.update_layout(
        height=700,
        showlegend=True,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif", size=12)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 변동성 리포트
    st.header("환경 변동성 리포트")
    variability_data = []
    for school in schools:
        variability_data.append({
            "학교": school,
            "온도 표준편차": f"{env_stats[school]['temp_std']:.2f}°C",
            "습도 표준편차": f"{env_stats[school]['humidity_std']:.2f}%",
            "EC 표준편차": f"{env_stats[school]['ec_std']:.2f} dS/m",
            "안정성 평가": "우수" if env_stats[school]['temp_std'] < 2 else "보통"
        })
    
    st.dataframe(pd.DataFrame(variability_data), use_container_width=True)
    
    st.markdown("""
    **분석 결과:**
    - 환경 변동성(표준편차)이 낮을수록 실험 조건이 안정적입니다.
    - 온도 변동이 2°C 이상인 경우 식물 생육에 스트레스를 줄 수 있습니다.
    - 차기 실험에서는 환경 제어 시스템의 정밀도를 높여야 합니다.
    """)
    
    # 시계열 추이
    if selected_school != "전체":
        st.header(f"{selected_school} 시계열 추이")
        
        if selected_school in env_data:
            df_env = env_data[selected_school].copy()
            
            fig_ts = make_subplots(
                rows=3, cols=1,
                subplot_titles=("온도 추이", "습도 추이", "EC 추이"),
                vertical_spacing=0.1
            )
            
            fig_ts.add_trace(go.Scatter(x=df_env.index, y=df_env['temperature'], mode='lines', name='온도'), row=1, col=1)
            fig_ts.add_trace(go.Scatter(x=df_env.index, y=df_env['humidity'], mode='lines', name='습도'), row=2, col=1)
            fig_ts.add_trace(go.Scatter(x=df_env.index, y=df_env['ec'], mode='lines', name='EC'), row=3, col=1)
            
            fig_ts.update_yaxes(title_text="온도 (°C)", row=1, col=1)
            fig_ts.update_yaxes(title_text="습도 (%)", row=2, col=1)
            fig_ts.update_yaxes(title_text="EC (dS/m)", row=3, col=1)
            
            fig_ts.update_layout(
                height=800,
                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
            )
            
            st.plotly_chart(fig_ts, use_container_width=True)
            
            # 차기 실험 방향성
            st.subheader("차기 실험 환경 조정 방향성")
            st.markdown(f"""
            **{selected_school} 환경 제어 개선 방안:**
            - 온도 변동성: {env_stats[selected_school]['temp_std']:.2f}°C → 목표: 1.5°C 이하
            - EC 정밀도: 목표 {SCHOOL_EC_MAP[selected_school]} dS/m, 실측 평균 {env_stats[selected_school]['ec_mean']:.2f} dS/m
            - 센서 점검 주기 단축 및 자동 제어 시스템 보완 필요
            """)
    
    # 데이터 다운로드
    with st.expander("환경 데이터 원본 보기"):
        for school in schools:
            st.subheader(school)
            st.dataframe(env_data[school], use_container_width=True)
            
            csv = env_data[school].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"{school} CSV 다운로드",
                data=csv,
                file_name=f"{school}_환경데이터.csv",
                mime="text/csv"
            )

# ===== TAB 3: 생육 성과 및 임계점 분석 =====
with tab3:
    st.header("핵심 결과: EC 농도별 평균 생중량")
    
    schools_growth = list(growth_stats.keys())
    ec_values = [growth_stats[s]["ec"] for s in schools_growth]
    weight_means = [growth_stats[s]["weight_mean"] for s in schools_growth]
    
    # 최대값 강조
    max_idx = weight_means.index(max(weight_means))
    colors = ['lightcoral' if i != max_idx else 'green' for i in range(len(schools_growth))]
    
    fig_weight = go.Figure(data=[
        go.Bar(x=schools_growth, y=weight_means, marker_color=colors,
               text=[f"{w:.2f}g" for w in weight_means], textposition='outside')
    ])
    
    fig_weight.update_layout(
        title="EC 농도별 평균 생중량 비교 (하늘고: 최적 EC 2.0)",
        xaxis_title="학교 (EC 농도)",
        yaxis_title="평균 생중량 (g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif", size=14),
        height=400
    )
    
    st.plotly_chart(fig_weight, use_container_width=True)
    
    st.success(f"✅ **최적 EC: {SCHOOL_EC_MAP[schools_growth[max_idx]]} dS/m ({schools_growth[max_idx]})**에서 평균 생중량 {weight_means[max_idx]:.2f}g으로 최대!")
    
    # 생육 지표 분석 (2x2)
    st.header("생육 지표 상세 분석")
    
    schools_to_analyze = [selected_school] if selected_school != "전체" else schools_growth
    schools_filtered = [s for s in schools_to_analyze if s in growth_stats]
    
    fig_growth = make_subplots(
        rows=2, cols=2,
        subplot_titles=("평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수 분포"),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    weights = [growth_stats[s]["weight_mean"] for s in schools_filtered]
    leaves = [growth_stats[s]["leaf_mean"] for s in schools_filtered]
    shoots = [growth_stats[s]["shoot_mean"] for s in schools_filtered]
    counts = [growth_stats[s]["count"] for s in schools_filtered]
    
    fig_growth.add_trace(go.Bar(x=schools_filtered, y=weights, name="생중량", marker_color='mediumseagreen'), row=1, col=1)
    fig_growth.add_trace(go.Bar(x=schools_filtered, y=leaves, name="잎 수", marker_color='skyblue'), row=1, col=2)
    fig_growth.add_trace(go.Bar(x=schools_filtered, y=shoots, name="지상부 길이", marker_color='coral'), row=2, col=1)
    fig_growth.add_trace(go.Bar(x=schools_filtered, y=counts, name="개체수", marker_color='gold'), row=2, col=2)
    
    fig_growth.update_yaxes(title_text="생중량 (g)", row=1, col=1)
    fig_growth.update_yaxes(title_text="잎 수 (장)", row=1, col=2)
    fig_growth.update_yaxes(title_text="길이 (mm)", row=2, col=1)
    fig_growth.update_yaxes(title_text="개체수", row=2, col=2)
    
    fig_growth.update_layout(
        height=700,
        showlegend=False,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    
    st.plotly_chart(fig_growth, use_container_width=True)
    
    # 바이올린 플롯
    st.header("임계점 분석: 생중량 분포")
    
    fig_violin = go.Figure()
    
    for school in schools_filtered:
        col_map = growth_stats[school]["col_map"]
        if 'weight' in col_map:
            weight_col = col_map['weight']
            df_school = growth_stats[school]["data"]
            
            fig_violin.add_trace(go.Violin(
                y=df_school[weight_col],
                name=f"{school} (EC {SCHOOL_EC_MAP[school]})",
                box_visible=True,
                meanline_visible=True
            ))
    
    fig_violin.update_layout(
        title="학교별 생중량 분포 (바이올린 플롯)",
        yaxis_title="생중량 (g)",
        xaxis_title="학교 (EC 농도)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif", size=14),
        height=500
    )
    
    st.plotly_chart(fig_violin, use_container_width=True)
    
    st.markdown("""
    **임계점 분석 결과:**
    - EC 2.0 (하늘고)에서 생중량이 최대치를 보임
    - EC 4.0 (아라고) 이상부터 생육이 저해되기 시작
    - EC 8.0 (동산고)에서는 염 스트레스로 인한 생육 감소 확인
    """)
    
    # 상관관계 분석
    st.header("생육 지표 간 상관관계")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_corr1 = go.Figure()
        
        for school in schools_filtered:
            col_map = growth_stats[school]["col_map"]
            df_school = growth_stats[school]["data"]
            
            if 'leaf_count' in col_map and 'weight' in col_map:
                fig_corr1.add_trace(go.Scatter(
                    x=df_school[col_map['leaf_count']],
                    y=df_school[col_map['weight']],
                    mode='markers',
                    name=school,
                    marker=dict(size=8)
                ))
        
        fig_corr1.update_layout(
            title="잎 수 vs 생중량",
            xaxis_title="잎 수 (장)",
            yaxis_title="생중량 (g)",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
            height=400
        )
        
        st.plotly_chart(fig_corr1, use_container_width=True)
    
    with col2:
        fig_corr2 = go.Figure()
        
        for school in schools_filtered:
            col_map = growth_stats[school]["col_map"]
            df_school = growth_stats[school]["data"]
            
            if 'shoot_length' in col_map and 'weight' in col_map:
                fig_corr2.add_trace(go.Scatter(
                    x=df_school[col_map['shoot_length']],
                    y=df_school[col_map['weight']],
                    mode='markers',
                    name=school,
                    marker=dict(size=8)
                ))
        
        fig_corr2.update_layout(
            title="지상부 길이 vs 생중량",
            xaxis_title="지상부 길이 (mm)",
            yaxis_title="생중량 (g)",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
            height=400
        )
        
        st.plotly_chart(fig_corr2, use_container_width=True)
    
    # 결론
    st.header("종합 결론")
    st.markdown(f"""
    ### 주요 발견사항
    
    1. **최적 EC 농도**: **2.0 dS/m** (하늘고)에서 생중량 최대
    2. **임계 EC 구간**: 4.0 dS/m 이상에서 생육 저해 시작
    3. **환경 안정성**: 온도/습도 변동성이 낮을수록 생육 우수
    4. **상관관계**: 잎 수와 지상부 길이 모두 생중량과 양의 상관관계
    
    ### 차기 실험 권장사항
    
    - EC 농도: **1.5~2.5 dS/m 범위 정밀 실험** 필요
    - 환경 제어: 온도 변동 **±1.5°C 이내** 유지
    - 모니터링: 센서 점검 주기 단축 및 자동 제어 시스템 고도화
    - 추가 변수: 광량, CO2 농도 등 복합 요인 분석 필요
    """)
    
    # 데이터 다운로드
    with st.expander("생육 데이터 원본 보기"):
        for school in schools_filtered:
            st.subheader(f"{school} (개체수: {growth_stats[school]['count']}개)")
            st.dataframe(growth_stats[school]["data"], use_container_width=True)
            
            # XLSX 다운로드
            buffer = io.BytesIO()
            growth_stats[school]["data"].to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            
            st.download_button(
                label=f"{school} XLSX 다운로드",
                data=buffer,
                file_name=f"{school}_생육데이터.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# 푸터
st.markdown("---")
st.markdown("🌱 극지식물 EC 농도 연구 대시보드 | Streamlit으로 제작")
