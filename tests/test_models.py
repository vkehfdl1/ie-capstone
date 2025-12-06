"""Tests for data models."""

from datetime import datetime

from ie_capstone.models import (
    ExperimentSession,
    Message,
    Problem,
    ProblemAttempt,
)


class TestProblem:
    def test_create_problem(self):
        problem = Problem(
            id=1,
            description="Test problem",
            buggy_code="def foo(): pass",
            bug_description="Missing return",
            expected_fixes=["Add return statement"],
            unit_tests=["assert foo() == 1"],
        )
        assert problem.id == 1
        assert problem.description == "Test problem"
        assert problem.buggy_code == "def foo(): pass"
        assert problem.bug_description == "Missing return"
        assert problem.expected_fixes == ["Add return statement"]
        assert problem.unit_tests == ["assert foo() == 1"]
        assert problem.example_dialogue == ""

    def test_problem_with_example_dialogue(self):
        problem = Problem(
            id=1,
            description="Test",
            buggy_code="code",
            bug_description="bug",
            expected_fixes=["fix"],
            unit_tests=["test"],
            example_dialogue="User: Hi\nAssistant: Hello",
        )
        assert problem.example_dialogue == "User: Hi\nAssistant: Hello"


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message(self):
        msg = Message(role="assistant", content="How can I help?")
        assert msg.role == "assistant"
        assert msg.content == "How can I help?"

    def test_message_with_custom_timestamp(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        msg = Message(role="user", content="Test", timestamp=ts)
        assert msg.timestamp == ts


class TestProblemAttempt:
    def test_create_empty_attempt(self):
        attempt = ProblemAttempt(problem_id=1)
        assert attempt.problem_id == 1
        assert attempt.conversation_history == []
        assert attempt.final_code == ""
        assert attempt.is_correct is None
        assert attempt.judge_scores == []
        assert attempt.turn_count == 0

    def test_turn_count_with_messages(self):
        attempt = ProblemAttempt(
            problem_id=1,
            conversation_history=[
                Message(role="user", content="Q1"),
                Message(role="assistant", content="A1"),
                Message(role="user", content="Q2"),
                Message(role="assistant", content="A2"),
                Message(role="user", content="Q3"),
            ],
        )
        assert attempt.turn_count == 3

    def test_attempt_with_result(self):
        attempt = ProblemAttempt(
            problem_id=1,
            final_code="def foo(): return 1",
            is_correct=True,
            judge_scores=[1.0, 1.0, 1.0],
        )
        assert attempt.is_correct is True
        assert attempt.judge_scores == [1.0, 1.0, 1.0]


class TestExperimentSession:
    def test_create_session(self):
        session = ExperimentSession(
            session_id="test-123",
            participant_id="P001",
            persona="neutral",
            start_time=datetime.now(),
        )
        assert session.session_id == "test-123"
        assert session.participant_id == "P001"
        assert session.persona == "neutral"
        assert session.end_time is None
        assert session.problem_attempts == []
        assert session.current_problem_index == 0

    def test_success_rate_no_attempts(self):
        session = ExperimentSession(
            session_id="test",
            participant_id="P001",
            persona="emotional",
            start_time=datetime.now(),
        )
        assert session.success_rate == 0.0

    def test_success_rate_with_attempts(self):
        session = ExperimentSession(
            session_id="test",
            participant_id="P001",
            persona="neutral",
            start_time=datetime.now(),
            problem_attempts=[
                ProblemAttempt(problem_id=1, is_correct=True),
                ProblemAttempt(problem_id=2, is_correct=True),
                ProblemAttempt(problem_id=3, is_correct=False),
                ProblemAttempt(problem_id=4, is_correct=None),  # Not completed
            ],
        )
        # 2 correct out of 3 completed
        assert session.success_rate == 2 / 3

    def test_average_turns_no_attempts(self):
        session = ExperimentSession(
            session_id="test",
            participant_id="P001",
            persona="neutral",
            start_time=datetime.now(),
        )
        assert session.average_turns == 0.0

    def test_average_turns_with_attempts(self):
        session = ExperimentSession(
            session_id="test",
            participant_id="P001",
            persona="neutral",
            start_time=datetime.now(),
            problem_attempts=[
                ProblemAttempt(
                    problem_id=1,
                    is_correct=True,
                    conversation_history=[
                        Message(role="user", content="Q1"),
                        Message(role="assistant", content="A1"),
                        Message(role="user", content="Q2"),
                        Message(role="assistant", content="A2"),
                    ],
                ),
                ProblemAttempt(
                    problem_id=2,
                    is_correct=True,
                    conversation_history=[
                        Message(role="user", content="Q1"),
                        Message(role="assistant", content="A1"),
                    ],
                ),
            ],
        )
        # (2 + 1) / 2 = 1.5
        assert session.average_turns == 1.5
