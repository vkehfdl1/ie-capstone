"""Gradio application for the IE Capstone Experiment."""

from datetime import datetime

import gradio as gr

from ie_capstone.config import GOOGLE_FORM_URL, TOTAL_PROBLEMS
from ie_capstone.dataset.parser import load_all_problems
from ie_capstone.llm.client import ClaudeClient
from ie_capstone.llm.judge import LLMJudge
from ie_capstone.llm.socratic_lm import SocraticLM
from ie_capstone.logging.session_logger import SessionLogger
from ie_capstone.models import PersonaType


def get_persona_from_request(request: gr.Request) -> PersonaType:
    """Extract persona from URL query parameter."""
    if request and request.query_params:
        persona = request.query_params.get("persona", "neutral")
        if persona in ("neutral", "emotional"):
            return persona
    return "neutral"


def get_participant_id_from_request(request: gr.Request) -> str:
    """Extract participant ID from URL query parameter."""
    if request and request.query_params:
        return request.query_params.get("participant_id", "anonymous")
    return "anonymous"


def create_app() -> gr.Blocks:
    """
    Create Gradio app for the experiment.

    URL Parameters:
        ?persona=neutral or ?persona=emotional
        ?participant_id=XXX

    Returns:
        Gradio Blocks app
    """
    # Load problems
    problems = load_all_problems()

    # Initialize components (will be set per session)
    logger = SessionLogger()

    with gr.Blocks(
        title="IE Capstone 실험 - Python 디버깅",
    ) as app:
        # State variables
        state = gr.State({})

        # Header
        gr.Markdown("# Python 디버깅 실험")

        # Progress indicator
        progress_text = gr.Markdown("**진행 상황: 문제 1 / 6**")

        with gr.Row():
            # Left column: Problem and Code
            with gr.Column(scale=1):
                problem_display = gr.Markdown(
                    label="문제 설명",
                    value="문제를 불러오는 중...",
                )

                code_editor = gr.Code(
                    label="코드 (버그를 수정하세요)",
                    language="python",
                    lines=15,
                    interactive=True,
                )

                submit_btn = gr.Button(
                    "최종 답안 제출",
                    variant="primary",
                    size="lg",
                )

            # Right column: Chat
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="AI 튜터",
                    height=400,
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="메시지 입력",
                        placeholder="버그에 대해 질문하세요...",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("전송", variant="secondary", scale=1)

        # Results section (hidden initially)
        results_section = gr.Column(visible=False)
        with results_section:
            gr.Markdown("---")
            gr.Markdown("## 실험 완료!")
            results_display = gr.Markdown("결과가 여기에 표시됩니다...")
            gr.Markdown(f"**설문조사를 완료해주세요:** [설문조사 링크]({GOOGLE_FORM_URL})")

        # Feedback after submission
        feedback_display = gr.Markdown("")

        def initialize_session(request: gr.Request):
            """Initialize experiment session on page load."""
            persona = get_persona_from_request(request)
            participant_id = get_participant_id_from_request(request)

            # Create session
            session = logger.create_session(participant_id, persona)

            # Initialize Claude client and components
            client = ClaudeClient()
            judge = LLMJudge(client)
            socratic_lm = SocraticLM(client, persona, problems[0])

            # Get initial greeting
            greeting = socratic_lm.get_initial_greeting()
            logger.log_message(session, 1, "assistant", greeting)

            # Prepare initial state
            new_state = {
                "session": session,
                "client": client,
                "judge": judge,
                "socratic_lm": socratic_lm,
                "current_problem_idx": 0,
                "problems": problems,
            }

            # Format problem display
            problem = problems[0]
            problem_md = f"""### 문제 1

{problem.description}

**과제:** 아래 코드에서 버그를 찾아 수정하세요.
"""

            # Initial chat with greeting
            chat_history = [{"role": "assistant", "content": greeting}]

            return (
                new_state,
                f"**진행 상황: 문제 1 / {TOTAL_PROBLEMS}**",
                problem_md,
                problem.buggy_code,
                chat_history,
                "",
                gr.update(visible=False),
            )

        def handle_chat_submit(user_message: str, current_code: str, chat_history: list, state: dict):
            """Handle user message submission in chat with streaming."""
            if not user_message.strip():
                yield chat_history, state, ""
                return

            session = state["session"]
            socratic_lm = state["socratic_lm"]
            current_idx = state["current_problem_idx"]
            problem_id = current_idx + 1

            # Log user message with current code context
            log_content = f"[현재 코드]\n```python\n{current_code}\n```\n\n[메시지]\n{user_message}"
            logger.log_message(session, problem_id, "user", log_content)

            # Add user message to chat history immediately
            chat_history = [
                *chat_history,
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ""},
            ]

            # Stream response (pass current code to AI)
            full_response = ""
            for chunk in socratic_lm.stream_response(user_message, current_code):
                full_response += chunk
                chat_history[-1]["content"] = full_response
                yield chat_history, state, ""

            # Log assistant response after streaming completes
            logger.log_message(session, problem_id, "assistant", full_response)

            # Save session after each message
            logger.save_session(session)

            yield chat_history, state, ""

        def handle_code_submit(code: str, chat_history: list, state: dict):
            """Handle final code submission for current problem."""
            session = state["session"]
            judge = state["judge"]
            problems_list = state["problems"]
            current_idx = state["current_problem_idx"]
            problem = problems_list[current_idx]
            problem_id = current_idx + 1

            # Evaluate the fix
            is_correct, scores = judge.evaluate_fix(problem, code)

            # Log final submission
            logger.log_final_submission(session, problem_id, code, is_correct, scores)

            # Save session
            logger.save_session(session)

            # Prepare feedback
            if is_correct:
                feedback = f"### 문제 {problem_id} 완료!\n\n제출한 코드가 **정답**으로 평가되었습니다."
            else:
                feedback = f"### 문제 {problem_id} 완료!\n\n제출한 코드가 **오답**으로 평가되었습니다."

            # Check if this was the last problem
            if current_idx >= TOTAL_PROBLEMS - 1:
                # Experiment complete
                session.end_time = datetime.now()
                logger.save_session(session)

                results_md = generate_results_summary(session)

                return (
                    state,
                    feedback,
                    gr.update(visible=True),
                    results_md,
                    "**진행 상황: 완료!**",
                    gr.update(interactive=False),
                    gr.update(interactive=False),
                    gr.update(interactive=False),
                    chat_history,
                    code,
                )

            # Move to next problem
            next_idx = current_idx + 1
            next_problem = problems_list[next_idx]
            state["current_problem_idx"] = next_idx

            # Update Socratic LM for new problem
            state["socratic_lm"].set_problem(next_problem)

            # Get new greeting
            new_greeting = state["socratic_lm"].get_initial_greeting()
            logger.log_message(session, next_idx + 1, "assistant", new_greeting)

            # New chat history
            new_chat = [{"role": "assistant", "content": new_greeting}]

            # Format new problem
            problem_md = f"""### 문제 {next_idx + 1}

{next_problem.description}

**과제:** 아래 코드에서 버그를 찾아 수정하세요.
"""

            return (
                state,
                feedback + f"\n\n**문제 {next_idx + 1}로 이동합니다...**",
                gr.update(visible=False),
                "",
                f"**진행 상황: 문제 {next_idx + 1} / {TOTAL_PROBLEMS}**",
                problem_md,
                next_problem.buggy_code,
                new_chat,
            )

        def generate_results_summary(session) -> str:
            """Generate final results summary."""
            success_rate = session.success_rate
            avg_turns = session.average_turns
            total_correct = sum(1 for a in session.problem_attempts if a.is_correct)

            results = f"""
### 실험 결과

| 항목 | 값 |
|------|-----|
| 정답 문제 수 | {total_correct} / {TOTAL_PROBLEMS} |
| 정답률 | {success_rate:.1%} |
| 평균 대화 턴 수 | {avg_turns:.1f} |

---

**세션 ID:** `{session.session_id}`

실험에 참여해 주셔서 감사합니다!
"""
            return results

        # Event handlers
        app.load(
            initialize_session,
            inputs=[],
            outputs=[
                state,
                progress_text,
                problem_display,
                code_editor,
                chatbot,
                feedback_display,
                results_section,
            ],
        )

        # Chat submission
        send_btn.click(
            handle_chat_submit,
            inputs=[msg_input, code_editor, chatbot, state],
            outputs=[chatbot, state, msg_input],
        )

        msg_input.submit(
            handle_chat_submit,
            inputs=[msg_input, code_editor, chatbot, state],
            outputs=[chatbot, state, msg_input],
        )

        # Code submission with multiple outputs based on whether experiment is complete
        submit_btn.click(
            handle_code_submit,
            inputs=[code_editor, chatbot, state],
            outputs=[
                state,
                feedback_display,
                results_section,
                results_display,
                progress_text,
                problem_display,
                code_editor,
                chatbot,
            ],
        )

    return app


def main():
    """Run the Gradio app."""
    app = create_app()
    app.launch(
        server_name="0.0.0.0",  # noqa: S104
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
