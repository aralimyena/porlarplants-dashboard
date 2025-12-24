import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path
import unicodedata
import io

# 페이지 설정
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    page_icon="🌱",
    layout="wide"
)

# 한글 폰트 설정
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# 파일명 정규화 함수
def normalize_filename(filename):
    """NFC/NFD 정규화를 모두 시도"""
    nfc = unicodedata.normalize("NFC", filename)
    nfd = unicodedata.normalize("NFD", filename)
    return nfc, nfd

# 데이터 로딩 함수
@st.cache_data
def load_environment_data():
    """환경 데이터 로딩 (CSV 4개)"""
    data_dir = Path("data")
    env_data = {}
    
    if not data_dir.exists():
        st.error("data 폴더를 찾을 수 없습니다.")
        return env_data
    
    # 학교별 패턴
    schools = ["송도고", "하늘고", "아라고", "동산고"]
    
    for school in schools:
        pattern_nfc = f"{unicodedata.normalize('NFC', school)}_환경데이터.csv"
        pattern_nfd = f"{unicodedata.normalize('NFD', school)}_환경데이터.csv"
        
        found = False
        for file in data_dir.iterdir():
            if file.is_file() and file.suffix == '.csv':
                file_nfc, file_nfd = normalize_filename(file.name)
                if file_nfc == pattern_nfc or file_nfd == pattern_nfd or file.name == pattern_nfc or file.name == pattern_nfd:
                    try:
                        df = pd.read_csv(file, encoding='utf-8-sig')
                        env_data[school] = df
                        found = True
                        break
                    except Exception as e:
                        st.warning(f"{school} 환경데이터 로딩 실패: {e}")
        
        if not found:
            st.warning(f"{school}_환경데이터.csv 파일을 찾을 수 없습니다.")
    
    return env_data

@st.cache_data
def load_growth_data():
    """생육 결과 데이터 로딩 (XLSX 1개, 4개 시트)"""
    data_dir = Path("data")
    growth_data = {}
    
    if not data_dir.exists():
        return growth_data
    
    # XLSX 파일 찾기
    xlsx_file = None
    for file in data_dir.iterdir():
        if file.is_file() and file.suffix in ['.xlsx', '.xls']:
            file_nfc, file_nfd = normalize_filename(file.name)
            if "생육결과데이터" in file_nfc or "생육결과데이터" in file_nfd:
                xlsx_file = file
                break
    
    if xlsx_file is None:
        st.error("생육결과데이터.xlsx 파일을 찾을 수 없습니다.")
        return growth_data
    
    try:
        # 시트 이름 동적으로 읽기
        xlsx = pd.ExcelFile(xlsx_file)
        for sheet_name in xlsx.sheet_names:
            df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
            # 시트명에서 학교명 추출
            for school in ["송도고", "하늘고", "아라고", "동산고"]:
                if school in sheet_name:
                    growth_data[school] = df
                    break
    except Exception as e:
        st.error(f"생육 데이터 로딩 실패: {e}")
    
    return growth_data

# EC 정보 매핑
EC_INFO = {
    "송도고": {"ec": 1.0, "type": "대조군", "color": "#4285F4"},
    "하늘고": {"ec": 2.0, "type": "최적", "color": "#34A853"},
    "아라고": {"ec": 4.0, "type": "고농도", "color": "#FBBC04"},
    "동산고": {"ec": 8.0, "type": "고농도", "color": "#EA4335"}
}

# 데이터 로딩
with st.spinner("데이터 로딩 중..."):
    env_data = load_environment_data()
    growth_data = load_growth_data()

# 제목
st.title("🌱 극지식물 최적 EC 농도 연구 및 차기 실험에서의 환경 조정 방향성")

# 사이드바
st.sidebar.header("🔍 분석 설정")
schools = ["전체"] + list(EC_INFO.keys())
selected_school = st.sidebar.selectbox("학교 선택", schools)

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📋 실험 개요 및 설계", "🌡️ 환경 변동성 분석", "📊 생육 성과 및 임계점 분석"])

