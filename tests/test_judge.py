"""Tests for LLM Judge."""

from unittest.mock import MagicMock

import pytest

from ie_capstone.llm.judge import LLMJudge
from ie_capstone.models import Problem


@pytest.fixture
def sample_problem():
    return Problem(
        id=1,
        description="Write a search function",
        buggy_code="def search(x, seq):\n  if x < seq[i]:\n    return i",
        bug_description="Should use <= instead of <",
        expected_fixes=["Replace < with <="],
        unit_tests=["assert search(5, [5]) == 0"],
    )


@pytest.fixture
def mock_client():
    return MagicMock()


class TestLLMJudge:
    def test_initialization(self, mock_client):
        judge = LLMJudge(mock_client)
        assert judge.client == mock_client

    def test_single_evaluation_correct(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "CORRECT"
        judge = LLMJudge(mock_client)

        score = judge._single_evaluation(sample_problem, "def search(x): return 0")
        assert score == 1.0

    def test_single_evaluation_incorrect(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "INCORRECT"
        judge = LLMJudge(mock_client)

        score = judge._single_evaluation(sample_problem, "def search(x): return -1")
        assert score == 0.0

    def test_single_evaluation_handles_lowercase(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "correct"
        judge = LLMJudge(mock_client)

        score = judge._single_evaluation(sample_problem, "code")
        assert score == 1.0

    def test_single_evaluation_handles_extra_text(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "The answer is CORRECT."
        judge = LLMJudge(mock_client)

        score = judge._single_evaluation(sample_problem, "code")
        assert score == 1.0

    def test_single_evaluation_incorrect_takes_precedence(self, mock_client, sample_problem):
        # If response contains both words, INCORRECT should win
        mock_client.send_single_message.return_value = "INCORRECT, not CORRECT"
        judge = LLMJudge(mock_client)

        score = judge._single_evaluation(sample_problem, "code")
        assert score == 0.0

    def test_evaluate_fix_all_correct(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "CORRECT"
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "good code")

        assert is_correct is True
        assert scores == [1.0, 1.0, 1.0]
        assert mock_client.send_single_message.call_count == 3

    def test_evaluate_fix_all_incorrect(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "INCORRECT"
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "bad code")

        assert is_correct is False
        assert scores == [0.0, 0.0, 0.0]

    def test_evaluate_fix_mixed_results_majority_correct(self, mock_client, sample_problem):
        mock_client.send_single_message.side_effect = [
            "CORRECT",
            "INCORRECT",
            "CORRECT",
        ]
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "code")

        assert is_correct is True  # 2/3 = 0.67 >= 0.5
        assert scores == [1.0, 0.0, 1.0]

    def test_evaluate_fix_mixed_results_majority_incorrect(self, mock_client, sample_problem):
        mock_client.send_single_message.side_effect = [
            "INCORRECT",
            "CORRECT",
            "INCORRECT",
        ]
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "code")

        assert is_correct is False  # 1/3 = 0.33 < 0.5
        assert scores == [0.0, 1.0, 0.0]

    def test_evaluate_fix_custom_iterations(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "CORRECT"
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "code", iterations=5)

        assert is_correct is True
        assert len(scores) == 5
        assert mock_client.send_single_message.call_count == 5

    def test_evaluate_fix_uses_low_temperature(self, mock_client, sample_problem):
        mock_client.send_single_message.return_value = "CORRECT"
        judge = LLMJudge(mock_client)

        judge.evaluate_fix(sample_problem, "code", iterations=1)

        call_kwargs = mock_client.send_single_message.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3

    def test_evaluate_fix_edge_case_exactly_half(self, mock_client, sample_problem):
        # 2 out of 4 = 0.5, which should be correct (>= 0.5)
        mock_client.send_single_message.side_effect = [
            "CORRECT",
            "INCORRECT",
            "CORRECT",
            "INCORRECT",
        ]
        judge = LLMJudge(mock_client)

        is_correct, scores = judge.evaluate_fix(sample_problem, "code", iterations=4)

        assert is_correct is True  # 0.5 >= 0.5
        assert scores == [1.0, 0.0, 1.0, 0.0]
