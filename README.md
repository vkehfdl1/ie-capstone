# IE Capstone - 소크라틱 LM 실험 시스템

Python 디버깅을 위한 소크라틱 학습 방식의 AI 튜터 실험 시스템입니다.
챗봇 페르소나(중립적 vs 감정적)에 따른 학습 효과를 연구합니다.

## 프로젝트 개요

### 연구 주제
> 소크라틱 LM에서 챗봇의 페르소나에 따른 정서적 영향이 있을까?

### 실험 설계
- **문제**: Python 코드 버그 수정 (6문제)
- **페르소나**:
  - `neutral`: 중립적 (3인칭, 격식체, 이모티콘 없음)
  - `emotional`: 감정적 (2인칭, 친근함, 이모티콘 사용)
- **평가 지표**: 성공률, 평균 턴 수, 정성 평가 (설문조사)

### 주요 기능
- Gradio 기반 실험 UI
- 실시간 스트리밍 AI 응답
- Claude API (claude-opus-4-5-20251101) 사용
- LLM-as-a-Judge로 정답 평가 (self-consistency 3회)
- JSON 기반 세션 로깅

## 설치 방법

### 요구사항
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ie-capstone
```

### 2. 의존성 설치
```bash
uv sync
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성 또는 환경 변수 설정
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 4. 실행
```bash
uv run python -m ie_capstone.app.gradio_app
```

브라우저에서 `http://localhost:7860` 접속

## 사용 방법

### URL 파라미터
```
http://localhost:7860?persona=neutral&participant_id=참가자ID
http://localhost:7860?persona=emotional&participant_id=참가자ID
```

| 파라미터 | 값 | 설명 |
|---------|-----|------|
| `persona` | `neutral` / `emotional` | 챗봇 페르소나 (기본: neutral) |
| `participant_id` | 문자열 | 참가자 식별자 (기본: anonymous) |

### 실험 흐름
1. URL로 페르소나/참가자 설정 후 접속
2. 6개의 Python 버그 수정 문제를 순차적으로 풀이
3. AI 튜터와 대화하며 버그 찾기
4. 코드 수정 후 "최종 답안 제출" 클릭
5. 6문제 완료 후 결과 확인 및 설문조사

## 개발

### 테스트 실행
```bash
uv run pytest -v
```

### 린팅 & 타입 체크
```bash
make check
```

### 의존성 추가
```bash
uv add <package-name>
```

## 로그 데이터

세션 로그는 `logs/sessions/` 디렉토리에 JSON 형식으로 저장됩니다.

```json
{
  "session_id": "참가자ID_날짜_시간_uuid",
  "participant_id": "참가자ID",
  "persona": "neutral",
  "start_time": "2025-12-06T20:00:00",
  "end_time": "2025-12-06T20:30:00",
  "metrics": {
    "success_rate": 0.833,
    "average_turns": 4.5
  },
  "problem_attempts": [...]
}
```

## 기술 스택

- **프레임워크**: Gradio
- **LLM**: Claude claude-opus-4-5-20251101 (Anthropic API)
- **패키지 관리**: uv
- **린터**: ruff
- **타입 체커**: ty
- **테스트**: pytest

## 참고 문헌

- Kargupta et al. "Instruct, Not Assist: LLM-based Multi-Turn Planning and Hierarchical Questioning for Socratic Code Debugging" (EMNLP 2024)
- Pezenka et al. "Emotionality in Task-Oriented Chatbots–The Effect of Emotion Expression on Chatbot Perception" (Communication Studies, 2024)

## 라이선스

MIT License
