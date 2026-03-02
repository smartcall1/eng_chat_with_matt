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
PC에 있는 파일들을 옮기거나 Git을 통해 가져온 후 설치를 진행합니다.

```bash
# 가상환경 생성 및 진입
python -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

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
