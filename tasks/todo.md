# 텔레그램 영어 회화 봇 (Brisbane Surfer Mate) 프로젝트 계획

## 1. 프로젝트 개요
* **목표:** 능동적이고 구체적인 페르소나(호주 브리즈번 30대 남성)를 가진 텔레그램 기반 영어 회화 봇 개발
* **기술 스택:** Python, `python-telegram-bot`, Google Gemini API, SQLite, APScheduler

## 2. 할 일 목록 (To-Do)

### Phase 1: 기본 셋업 및 구조 설계
- [x] 프로젝트 초기 요구사항 분석 및 방향 설정
- [x] 파이썬 프로젝트 환경 설정 (가상환경, `requirements.txt`)
- [x] 텔레그램 봇 토큰 발급 및 `.env` 파일 세팅 
- [x] 메인 아키텍처 및 봇 골격 작성 (`main.py`)

### Phase 2: 페르소나 및 대화 컨텍스트 관리
- [x] System Prompt 정교화 (브리즈번 거주, 서퍼, 호주 슬랭, 교정 지침)
- [x] SQLite Database 셋업 (유저 정보, 대화 기록 저장용)
- [x] 효율적인 Context Window 로직 구현 (최근 대화 10회만 기억하여 토큰 절약)
- [ ] 기본 메시지 수발신 및 Gemini API 연동 테스트

### Phase 3: 능동적 상호작용 (Proactive Messaging)
- [x] 유저 마지막 응답 시간 기록 로직 구축
- [x] 1시간 무응답 시 대화 세션 분리(새로운 세션 시작 가능 상태) 처리
- [x] APScheduler 연동 (08:00 ~ 23:00 사이, 일 5회 랜덤 메시지 트리거)
- [x] 실시간 날씨/뉴스 API 연동 (먼저 대화 걸 때 소재로 활용하여 자연스러움 극대화)

### Phase 4: 학습 피드백 및 데일리 요약
- [x] 대화 중 발생하는 문장 교정 내용 별도 DB 저장
- [x] 매일 밤(예: 23:30) 오늘의 교정/추천 표현 요약본 리포트 전송 (APScheduler 활용)

### Phase 5: 이미지 생성 및 전송 기능
- [ ] Matt이 대화 맥락에 맞는 이미지를 생성하는 로직 추가 (Imagen 3 등 활용)
- [ ] 텔레그램 `send_photo` 메서드 연동

### Phase 6: 퓨처 플랜 (Future Backlog)
- [ ] 보이스 메시지(TTS/STT) 지원 추가 (추후 구현)

## 3. 리뷰 및 회고
* (프로젝트 진행 및 완료 후 작성 예정)