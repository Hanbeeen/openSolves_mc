# 최근 변경 사항 요약

최근 리포지토리에 푸시된 변경 사항들을 최신순으로 정리한 요약입니다.

## 1. Grafana & Discord 대시보드 연동
**커밋:** `2acc3e0` - `grafana <-> discord 대시보드 연결`
- **설명:** Grafana와 Discord 간의 대시보드 시각화 연동을 구현했습니다.
- **주요 변경 파일:**
  - `bot/cogs/grafana.py`: Discord 봇용 Grafana Cog 추가.
  - `bot/main.py`: 새로운 Grafana Cog 등록.
  - `bot/requirements.txt`: 의존성 라이브러리 추가.
  - `docker-compose.yml`: 서비스 설정 업데이트.
  - `prometheus/prometheus.yml`: 모니터링 타겟 업데이트.

## 2. Minecraft 서버 데이터 업데이트
**커밋:** `1337201` - `chore: Minecraft 서버 플레이어 활동 및 월드 데이터 업데이트`
- **설명:** 월드 데이터 및 플레이어 활동 로그의 정기 업데이트입니다.
- **주요 변경 파일:**
  - `mc-data/`: 바이너리 월드 데이터 업데이트 (level.dat, region 파일 등).

## 3. Minecraft 버전 및 설정 업데이트
**커밋:** `df69f5b` - `feat: Minecraft 버전 업데이트, 서버 설정 및 무시 규칙 변경, 세계 데이터 수정`
- **설명:** Minecraft 서버 버전을 업데이트하고, 서버 설정 및 gitignore 규칙을 조정했습니다.
- **주요 변경 파일:**
  - `docker-compose.yml`: 이미지 태그 또는 환경 변수 업데이트 추정.
  - `.gitignore`: 무시 규칙 개선.
  - `prometheus/prometheus.yml`: 설정 조정.
  - `mc-data/`: 월드 데이터 마이그레이션/업데이트.

## 4. 초기 프로젝트 설정
**커밋:** `f78fabb` - `feat: 마인크래프트 서버, 디스코드 봇 및 프로메테우스 모니터링 초기 설정 파일들을 추가`
- **설명:** Minecraft 서버, Discord 봇, Prometheus 모니터링을 포함한 프로젝트 구조의 초기 커밋입니다.
- **주요 추가 파일:**
  - `bot/`: 봇 전체 소스 코드 (`main.py`, `cogs/`, `core/`).
  - `docker-compose.yml`: 기본 컨테이너 오케스트레이션 파일.
  - `prometheus/prometheus.yml`: 초기 모니터링 설정.
  - `README.md`: 프로젝트 문서.

## 5. 기타 수정 사항
**커밋:** `13f729e` - `fix: .gitignore에 .env 추가`
- **설명:** 보안을 위해 `.env` 파일을 `.gitignore`에 추가했습니다.

**커밋:** `483959c` - `git init`
- **설명:** 리포지토리 초기화.
