# ⛏️ Minecraft Server Monitoring & Bot System

마인크래프트 서버의 상태를 모니터링하고, 디스코드 봇을 통해 서버를 관리하며, 플레이어 통계를 제공하는 통합 시스템입니다.

## 🏗️ 아키텍처

이 프로젝트는 Docker Compose를 사용하여 5개의 컨테이너를 유기적으로 연결합니다.

1.  **Minecraft Server**: PaperMC 기반의 마인크래프트 서버.
2.  **Prometheus**: 서버 성능 데이터(TPS, RAM 등) 수집.
3.  **Grafana**: 수집된 데이터를 시각화하는 대시보드.
4.  **PostgreSQL**: 플레이어 통계(킬, 데스 등) 영구 저장.
5.  **Bot Server (FastAPI + Discord.py)**:
    *   **Alert Webhook**: Prometheus에서 이상 징후 감지 시 알림 수신.
    *   **RCON Client**: 디스코드 명령어로 서버 제어 (Kick, Ban, Whitelist).
    *   **Log Parser**: 실시간 로그 분석 및 DB 저장.
    *   **Leaderboard**: DB 데이터를 기반으로 랭킹 조회.

## 🚀 설치 및 실행 방법

### 1. 필수 요구 사항
*   Docker & Docker Compose

### 2. 환경 설정 (.env)
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 채워주세요.
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 3. 실행
```bash
docker-compose up -d --build
```
*   `--build`: 봇 서버 이미지를 빌드하기 위해 처음 실행 시 필수입니다.

### 4. 접속 정보
*   **Minecraft Server**: `localhost:25565`
*   **Grafana**: `localhost:3000` (ID: admin / PW: admin)
*   **Prometheus**: `localhost:29090`
*   **Bot Server API**: `localhost:8000`

## 🎮 사용법 (Discord 명령어)

### 관리자 명령어
*   `!say [메시지]`: 서버 전체에 공지 메시지를 보냅니다.
*   `!kick [플레이어] [사유]`: 플레이어를 추방합니다.
*   `!whitelist add [플레이어]`: 화이트리스트에 추가합니다.

### 일반 명령어
*   `!ping`: 봇 상태 확인 (Pong!).
*   `!health`: 봇 헬스체크 및 지연 시간 확인.
*   `!leaderboard [deaths|kills]`: 사망/킬 랭킹을 확인합니다. (예: `!lb deaths`)

## 📂 디렉토리 구조
```
.
├── bot/                # 봇 서버 소스코드
│   ├── cogs/           # 디스코드 명령어 모듈 (Admin, Stats)
│   ├── core/           # 핵심 로직 (DB, RCON, Config, LogParser)
│   ├── main.py         # FastAPI 및 봇 진입점
│   └── Dockerfile      # 봇 서버 도커 이미지 정의
├── prometheus/         # 모니터링 설정
├── docker-compose.yml  # 전체 시스템 구성
└── .env                # 환경 변수 (토큰 등)
```

## ⚠️ 주의사항
*   **RCON 보안**: `docker-compose.yml`의 `RCON_PASSWORD`를 반드시 변경하고 `.env` 등 안전한 곳에서 관리하세요.
*   **로그 파싱**: `LogParser`는 `latest.log`의 텍스트 패턴을 분석합니다. 플러그인이나 서버 버전에 따라 로그 형식이 다를 수 있으므로 `bot/core/log_parser.py`의 정규표현식 수정이 필요할 수 있습니다.
