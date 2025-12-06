"""Tests for Socratic LM chatbot."""

from unittest.mock import MagicMock

import pytest

from ie_capstone.llm.socratic_lm import SocraticLM
from ie_capstone.models import Problem


@pytest.fixture
def sample_problem():
    return Problem(
        id=1,
        description="Write a search function",
        buggy_code="def search(x, seq):\n  for i in range(len(seq)):\n    if x < seq[i]:\n      return i\n  return len(seq)",
        bug_description="Missing equality check",
        expected_fixes=["Replace < with <="],
        unit_tests=["assert search(5, [-1, 5]) == 1"],
    )


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.send_message.return_value = "Have you considered what happens when x equals seq[i]?"
    return client


class TestSocraticLM:
    def test_initialization(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        assert slm.persona == "neutral"
        assert slm.problem == sample_problem
        assert slm.conversation_history == []
        assert "search function" in slm.system_prompt

    def test_initialization_emotional_persona(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "emotional", sample_problem)
        assert slm.persona == "emotional"
        # Korean: "친근" means friendly, "이모티콘" means emoji
        assert "친근" in slm.system_prompt or "이모티콘" in slm.system_prompt

    def test_get_initial_greeting_neutral(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        greeting = slm.get_initial_greeting()
        # Korean greeting should contain formal language
        assert "문제" in greeting or "설명" in greeting or "코드" in greeting
        assert len(slm.conversation_history) == 1
        assert slm.conversation_history[0].role == "assistant"

    def test_get_initial_greeting_emotional(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "emotional", sample_problem)
        greeting = slm.get_initial_greeting()
        assert "!" in greeting  # Enthusiastic punctuation
        assert len(slm.conversation_history) == 1

    def test_get_response(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        response = slm.get_response("My code isn't working")

        assert response == "Have you considered what happens when x equals seq[i]?"
        assert len(slm.conversation_history) == 2
        assert slm.conversation_history[0].role == "user"
        assert slm.conversation_history[0].content == "My code isn't working"
        assert slm.conversation_history[1].role == "assistant"

    def test_get_response_multi_turn(self, sample_problem, mock_client):
        mock_client.send_message.side_effect = [
            "What test case is failing?",
            "What value is returned instead?",
            "Let's trace through the code.",
        ]
        slm = SocraticLM(mock_client, "neutral", sample_problem)

        slm.get_response("Help me debug")
        slm.get_response("The first test fails")
        slm.get_response("It returns 2 instead of 1")

        assert len(slm.conversation_history) == 6  # 3 user + 3 assistant
        assert slm.turn_count == 3

    def test_reset_conversation(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        slm.get_response("Test message")
        assert len(slm.conversation_history) > 0

        slm.reset_conversation()
        assert slm.conversation_history == []

    def test_set_problem(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        slm.get_response("Test")
        assert len(slm.conversation_history) > 0

        new_problem = Problem(
            id=2,
            description="Factorial function",
            buggy_code="def factorial(n): return n",
            bug_description="Missing recursion",
            expected_fixes=["Add base case and recursion"],
            unit_tests=["assert factorial(5) == 120"],
        )

        slm.set_problem(new_problem)
        assert slm.problem == new_problem
        assert slm.conversation_history == []
        assert "Factorial" in slm.system_prompt

    def test_turn_count(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        assert slm.turn_count == 0

        slm.get_initial_greeting()
        assert slm.turn_count == 0  # Greeting doesn't count as user turn

        slm.get_response("Question 1")
        assert slm.turn_count == 1

        slm.get_response("Question 2")
        assert slm.turn_count == 2

    def test_conversation_for_api_format(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        slm.get_initial_greeting()
        slm.get_response("My question")

        api_messages = slm._get_conversation_for_api()

        assert len(api_messages) == 3
        assert api_messages[0]["role"] == "assistant"
        assert api_messages[1]["role"] == "user"
        assert api_messages[1]["content"] == "My question"
        assert api_messages[2]["role"] == "assistant"

    def test_client_called_with_correct_params(self, sample_problem, mock_client):
        slm = SocraticLM(mock_client, "neutral", sample_problem)
        slm.get_response("Test")

        mock_client.send_message.assert_called_once()
        call_kwargs = mock_client.send_message.call_args.kwargs
        assert call_kwargs["system_prompt"] == slm.system_prompt
        assert call_kwargs["temperature"] == 0.7
        assert len(call_kwargs["messages"]) == 1
