"""Tests for Session Logger."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ie_capstone.logging.session_logger import SessionLogger


@pytest.fixture
def temp_logs_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSessionLogger:
    def test_initialization_creates_directory(self, temp_logs_dir):
        logs_dir = temp_logs_dir / "sessions"
        assert not logs_dir.exists()

        logger = SessionLogger(logs_dir=logs_dir)

        assert logs_dir.exists()
        assert logger.logs_dir == logs_dir

    def test_create_session(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)

        session = logger.create_session("P001", "neutral")

        assert "P001" in session.session_id
        assert session.participant_id == "P001"
        assert session.persona == "neutral"
        assert isinstance(session.start_time, datetime)
        assert session.end_time is None
        assert session.problem_attempts == []

    def test_create_session_emotional_persona(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)

        session = logger.create_session("P002", "emotional")

        assert session.persona == "emotional"

    def test_log_message_creates_attempt(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        logger.log_message(session, problem_id=1, role="user", content="Hello")

        assert len(session.problem_attempts) == 1
        assert session.problem_attempts[0].problem_id == 1
        assert len(session.problem_attempts[0].conversation_history) == 1

    def test_log_message_appends_to_existing_attempt(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        logger.log_message(session, problem_id=1, role="user", content="Question 1")
        logger.log_message(session, problem_id=1, role="assistant", content="Answer 1")
        logger.log_message(session, problem_id=1, role="user", content="Question 2")

        assert len(session.problem_attempts) == 1
        assert len(session.problem_attempts[0].conversation_history) == 3

    def test_log_message_multiple_problems(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        logger.log_message(session, problem_id=1, role="user", content="P1 Q1")
        logger.log_message(session, problem_id=2, role="user", content="P2 Q1")
        logger.log_message(session, problem_id=1, role="assistant", content="P1 A1")

        assert len(session.problem_attempts) == 2
        p1 = next(a for a in session.problem_attempts if a.problem_id == 1)
        p2 = next(a for a in session.problem_attempts if a.problem_id == 2)
        assert len(p1.conversation_history) == 2
        assert len(p2.conversation_history) == 1

    def test_log_final_submission(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        logger.log_message(session, problem_id=1, role="user", content="Help")
        logger.log_final_submission(
            session,
            problem_id=1,
            final_code="def foo(): return 1",
            is_correct=True,
            judge_scores=[1.0, 1.0, 1.0],
        )

        attempt = session.problem_attempts[0]
        assert attempt.final_code == "def foo(): return 1"
        assert attempt.is_correct is True
        assert attempt.judge_scores == [1.0, 1.0, 1.0]

    def test_save_and_load_session(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        logger.log_message(session, problem_id=1, role="user", content="Test")
        logger.log_final_submission(session, problem_id=1, final_code="code", is_correct=True, judge_scores=[1.0])

        saved_path = logger.save_session(session)

        assert saved_path.exists()
        loaded = logger.load_session(session.session_id)

        assert loaded["session_id"] == session.session_id
        assert loaded["participant_id"] == "P001"
        assert loaded["persona"] == "neutral"
        assert len(loaded["problem_attempts"]) == 1

    def test_session_to_dict_structure(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "emotional")

        logger.log_message(session, problem_id=1, role="user", content="Q1")
        logger.log_message(session, problem_id=1, role="assistant", content="A1")
        logger.log_final_submission(
            session,
            problem_id=1,
            final_code="fixed code",
            is_correct=True,
            judge_scores=[1.0, 1.0, 0.0],
        )

        result = logger._session_to_dict(session)

        assert "session_id" in result
        assert "participant_id" in result
        assert "persona" in result
        assert "start_time" in result
        assert "metrics" in result
        assert "success_rate" in result["metrics"]
        assert "average_turns" in result["metrics"]
        assert "problem_attempts" in result

        attempt = result["problem_attempts"][0]
        assert "problem_id" in attempt
        assert "final_code" in attempt
        assert "is_correct" in attempt
        assert "judge_scores" in attempt
        assert "turn_count" in attempt
        assert "conversation_history" in attempt

    def test_get_session_file_path(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)

        path = logger.get_session_file_path("test-session-123")

        assert path == temp_logs_dir / "test-session-123.json"

    def test_saved_json_is_valid(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")
        logger.log_message(session, problem_id=1, role="user", content="Test message")

        saved_path = logger.save_session(session)

        # Read raw file and parse JSON
        with open(saved_path) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert data["participant_id"] == "P001"

    def test_metrics_calculated_correctly(self, temp_logs_dir):
        logger = SessionLogger(logs_dir=temp_logs_dir)
        session = logger.create_session("P001", "neutral")

        # Problem 1: 2 turns, correct
        logger.log_message(session, 1, "user", "Q1")
        logger.log_message(session, 1, "assistant", "A1")
        logger.log_message(session, 1, "user", "Q2")
        logger.log_message(session, 1, "assistant", "A2")
        logger.log_final_submission(session, 1, "code1", True, [1.0])

        # Problem 2: 1 turn, incorrect
        logger.log_message(session, 2, "user", "Q1")
        logger.log_message(session, 2, "assistant", "A1")
        logger.log_final_submission(session, 2, "code2", False, [0.0])

        result = logger._session_to_dict(session)

        assert result["metrics"]["success_rate"] == 0.5  # 1 out of 2
        assert result["metrics"]["average_turns"] == 1.5  # (2 + 1) / 2