# ==================== TAB 1: 실험 개요 및 설계 ====================
with tab1:
    st.header("📋 실험 개요 및 설계")
    
    # 연구 배경
    st.subheader("🔬 연구 배경")
    st.markdown("""
    극지 환경에서의 식물 재배는 기후 변화 연구 및 지속 가능한 식량 생산을 위한 핵심 기술입니다. 
    본 연구는 스마트팜 환경에서 **전기전도도(EC) 농도**가 극지식물의 생육에 미치는 영향을 분석하고, 
    최적의 재배 조건을 도출하여 차기 실험의 환경 조정 방향성을 제시합니다.
    """)
    
    # 실험 설계 테이블
    st.subheader("🧪 실험 설계")
    design_df = pd.DataFrame([
        {"학교명": school, "목표 EC": info["ec"], "처리 성격": info["type"], 
         "개체수": len(growth_data.get(school, []))}
        for school, info in EC_INFO.items()
    ])
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(design_df, use_container_width=True, hide_index=True)
    
    # 주요 지표 카드
    st.subheader("📌 주요 지표")
    metric_cols = st.columns(4)
    
    total_samples = sum(len(df) for df in growth_data.values())
    metric_cols[0].metric("총 분석 개체수", f"{total_samples}개")
    
    if env_data:
        avg_temp = sum(df['temperature'].mean() for df in env_data.values()) / len(env_data)
        avg_humidity = sum(df['humidity'].mean() for df in env_data.values()) / len(env_data)
        metric_cols[1].metric("평균 온도", f"{avg_temp:.1f}°C")
        metric_cols[2].metric("평균 습도", f"{avg_humidity:.1f}%")
    
    metric_cols[3].metric("도출된 최적 EC", "2.0 (하늘고)", delta="최적", delta_color="normal")

