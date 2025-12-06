"""Data models for the IE Capstone Experiment."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

PersonaType = Literal["neutral", "emotional"]
MessageRole = Literal["user", "assistant"]


@dataclass
class Problem:
    """Represents a debugging problem from the dataset."""

    id: int
    description: str
    buggy_code: str
    bug_description: str
    expected_fixes: list[str]
    unit_tests: list[str]
    example_dialogue: str = ""


@dataclass
class Message:
    """A single message in the conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProblemAttempt:
    """Records a participant's attempt at solving a problem."""

    problem_id: int
    conversation_history: list[Message] = field(default_factory=list)
    final_code: str = ""
    is_correct: bool | None = None
    judge_scores: list[float] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        """Count the number of user messages (turns) in the conversation."""
        return sum(1 for msg in self.conversation_history if msg.role == "user")


@dataclass
class ExperimentSession:
    """Complete session data for one participant."""

    session_id: str
    participant_id: str
    persona: PersonaType
    start_time: datetime
    end_time: datetime | None = None
    problem_attempts: list[ProblemAttempt] = field(default_factory=list)
    current_problem_index: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate across all completed problems."""
        completed = [a for a in self.problem_attempts if a.is_correct is not None]
        if not completed:
            return 0.0
        correct = sum(1 for a in completed if a.is_correct)
        return correct / len(completed)

    @property
    def average_turns(self) -> float:
        """Calculate average turns per problem."""
        completed = [a for a in self.problem_attempts if a.is_correct is not None]
        if not completed:
            return 0.0
        total_turns = sum(a.turn_count for a in completed)
        return total_turns / len(completed)
