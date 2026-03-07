# 📱 Termux 모바일 구동 가이드

안드로이드 스마트폰에 **Termux** 앱을 설치하여 PC 없이 24시간 봇을 구동하는 단계별 안내입니다.

## 1. Termux 기초 환경 설정
Termux를 실행하고 아래 명령어들을 순서대로 입력하세요.

```bash
# 패키지 업데이트
pkg update && pkg upgrade

# 필수 패키지 설치 (Python 및 Git)
pkg install python git

# 저장소 권한 획득 (선택 사항)
termux-setup-storage
```

## 2. 프로젝트 가져오기 및 설치
git clone https://github.com/smartcall1/eng_chat_with_matt.git

```bash
# 가상환경 생성 및 진입
python -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 💡 시스템 패키지(`pkg`) vs 가상환경(`venv`) 구분하기
David, 이 부분이 헷갈릴 수 있는데 아주 중요한 포인트야! 구조를 이렇게 이해하면 쉬워:

1.  **시스템 패키지 (`pkg install ...`):**
    *   이건 휴대폰(Termux 시스템) 전체에 까는 거야.
    *   **도구(Rust, C 컴파일러)**나 **시스템 라이브러리(OpenSSL, libffi)** 같은 녀석들은 무조건 여기서 **범용(글로벌)**으로 깔아야 해. 가상환경은 이런 '망치와 못'같은 도구들을 직접 가질 수 없거든.
    *   `python-cryptography`를 여기서 까는 이유는, 안드로이드용으로 미리 빌드된 '완제품'을 가져오기 위해서야.

2.  **가상환경 패키지 (`pip install ...`):**
    *   `venv` 안으로 들어가서 (`source venv/bin/activate`) 설치하는 건 이 프로젝트 전용이야.
    *   `Gradio`, `google-genai` 같은 파이썬 라이브러리들은 **가상환경 안에** 까는 게 정석이야. 그래야 다른 프로젝트랑 꼬이지 않거든.

**결론적으로:** 
*   **'빌드 도구'**(rust, binutils)는 **밖에서 미리** 범용으로 깔고,
*   **'파이썬 패키지'**(gradio, httpx 등)는 **가상환경 안에서** 까는 게 맞아!

---

### ⚠️ 자주 발생하는 오류 및 해결 방법

#### 1. `cryptography` 설치 오류 해결 (빌드 도구 필수)
Termux 환경은 PC와 달리 `cryptography` 같은 라이브러리를 설치할 때 직접 빌드(Compile)해야 하는 경우가 많아요. 이때 Rust나 C 컴파일러가 없으면 100% 실패합니다.

**가장 확실한 해결 순서:**
```bash
# 1. 빌드 도구 및 라이브러리 일괄 설치
pkg update
pkg install -y binutils rust python-cryptography lld libffi openssl

# 2. 환경 변수 설정 (컴파일러에게 안드로이드 환경임을 알림)
export ANDROID_API_LEVEL=24

# 3. pip로 cryptography 설치 시도
pip install cryptography
```

#### 2. `Gradio` 또는 `google-genai` 설치 시 의존성 충돌
`Gradio`나 `google-genai`를 설치할 때 `anyio`, `pydantic` 같은 라이브러리가 줄줄이 에러를 낸다면 아래 명령어로 **필수 의존성들을 한꺼번에 먼저 설치**해야 합니다.

```bash
# 의존성 패키지 강제 일괄 설치
pip install anyio httpx pydantic requests typing-extensions websockets
```

그 후 다시 원래 설치하려던 패키지를 설치하세요:
```bash
pip install -r requirements.txt
# 또는
pip install gradio google-genai
```

#### 3. `ModuleNotFoundError: No module named 'tzdata'`
봇 실행 시 스케줄러(APScheduler)가 타임존 데이터를 찾지 못해 발생하는 에러입니다.

```bash
# tzdata 패키지 설치
pip install tzdata
```

그 후 다시 실행해 보세요:
```bash
python main.py
```

> [!IMPORTANT]
> **왜 계속 실패할까요?**
> Termux의 파이썬 환경과 안드로이드 시스템 라이브러리 버전이 안 맞아서 발생하는 경우가 많습니다. 위처럼 `pkg install python-cryptography`를 통해 Termux 팀이 미리 빌드해둔 버전을 먼저 깔아주는 것이 가장 똑똑한 방법입니다.

## 3. 백그라운드 상시 구동 (중요)
Termux가 안드로이드 시스템에 의해 강제 종료되지 않도록 설정해야 합니다.

1. **Battery Optimization 제외:** 휴대폰 설정 -> 애플리케이션 -> Termux -> 배터리 -> '제한 없음' 또는 '최적화 제외'로 설정
2. **Termux-wake-lock:** Termux 알림창을 내려서 'Acquire wake-lock'을 누르거나, 터미널에 아래 명령어 입력
   ```bash
   termux-wake-lock
   ```

## 4. 봇 실행 및 관리
```bash
# 실행
python main.py

# 세션 유지하며 실행 (추천)
# 세션 관리를 위해 screen이나 tmux를 사용하면 더 좋습니다.
pkg install tmux
tmux new -s bot_session
python main.py
# (나갈 때: Ctrl+B 누른 뒤 D)
# (다시 들어올 때: tmux attach -t bot_session)
```

## ⚠️ 주의사항
- **네트워크 연결:** 봇은 인터넷이 연결된 상태에서만 작동합니다. 와이파이가 안정적인 곳에서 공기계를 충전기에 연결해두는 것이 좋습니다.
- **발열 관리:** 장기간 구동 시 폰이 뜨거워질 수 있으니 통풍이 잘 되는 곳에 두세요.
