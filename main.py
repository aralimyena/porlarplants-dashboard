[Role]
너는 Streamlit 전문가야.
한글 파일명(NFC/NFD) 인식 오류와 한글 폰트 깨짐을 완벽히 방지하며,
Streamlit Cloud에서도 에러 없이 실행되는 코드를 작성한다.

[Task]
극지식물 최적 EC 농도 연구 대시보드 제작 
📁 파일 구조:
polar-plant-dashboard/ 
├── main.py 
├── data/ 
│ ├── 송도고_환경데이터.csv 
│ ├── 하늘고_환경데이터.csv 
│ ├── 아라고_환경데이터.csv 
│ ├── 동산고_환경데이터.csv 
│ └── 4개교_생육결과데이터.xlsx (4개 시트: 동산고, 송도고, 아라고, 하늘고) 
└── requirements.txt

📊 데이터 정보:
환경 데이터 (CSV 4개):
●	컬럼: time, temperature, humidity, ph, ec
●	학교별 측정 주기 다름.
생육 결과 데이터 (XLSX 1개, 4개 시트):
●	시트별 학교: 동산고(58개), 송도고(29개), 아라고(106개), 하늘고(45개)
●	컬럼: 개체번호, 잎 수(장), 지상부 길이(mm), 지하부길이(mm), 생중량(g)
●	✅ 학교별 비교 가능!
학교별 EC 조건:
●	송도고: EC 1.0
●	하늘고: EC 2.0 (최적)
●	아라고: EC 4.0
●	동산고: EC 8.0
핵심 분석:
-학교별 환경 데이터 비교: 온도/습도/pH/EC의 평균값뿐만 아니라 **표준편차(변동성)**를 분석하여 환경 제어의 안정성 평가.
-EC별 생육 결과 비교: 생중량, 잎 수, 길이 데이터를 통해 **최적 EC(하늘고: 2.0)**를 도출하고, 성장이 저해되기 시작하는 임계 EC 지점을 파악.
-복합 요인 분석: EC 농도 외에 온도/습도 등 환경 변동성(안정성)이 생중량에 미치는 영향을 상관관계와 산점도를 통해 분석.
-차기 실험 방향성 제안: 데이터 분석 결과를 바탕으로 환경 조정 및 실험 설계 보완 방향 제시.
[Format]
앱 구조:
●	제목:  극지식물 최적 EC 농도 연구 및 차기 실험에서의 환경 조정 방향성 
●	레이아웃: wide mode
●	사이드바: 학교 선택 드롭다운 (전체, 송도고, 하늘고, 아라고, 동산고)

3개 탭:
•  Tab 1 "실험 개요 및 설계"
•	연구 배경: 극지 식물 스마트팜 재배의 필요성 및 연구 목적 설명.
•	실험 설계: 학교별 EC 처리 조건 테이블 (학교명, 목표 EC, 처리 성격[대조/최적/고농도], 개체수).
•	주요 지표 카드: 총 분석 개체수, 데이터 기반 평균 온도/습도, 도출된 최적 EC.
•  Tab 2 “ 환경 변동성 분석"
•	환경 데이터 비교 (2x2): 평균 온도, 습도, pH 막대그래프 + 목표 대비 실측 EC 정밀도 비교.
•	변동성 리포트: 학교별 환경 변동성(표준편차)을 비교하고, 이 변동성이 실험 결과에 미칠 수 있는 영향 기술.
•	시계열 추이: 선택한 학교의 시계열 그래프(온도, 습도, EC)와 함께 차기 실험에서의 환경 조정 방향성(방향성 피드백) 섹션 추가.
•	Expander: 데이터 테이블 및 CSV 다운로드.
•  Tab 3 "생육 성과 및 임계점 분석"
•	핵심 결과: EC 농도별 평균 생중량 비교 (최대값인 하늘고 강조).
•	생육 지표 분석 (2x2): 생중량, 잎 수, 지상부 길이, 개체수 분포 막대그래프.
•	임계점 및 영향력 분석: - 바이올린 플롯: 학교별 생중량 분포를 통해 성장이 급감하는 임계 EC 구간 시각화.
o	상관관계 산점도: (1) 잎 수 vs 생중량, (2) 지상부 길이 vs 생중량.
•	결론 섹션: EC 수치와 환경 안정성이 생중량에 끼친 영향력을 종합 요약.
•	Expander: 생육 데이터 원본 및 XLSX 다운로드

[Constraints]
✅ 필수 1: 파일 인식 (매우 중요!)
●	pathlib.Path.iterdir() 사용
●	unicodedata.normalize("NFC"/"NFD") 양방향 비교
●	파일명 f-string 조합 금지
●	glob 패턴만 사용하는 방식 금지
●	시트 이름 하드코딩 금지
예시 코드:
# 예시: 반드시 이런 구조 사용
from pathlib import Path
import unicodedata

2. Plotly 서브플롯 (NameError 방지)
반드시 import 포함
from plotly.subplots import make_subplots
3. XLSX 다운로드 (TypeError 방지)
●	to_excel()은 반드시 BytesIO 사용
●	파일 경로 없이 호출 ❌
import io

buffer = io.BytesIO()
df.to_excel(buffer, index=False, engine="openpyxl")
buffer.seek(0)

st.download_button(
    data=buffer,
    file_name="파일명.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

4. 한글 폰트 (깨짐 방지)
Streamlit CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)
Plotly
fig.update_layout(
    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
)
5. 성능 & 안정성
●	모든 데이터 로딩 함수에 @st.cache_data
●	로딩 중 st.spinner()
●	데이터 없을 경우 st.error()로 명확히 안내

❌ 금지 사항:
●	“여기에 코드 추가” 같은 플레이스홀더
●	파일명/시트명 하드코딩
●	df.to_excel() 단독 호출
●	import 누락된 상태의 make_subplots


✅ 기타:
- @st.cache_data로 데이터 로딩 최적화
- 에러 발생 시 st.error()로 명확히 안내
- 로딩 중 st.spinner() 표시
- EC별 생중량 비교 시 하늘고(EC 2.0) 최적값 강조


[Output]

1. main.py
- 완성된 전체 코드
- 복사-붙여넣기 후 즉시 실행 가능
- 모든 그래프, 버튼, 다운로드 실제 작동

2. requirements.txt
streamlit
pandas
plotly
openpyxl



