"""Tests for Claude API client."""

from unittest.mock import MagicMock, patch

from ie_capstone.llm.client import ClaudeClient


class TestClaudeClient:
    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_client_initialization(self, mock_anthropic):
        client = ClaudeClient(api_key="test-key")
        mock_anthropic.assert_called_once_with(api_key="test-key")
        assert client.model == "claude-opus-4-5-20251101"

    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_client_initialization_no_key(self, mock_anthropic):
        _client = ClaudeClient()
        mock_anthropic.assert_called_once_with(api_key=None)

    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_send_message(self, mock_anthropic):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]
        result = client.send_message(messages, "System prompt")

        assert result == "Test response"
        mock_client.messages.create.assert_called_once_with(
            model="claude-opus-4-5-20251101",
            max_tokens=16384,
            system="System prompt",
            messages=messages,
            temperature=0.7,
        )

    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_send_message_with_custom_params(self, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]
        result = client.send_message(messages, "System", temperature=0.3, max_tokens=1000)

        assert result == "Response"
        mock_client.messages.create.assert_called_once_with(
            model="claude-opus-4-5-20251101",
            max_tokens=1000,
            system="System",
            messages=messages,
            temperature=0.3,
        )

    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_send_single_message(self, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Single response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        result = client.send_single_message("Hello", "System prompt")

        assert result == "Single response"
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    @patch("ie_capstone.llm.client.anthropic.Anthropic")
    def test_send_message_multi_turn(self, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Multi-turn response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        messages = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]
        result = client.send_message(messages, "System prompt")

        assert result == "Multi-turn response"
        call_args = mock_client.messages.create.call_args
        assert len(call_args.kwargs["messages"]) == 3
