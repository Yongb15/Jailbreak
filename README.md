# 🛡️ Jailbreak Evaluation Pipeline
대형 언어 모델(LLM)의 Jailbreak 공격 대응 성능 평가 및 비교 연구를 위한 자동화 파이프라인입니다.

## 🚀 시작하기 (Quick Start)

본 프로젝트는 Python 3.14+ 환경에서 최적화되어 있습니다. 아래 단계를 순서대로 진행하여 실험 환경을 구축하세요.

### 1. 환경 설정 및 의존성 설치
```powershell
# 프로젝트 복제
git clone [https://github.com/사용자명/프로젝트명.git](https://github.com/사용자명/프로젝트명.git)
cd 프로젝트명

# 가상환경 생성 및 활성화
py -m venv venv
.\venv\Scripts\activate

# 필수 라이브러리 설치
pip install -r requirements.txt
2. 환경 변수 설정
.env.example 파일을 복사하여 .env 파일을 생성하고, 본인의 DB 정보 및 API Key를 입력합니다.

[.env 설정 예시]

Plaintext
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=jailbreak_eval

# LLM API Keys
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
3. 데이터베이스 및 데이터 초기화
설계된 스키마를 적용하고 실험용 데이터셋(300건)을 DB에 로드합니다.

PowerShell
# 1. 테이블 생성 (src/database/schema.sql 적용)
py src/database/setup_db.py

# 2. 데이터셋 로드 (Jailbreak_dataset.csv -> MySQL)
py src/ingestion/load_data.py
📂 프로젝트 구조 (Project Structure)
src/database/: DB 스키마 설계 및 초기화 관리 (schema.sql, setup_db.py)

src/ingestion/: 데이터셋 전처리 및 DB 적재 모듈 (load_data.py)

src/evaluation/: LLM 비동기 호출 및 성능 지표 측정 모듈

data/raw/: 원본 데이터셋 (CSV) 관리 폴더

📊 주요 실험 지표 (Metrics)
Judgment: Hard Refusal, Soft Refusal, Success 여부 판정

Latency: 모델별 응답 속도(초) 측정

Token Usage: 비용 효율성 분석을 위한 토큰 사용량 기록

Created At: 실험 수행 시간 자동 기록