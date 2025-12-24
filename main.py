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
# 0. 전역 설정 (NameError 방지: 학교별 설정 정보를 전역 변수로 이동)
# -----------------------------------------------------------------------------
SCHOOLS_CONFIG = {
    "송도고": {"ec": 1.0, "color": "#1f77b4"},
    "하늘고": {"ec": 2.0, "color": "#2ca02c"}, # 최적
    "아라고": {"ec": 4.0, "color": "#ff7f0e"},
    "동산고": {"ec": 8.0, "color": "#d62728"}
}

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
    
    # 1) 환경 데이터 로드 (CSV)
    for school_name in SCHOOLS_CONFIG.keys():
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
                df['target_ec'] = SCHOOLS_CONFIG[school_name]['ec']
                env_data[school_name] = df
            except Exception as e:
                st.error(f"❌ {school_name} 환경 데이터 로딩 실패: {e}")
        else:
            # 파일이 없을 경우 로그만 남기고 진행 (st.error 남발 방지)
            pass

    # 2) 생육 결과 데이터 로드 (XLSX)
    growth_file = find_file_in_dir(base_path, "4개교_생육결과데이터", ".xlsx")
    
    if growth_file:
        try:
            # 시트 이름 하드코딩 없이 동적 로드
            xls = pd.ExcelFile(growth_file)
            for sheet_name in xls.sheet_names:
                # 시트 이름 정규화하여 학교명 매칭
                sheet_nfc = unicodedata.normalize("NFC", sheet_name)
                matched_school
