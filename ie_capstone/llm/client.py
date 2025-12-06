"""Claude API client wrapper."""

import anthropic

from ie_capstone.config import CLAUDE_MODEL, MAX_TOKENS


class ClaudeClient:
    """Simple wrapper for Claude API calls."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize client. Uses ANTHROPIC_API_KEY env var if not provided.

        Args:
            api_key: Optional API key (uses env var if not provided)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def send_message(
        self,
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = MAX_TOKENS,
    ) -> str:
        """
        Send messages to Claude and get response.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system_prompt: System prompt for the conversation
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's response text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        )
        return response.content[0].text

    def send_single_message(
        self,
        user_message: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = MAX_TOKENS,
    ) -> str:
        """
        Convenience method for single-turn interactions (e.g., judge).

        Args:
            user_message: Single user message
            system_prompt: System prompt for the conversation
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's response text
        """
        messages = [{"role": "user", "content": user_message}]
        return self.send_message(messages, system_prompt, temperature, max_tokens)
