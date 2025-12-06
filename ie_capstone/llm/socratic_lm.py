"""Socratic Learning Model chatbot for debugging assistance."""

from datetime import datetime

from ie_capstone.llm.client import ClaudeClient
from ie_capstone.llm.prompts import get_socratic_prompt
from ie_capstone.models import Message, PersonaType, Problem


class SocraticLM:
    """
    Socratic Learning Model chatbot for debugging assistance.
    Guides students through Socratic questioning without revealing answers.
    """

    def __init__(
        self,
        client: ClaudeClient,
        persona: PersonaType,
        problem: Problem,
    ):
        """
        Initialize SocraticLM with persona and problem context.

        Args:
            client: Claude API client
            persona: "neutral" or "emotional"
            problem: The current debugging problem
        """
        self.client = client
        self.persona = persona
        self.problem = problem
        self.system_prompt = get_socratic_prompt(persona, problem)
        self.conversation_history: list[Message] = []

    def get_response(self, user_message: str) -> str:
        """
        Get Socratic response to user's message.

        Args:
            user_message: Student's message

        Returns:
            Assistant's Socratic response
        """
        # Add user message to history
        self.conversation_history.append(Message(role="user", content=user_message, timestamp=datetime.now()))

        # Convert to API format
        api_messages = self._get_conversation_for_api()

        # Get response from Claude
        response = self.client.send_message(
            messages=api_messages,
            system_prompt=self.system_prompt,
            temperature=0.7,
        )

        # Add assistant response to history
        self.conversation_history.append(Message(role="assistant", content=response, timestamp=datetime.now()))

        return response

    def get_initial_greeting(self) -> str:
        """
        Get persona-appropriate initial greeting.

        Returns:
            Initial greeting message
        """
        if self.persona == "neutral":
            greeting = (
                "The student may begin by describing the issue encountered with the code. "
                "What behavior has been observed when running the code?"
            )
        else:
            greeting = (
                "Hey there! I'm excited to help you debug this code! "
                "What's going on? Tell me about the problem you're running into. "
            )

        # Add greeting to conversation history
        self.conversation_history.append(Message(role="assistant", content=greeting, timestamp=datetime.now()))

        return greeting

    def reset_conversation(self) -> None:
        """Clear conversation history for new problem."""
        self.conversation_history = []

    def set_problem(self, problem: Problem) -> None:
        """
        Set a new problem and reset conversation.

        Args:
            problem: New debugging problem
        """
        self.problem = problem
        self.system_prompt = get_socratic_prompt(self.persona, problem)
        self.reset_conversation()

    def _get_conversation_for_api(self) -> list[dict]:
        """
        Convert conversation history to API format.

        Returns:
            List of message dicts for Claude API
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.conversation_history]

    @property
    def turn_count(self) -> int:
        """Get number of user turns in conversation."""
        return sum(1 for msg in self.conversation_history if msg.role == "user")
