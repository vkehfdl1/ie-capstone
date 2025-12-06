"""Session logging to JSON files."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from ie_capstone.config import LOGS_DIR
from ie_capstone.models import ExperimentSession, Message, MessageRole, PersonaType, ProblemAttempt


class SessionLogger:
    """
    Logs experiment sessions to JSON files.
    Each session gets its own file with all conversation data.
    """

    def __init__(self, logs_dir: Path | None = None):
        """
        Initialize logger with log directory.

        Args:
            logs_dir: Optional path to log directory (defaults to LOGS_DIR)
        """
        self.logs_dir = logs_dir or LOGS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        participant_id: str,
        persona: PersonaType,
    ) -> ExperimentSession:
        """
        Create new experiment session.

        Args:
            participant_id: Unique participant identifier
            persona: "neutral" or "emotional"

        Returns:
            New ExperimentSession with generated session_id
        """
        session_id = f"{participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        return ExperimentSession(
            session_id=session_id,
            participant_id=participant_id,
            persona=persona,
            start_time=datetime.now(),
        )

    def log_message(
        self,
        session: ExperimentSession,
        problem_id: int,
        role: MessageRole,
        content: str,
    ) -> None:
        """
        Log a single message in the current problem attempt.

        Args:
            session: The experiment session
            problem_id: ID of the current problem (1-6)
            role: "user" or "assistant"
            content: Message content
        """
        # Find or create problem attempt
        attempt = self._get_or_create_attempt(session, problem_id)

        # Add message
        message = Message(role=role, content=content, timestamp=datetime.now())
        attempt.conversation_history.append(message)

    def log_final_submission(
        self,
        session: ExperimentSession,
        problem_id: int,
        final_code: str,
        is_correct: bool,
        judge_scores: list[float],
    ) -> None:
        """
        Log the final submission for a problem.

        Args:
            session: The experiment session
            problem_id: ID of the problem (1-6)
            final_code: Student's final submitted code
            is_correct: Whether the fix was correct
            judge_scores: List of scores from judge evaluations
        """
        attempt = self._get_or_create_attempt(session, problem_id)
        attempt.final_code = final_code
        attempt.is_correct = is_correct
        attempt.judge_scores = judge_scores

    def save_session(self, session: ExperimentSession) -> Path:
        """
        Save session to JSON file.

        Args:
            session: The experiment session to save

        Returns:
            Path to saved file
        """
        file_path = self.get_session_file_path(session.session_id)
        session_dict = self._session_to_dict(session)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)

        return file_path

    def load_session(self, session_id: str) -> dict:
        """
        Load session from JSON file.

        Args:
            session_id: The session ID to load

        Returns:
            Session data as dictionary
        """
        file_path = self.get_session_file_path(session_id)
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def get_session_file_path(self, session_id: str) -> Path:
        """
        Get file path for session.

        Args:
            session_id: The session ID

        Returns:
            Path to the session JSON file
        """
        return self.logs_dir / f"{session_id}.json"

    def _get_or_create_attempt(self, session: ExperimentSession, problem_id: int) -> ProblemAttempt:
        """
        Get existing attempt or create new one.

        Args:
            session: The experiment session
            problem_id: ID of the problem

        Returns:
            The ProblemAttempt for this problem
        """
        # Find existing attempt
        for attempt in session.problem_attempts:
            if attempt.problem_id == problem_id:
                return attempt

        # Create new attempt
        attempt = ProblemAttempt(problem_id=problem_id)
        session.problem_attempts.append(attempt)
        return attempt

    def _session_to_dict(self, session: ExperimentSession) -> dict:
        """
        Convert session to JSON-serializable dict.

        Args:
            session: The experiment session

        Returns:
            Dictionary representation of session
        """
        return {
            "session_id": session.session_id,
            "participant_id": session.participant_id,
            "persona": session.persona,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "current_problem_index": session.current_problem_index,
            "metrics": {
                "success_rate": session.success_rate,
                "average_turns": session.average_turns,
            },
            "problem_attempts": [
                {
                    "problem_id": attempt.problem_id,
                    "final_code": attempt.final_code,
                    "is_correct": attempt.is_correct,
                    "judge_scores": attempt.judge_scores,
                    "turn_count": attempt.turn_count,
                    "conversation_history": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat(),
                        }
                        for msg in attempt.conversation_history
                    ],
                }
                for attempt in session.problem_attempts
            ],
        }
