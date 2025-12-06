  You are making the expeirment suite for my IE capston project.
The project description is below.

# IE Capstone Experiment

# 실험 계획 초안

주제 : 소크라틱 LM에서 챗봇의 페르소나에 따른 정서적 영향이 있을까?

학생이 풀게 되는 문제 상황 : Python 코딩 문제의 버그 수정.
(Instruct, Not Assist 논문 차용)
Socratic Debugging Benchmark, MULTI-DEBUG 데이터셋 활용.

서로 다른 페르소나의 챗봇:

- 중립적 챗봇 : 3인칭. 정중하지만 딱딱한 표현. 이모티콘 없음. 사실적인 페르소나.
- 감정적 챗봇 : 긍정적인 텍스트. 유머, 감정표현. 이모티콘 등으로 친근함을 주도록 함.
(Pezenka et al., 2024)

## 실험 세팅

### 능력 레벨에 따른 분류

- Python을 몇 달 간 배운 초급 프로그래머 (원준, 주환)
- Python을 자주 사용하지 않는 비전공자지만 기본 개념은 이해 (성민,
- Python을 2년 이상 사용한 컴퓨터 과학 전공 학부 고학년생 혹은 유사한 수준의 코딩 실력 (동규,

각 레벨 당 2명의 피험자 배치. 각 피험자에게 무작위로 중립적 챗봇 혹은 감정적 챗봇을 사용하게 함.
(집단 간 설계)

한 피험자 당 총 6문제의 버그 수정 태스크를 풀게 하고, 6문제의 평균치를 최종 결과로 사용.

각 챗봇 당 총합 18번의 AI-사람 상호작용에 대해 평가하도록 설계됨. (총합 36번의 AI-사람 상호작용 평가)

## 메트릭

- 성공률
    - **학생이 최종적으로 버그를 올바르게 수정했는가**를 측정.
    학생이 제안한 버그 수정 사항(BS)과 정답 버그 수정 사항(BGT)이 동일한지 판단, 전체 정답 버그 수정 사항 중 학생이 제안한 버그 수정 사항의 비율임.
    - Claude-4.5-opus 모델을 이용하여 판단.
    - self-consistency를 위하여 3번 판단을 실행한 후 평균값을 최종 값으로 사용.
- 평균 턴수
    - 마지막 정답에 도달하기 까지 필요한 평균 대화 턴 수, AI와 인간 상호작용의 효율성을 나타냄.
- 정성 평가 (이것이 핵심)
    - 모든 문제를 푼 뒤 설문조사를 통해 신뢰도, 만족도, 즐거움, 진정성의 변수를 리커트 척도(1~5스케일의 설문조사)로 평가. (추가해야 함. 소크라틱 LM에 관련한 지표 ex. 동기 부여를 받았는가? )
- 10명+ 더하기

## 참고 문헌

- Instruct, Not Assist:
LLM-based Multi-Turn Planning and Hierarchical Questioning for Socratic Code Debugging, Kargupta et al., University of Illinois at Urbana-Champaign, EMNLP 2024
- “Emotionality in Task-Oriented Chatbots–The Effect of Emotion
Expression on Chatbot Perception." Pezenka, Ilona, et al. Communication Studies 75.6 (2024): 825-843.

[설문 참고 논문](https://www.notion.so/2bcc7b6bc1818098b11fd3ba6873f174?pvs=21)

[설문 문항 초안](https://www.notion.so/2bec7b6bc181802aaefaef563206fba3?pvs=21)


# Project Structure

It contains the python library code, which contains Socratic LM for python debugging problem, the datasets (Six problems),
the experiment suite made with Gradio. The form for survey is not included (We use Google Forms).

The main thing is Gradio app. The user access there, check the Python problem, and chat with Socratic LM chatbot to solve the problem.
It records all conversation logs and timestamps.

Also, it contains Socratic LM code. This is not fancy structure, but well prompt-engineered Agent using Claude-4.5-opus model.
All LLM will be Claude-4.5-oups model and will use Claude Official API.

Claude Docs : https://platform.claude.com/docs/en/api/python/messages/create

You don't have to use external library like LlamaIndex, Langchain etc. Just use simple python code with requests to Claude API.

Finally, the LLM-as-a-judge to determine whether the user's proposed bug fix is correct or not.
It will show the results in the experiment suite after all 6 problems are solved.
Also, at the end of the experiment, the Google Form link will be contained.


# Things to know

- We use `uv` environment. Do not use conda, pip, or etc. Use `uv add` commands.
- All LLM calls should be done with Claude-4.5-opus model.
- Keep it Simple. Do not use Local DB (like SQLite), or external libraries for LLM orchestration.
- We use `pytest` for unit tests. Try to use plugins like `pytest-asyncio`, `pytest-mock`, and etc. if needed.
- Build test code first and then build the actual code. (Except for gradio-related codes)
- DO NOT MAKE TEST CODES FOR GRADIO APP. ONLY ACTUAL CODE.
- Use `make check` for linting and type checking.
- We use `ruff` linter and `ty` for type checking.
- Check linting and type checking errors after a feature has been added.
