# 🇦🇺 Brisbane Surfer Mate (텔레그램 영어 회화 봇)

이 프로젝트는 호주 브리즈번에 사는 30대 서퍼 **'Matt'**과 자유롭게 대화하며 영어 실력을 향상시킬 수 있는 텔레그램 봇입니다.

## 🌟 주요 기능
- **호주인 페르소나 적용:** 브리즈번 거주, 30대 서퍼 Matt과의 실감 나는 대화 (호주 슬랭 및 이모지 포함 🏄‍♂️🤙)
- **초보자 맞춤형 대화:** 쉬운 단어와 짧은 문장 위주로 대화 (A1-A2 수준)
- **듀얼 실시간 & 데일리 피드백:** 
    - **실시간 English Tips:** 대화 직후 틀린 문법이나 어색한 표현을 즉시 교정 (채팅 스타일인 소문자/마침표 생략 등은 쿨하게 무시!)
    - **데일리 리포트:** 매일 밤 11시 30분, 오늘 틀린 표현들을 모아서 한 번 더 복습 리포트 발송
- **능동적 상호작용 (선톡):** 1시간 이상 대화가 없을 때, 브리즈번 실시간 날씨 등을 소재로 Matt이 먼저 질문을 던짐
- **모바일 실행 지원:** 안드로이드 Termux 환경에서 봇을 띄우는 가이드 제공 ([mobile_guide.md](./mobile_guide.md))

## 🛠️ 설치 및 실행 (PC 기준)

### 1. 환경 준비
- Python 3.10 이상 설치 권장
- 텔레그램 봇 토큰 발급 (@BotFather)
- Gemini API 키 발급 ([Google AI Studio](https://aistudio.google.com/))

### 2. 패키지 설치
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성한 후 정보를 입력합니다.
- `TELEGRAM_BOT_TOKEN`: 발급받은 봇 토큰
- `GEMINI_API_KEY`: 발급받은 제미나이 API 키
- `TIMEZONE`: `Australia/Brisbane` (또는 원하는 지역)

### 4. 실행
```bash
python main.py
```

## 📂 파일 구조
- `main.py`: 텔레그램 봇 메인 실행부 및 스케줄러 설정
- `database.py`: SQLite 연동 (대화 기록 및 피드백 저장)
- `gemini_integration.py`: 제미나이 API 연동 및 Matt 페르소나 설정
- `scheduler_jobs.py`: 선톡 및 데일리 리포트 배치 작업 정의
- `weather_hook.py`: 브리즈번 실시간 날씨 데이터 수집 (wttr.in)
- `surfer_bot.db`: 대화 내역이 저장되는 로컬 데이터베이스 파일