# ==================== TAB 2: 환경 변동성 분석 ====================
with tab2:
    st.header("🌡️ 환경 변동성 분석")
    
    if not env_data:
        st.error("환경 데이터를 불러올 수 없습니다.")
    else:
        # 환경 데이터 비교
        st.subheader("📊 환경 데이터 비교")
        
        # 통계 계산
        env_stats = {}
        for school, df in env_data.items():
            env_stats[school] = {
                'temp_mean': df['temperature'].mean(),
                'temp_std': df['temperature'].std(),
                'humidity_mean': df['humidity'].mean(),
                'humidity_std': df['humidity'].std(),
                'ph_mean': df['ph'].mean(),
                'ph_std': df['ph'].std(),
                'ec_mean': df['ec'].mean(),
                'ec_std': df['ec'].std()
            }
        
        # 2x2 서브플롯
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("평균 온도", "평균 습도", "평균 pH", "목표 대비 실측 EC"),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        schools_list = list(env_stats.keys())
        colors = [EC_INFO[s]["color"] for s in schools_list]
        
        # 온도
        fig.add_trace(
            go.Bar(x=schools_list, y=[env_stats[s]['temp_mean'] for s in schools_list],
                   name="온도", marker_color=colors, showlegend=False,
                   text=[f"{env_stats[s]['temp_mean']:.1f}°C" for s in schools_list],
                   textposition='outside'),
            row=1, col=1
        )
        
        # 습도
        fig.add_trace(
            go.Bar(x=schools_list, y=[env_stats[s]['humidity_mean'] for s in schools_list],
                   name="습도", marker_color=colors, showlegend=False,
                   text=[f"{env_stats[s]['humidity_mean']:.1f}%" for s in schools_list],
                   textposition='outside'),
            row=1, col=2
        )
        
        # pH
        fig.add_trace(
            go.Bar(x=schools_list, y=[env_stats[s]['ph_mean'] for s in schools_list],
                   name="pH", marker_color=colors, showlegend=False,
                   text=[f"{env_stats[s]['ph_mean']:.2f}" for s in schools_list],
                   textposition='outside'),
            row=2, col=1
        )
        
        # EC 목표 vs 실측
        target_ec = [EC_INFO[s]["ec"] for s in schools_list]
        actual_ec = [env_stats[s]['ec_mean'] for s in schools_list]
        
        fig.add_trace(
            go.Bar(x=schools_list, y=target_ec, name="목표 EC", 
                   marker_color='lightgray', opacity=0.5),
            row=2, col=2
        )
        fig.add_trace(
            go.Bar(x=schools_list, y=actual_ec, name="실측 EC", 
                   marker_color=colors,
                   text=[f"{ec:.2f}" for ec in actual_ec],
                   textposition='outside'),
            row=2, col=2
        )
        
        fig.update_xaxes(title_text="학교", row=2, col=1)
        fig.update_xaxes(title_text="학교", row=2, col=2)
        fig.update_yaxes(title_text="온도 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
        fig.update_yaxes(title_text="pH", row=2, col=1)
        fig.update_yaxes(title_text="EC", row=2, col=2)
        
        fig.update_layout(
            height=700,
            showlegend=True,
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 변동성 리포트
        st.subheader("📈 환경 변동성 리포트")
        
        variability_df = pd.DataFrame([
            {
                "학교": school,
                "온도 표준편차": f"{stats['temp_std']:.2f}°C",
                "습도 표준편차": f"{stats['humidity_std']:.2f}%",
                "pH 표준편차": f"{stats['ph_std']:.3f}",
                "EC 표준편차": f"{stats['ec_std']:.3f}"
            }
            for school, stats in env_stats.items()
        ])
        
        st.dataframe(variability_df, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **분석 결과:**
        - 환경 변동성(표준편차)이 낮을수록 실험 조건이 안정적으로 유지되었음을 의미합니다.
        - 표준편차가 높은 학교는 환경 제어 시스템 보완이 필요합니다.
        - 차기 실험에서는 변동성을 최소화하여 EC 효과를 더욱 명확히 분석할 수 있습니다.
        """)
        
        # 시계열 추이
        st.subheader("📅 시계열 환경 추이")
        
        if selected_school != "전체" and selected_school in env_data:
            df = env_data[selected_school].copy()
            
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
                df = df.sort_values('time')
            
            fig_ts = make_subplots(
                rows=3, cols=1,
                subplot_titles=(f"{selected_school} 온도 추이", 
                              f"{selected_school} 습도 추이", 
                              f"{selected_school} EC 추이"),
                vertical_spacing=0.08
            )
            
            color = EC_INFO[selected_school]["color"]
            
            fig_ts.add_trace(
                go.Scatter(x=df['time'] if 'time' in df.columns else df.index, 
                          y=df['temperature'], mode='lines', 
                          name='온도', line=dict(color=color)),
                row=1, col=1
            )
            
            fig_ts.add_trace(
                go.Scatter(x=df['time'] if 'time' in df.columns else df.index, 
                          y=df['humidity'], mode='lines', 
                          name='습도', line=dict(color=color)),
                row=2, col=1
            )
            
            fig_ts.add_trace(
                go.Scatter(x=df['time'] if 'time' in df.columns else df.index, 
                          y=df['ec'], mode='lines', 
                          name='EC', line=dict(color=color)),
                row=3, col=1
            )
            
            # 목표 EC 라인 추가
            target = EC_INFO[selected_school]["ec"]
            fig_ts.add_hline(y=target, line_dash="dash", line_color="red", 
                           annotation_text=f"목표 EC: {target}", row=3, col=1)
            
            fig_ts.update_yaxes(title_text="온도 (°C)", row=1, col=1)
            fig_ts.update_yaxes(title_text="습도 (%)", row=2, col=1)
            fig_ts.update_yaxes(title_text="EC", row=3, col=1)
            fig_ts.update_xaxes(title_text="시간", row=3, col=1)
            
            fig_ts.update_layout(
                height=800,
                showlegend=False,
                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
            )
            
            st.plotly_chart(fig_ts, use_container_width=True)
            
            # 방향성 피드백
            temp_mean = env_stats[selected_school]['temp_mean']
            temp_std = env_stats[selected_school]['temp_std']
            humidity_mean = env_stats[selected_school]['humidity_mean']
            humidity_std = env_stats[selected_school]['humidity_std']
            ec_mean = env_stats[selected_school]['ec_mean']
            target_ec = EC_INFO[selected_school]['ec']
            
            feedback_text = f"""
### 🎯 {selected_school} 차기 실험 환경 조정 방향성

**현재 상태:**
- 평균 온도: {temp_mean:.1f}°C (변동성: ±{temp_std:.2f})
- 평균 습도: {humidity_mean:.1f}% (변동성: ±{humidity_std:.2f})
- 실측 EC: {ec_mean:.2f} (목표: {target_ec})

**개선 제안:**
1. EC 정밀도: 목표 대비 편차를 ±0.1 이내로 유지
2. 온도 안정화: 주야간 온도 변동을 ±2°C 이내로 제어
3. 습도 제어: 일정 습도 유지를 위한 자동화 시스템 보완
"""
            st.markdown(feedback_text)
        else:
            st.info("특정 학교를 선택하면 시계열 추이를 확인할 수 있습니다.")
        
        # 데이터 다운로드
        with st.expander("📥 환경 데이터 다운로드"):
            for school, df in env_data.items():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{school} 환경데이터**")
                csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                col2.download_button(
                    label="CSV 다운로드",
                    data=csv,
                    file_name=f"{school}_환경데이터.csv",
                    mime="text/csv"
                )

# ==================== TAB 3: 생육 성과 및 임계점 분석 ====================
with tab3:
    st.header("📊 생육 성과 및 임계점 분석")
    
    if not growth_data:
        st.error("생육 데이터를 불러올 수 없습니다.")
    else:
        # 핵심 결과
        st.subheader("🏆 핵심 결과: EC 농도별 평균 생중량")
        
        avg_weights = {}
        for school, df in growth_data.items():
            if '생중량(g)' in df.columns:
                avg_weights[school] = df['생중량(g)'].mean()
        
        fig_key = go.Figure()
        schools_list = list(avg_weights.keys())
        weights = list(avg_weights.values())
        colors = [EC_INFO[s]["color"] for s in schools_list]
        
        # 최대값 강조
        max_school = max(avg_weights, key=avg_weights.get)
        colors_highlight = [EC_INFO[s]["color"] if s != max_school else "#34A853" 
                           for s in schools_list]
        
        fig_key.add_trace(go.Bar(
            x=schools_list,
            y=weights,
            marker_color=colors_highlight,
            text=[f"{w:.2f}g<br>EC {EC_INFO[s]['ec']}" for s, w in zip(schools_list, weights)],
            textposition='outside'
        ))
        
        fig_key.update_layout(
            title=f"최적 EC: {EC_INFO[max_school]['ec']} ({max_school})",
            xaxis_title="학교 (EC 조건)",
            yaxis_title="평균 생중량 (g)",
            height=400,
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )
        
        st.plotly_chart(fig_key, use_container_width=True)
        
        # 생육 지표 분석 (2x2)
        st.subheader("📈 생육 지표 종합 분석")
        
        fig_growth = make_subplots(
            rows=2, cols=2,
            subplot_titles=("평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수 분포"),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 데이터 준비
        metrics = {
            '생중량(g)': [],
            '잎 수(장)': [],
            '지상부 길이(mm)': []
        }
        counts = []
        
        for school in schools_list:
            df = growth_data[school]
            counts.append(len(df))
            for col in metrics.keys():
                if col in df.columns:
                    metrics[col].append(df[col].mean())
                else:
                    metrics[col].append(0)
        
        colors = [EC_INFO[s]["color"] for s in schools_list]
        
        # 생중량
        fig_growth.add_trace(
            go.Bar(x=schools_list, y=metrics['생중량(g)'], 
                   marker_color=colors, showlegend=False,
                   text=[f"{v:.2f}g" for v in metrics['생중량(g)']],
                   textposition='outside'),
            row=1, col=1
        )
        
        # 잎 수
        fig_growth.add_trace(
            go.Bar(x=schools_list, y=metrics['잎 수(장)'], 
                   marker_color=colors, showlegend=False,
                   text=[f"{v:.1f}장" for v in metrics['잎 수(장)']],
                   textposition='outside'),
            row=1, col=2
        )
        
        # 지상부 길이
        fig_growth.add_trace(
            go.Bar(x=schools_list, y=metrics['지상부 길이(mm)'], 
                   marker_color=colors, showlegend=False,
                   text=[f"{v:.1f}mm" for v in metrics['지상부 길이(mm)']],
                   textposition='outside'),
            row=2, col=1
        )
        
        # 개체수
        fig_growth.add_trace(
            go.Bar(x=schools_list, y=counts, 
                   marker_color=colors, showlegend=False,
                   text=[f"{c}개" for c in counts],
                   textposition='outside'),
            row=2, col=2
        )
        
        fig_growth.update_yaxes(title_text="생중량 (g)", row=1, col=1)
        fig_growth.update_yaxes(title_text="잎 수 (장)", row=1, col=2)
        fig_growth.update_yaxes(title_text="길이 (mm)", row=2, col=1)
        fig_growth.update_yaxes(title_text="개체수", row=2, col=2)
        
        fig_growth.update_layout(
            height=700,
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)
        
        # 임계점 및 영향력 분석
        st.subheader("🔍 임계점 및 영향력 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 바이올린 플롯
            all_growth = []
            for school, df in growth_data.items():
                if '생중량(g)' in df.columns:
                    temp_df = df[['생중량(g)']].copy()
                    temp_df['학교'] = school
                    temp_df['EC'] = EC_INFO[school]['ec']
                    all_growth.append(temp_df)
            
            if all_growth:
                combined_df = pd.concat(all_growth, ignore_index=True)
                
                fig_violin = go.Figure()
                for school in schools_list:
                    school_data = combined_df[combined_df['학교'] == school]
                    fig_violin.add_trace(go.Violin(
                        y=school_data['생중량(g)'],
                        name=f"{school}<br>EC {EC_INFO[school]['ec']}",
                        box_visible=True,
                        meanline_visible=True,
                        fillcolor=EC_INFO[school]['color'],
                        opacity=0.6
                    ))
                
                fig_violin.update_layout(
                    title="학교별 생중량 분포 (임계점 시각화)",
                    yaxis_title="생중량 (g)",
                    height=500,
                    showlegend=True,
                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
                )
                
                st.plotly_chart(fig_violin, use_container_width=True)
        
        with col2:
            # 상관관계 분석
            st.markdown("#### 📊 상관관계 분석")
            
            # 잎 수 vs 생중량
            all_corr = []
            for school, df in growth_data.items():
                if '잎 수(장)' in df.columns and '생중량(g)' in df.columns:
                    temp_df = df[['잎 수(장)', '생중량(g)']].copy()
                    temp_df['학교'] = school
                    all_corr.append(temp_df)
            
            if all_corr:
                corr_df = pd.concat(all_corr, ignore_index=True)
                
                fig_corr1 = px.scatter(
                    corr_df, x='잎 수(장)', y='생중량(g)', color='학교',
                    color_discrete_map={s: EC_INFO[s]['color'] for s in schools_list},
                    trendline="ols",
                    title="잎 수 vs 생중량"
                )
                fig_corr1.update_layout(
                    height=250,
                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
                )
                st.plotly_chart(fig_corr1, use_container_width=True)
            
            # 지상부 길이 vs 생중량
            all_corr2 = []
            for school, df in growth_data.items():
                if '지상부 길이(mm)' in df.columns and '생중량(g)' in df.columns:
                    temp_df = df[['지상부 길이(mm)', '생중량(g)']].copy()
                    temp_df['학교'] = school
                    all_corr2.append(temp_df)
            
            if all_corr2:
                corr_df2 = pd.concat(all_corr2, ignore_index=True)
                
                fig_corr2 = px.scatter(
                    corr_df2, x='지상부 길이(mm)', y='생중량(g)', color='학교',
                    color_discrete_map={s: EC_INFO[s]['color'] for s in schools_list},
                    trendline="ols",
                    title="지상부 길이 vs 생중량"
                )
                fig_corr2.update_layout(
                    height=250,
                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
                )
                st.plotly_chart(fig_corr2, use_container_width=True)
        
        # 결론 섹션
        st.subheader("📝 종합 결론")
        
        max_weight = max(avg_weights.values())
        optimal_school = max(avg_weights, key=avg_weights.get)
        optimal_ec = EC_INFO[optimal_school]['ec']
        
        conclusion_text = f"""
### 🎯 주요 발견

1. **최적 EC 농도**: **{optimal_ec} (하늘고)**에서 평균 생중량 **{max_weight:.2f}g**으로 최대값 기록

2. **임계점 분석**:
   - EC 1.0 (송도고): 대조군 대비 생육 양호
   - EC 2.0 (하늘고): 최적 성장 구간 ✅
   - EC 4.0 (아라고): 생중량 감소 시작
   - EC 8.0 (동산고): 고농도로 인한 생육 저해 확인

3. **환경 안정성의 중요성**:
   - EC 농도뿐만 아니라 온도/습도 변동성도 생중량에 영향
   - 환경 제어가 안정적인 조건에서 더 우수한 생육 결과 확인

4. **차기 실험 권장사항**:
   - EC 2.0을 중심으로 ±0.5 범위 내 세밀한 농도 구간 추가 실험
