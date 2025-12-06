"""LLM-as-a-Judge for evaluating student bug fixes."""

from ie_capstone.config import JUDGE_ITERATIONS
from ie_capstone.llm.client import ClaudeClient
from ie_capstone.llm.prompts import get_judge_prompt
from ie_capstone.models import Problem


class LLMJudge:
    """
    LLM-as-a-Judge for evaluating student bug fixes.
    Uses self-consistency with multiple evaluations.
    """

    def __init__(self, client: ClaudeClient):
        """
        Initialize judge with Claude client.

        Args:
            client: Claude API client
        """
        self.client = client

    def evaluate_fix(
        self,
        problem: Problem,
        student_code: str,
        iterations: int = JUDGE_ITERATIONS,
    ) -> tuple[bool, list[float]]:
        """
        Evaluate if student's fix is correct using self-consistency.

        Args:
            problem: The debugging problem
            student_code: Student's submitted code
            iterations: Number of evaluation rounds (default 3)

        Returns:
            Tuple of (is_correct: bool, scores: list[float])
            - is_correct: True if average score >= 0.5
            - scores: Individual scores from each iteration (1.0 or 0.0)
        """
        scores = []
        for _ in range(iterations):
            score = self._single_evaluation(problem, student_code)
            scores.append(score)

        average_score = sum(scores) / len(scores)
        is_correct = average_score >= 0.5

        return is_correct, scores

    def _single_evaluation(self, problem: Problem, student_code: str) -> float:
        """
        Perform single evaluation.

        Args:
            problem: The debugging problem
            student_code: Student's submitted code

        Returns:
            1.0 if CORRECT, 0.0 if INCORRECT
        """
        prompt = get_judge_prompt(problem, student_code)

        # Use lower temperature for more consistent judgments
        response = self.client.send_single_message(
            user_message="Please evaluate the student's code fix.",
            system_prompt=prompt,
            temperature=0.3,
        )

        # Parse response - looking for CORRECT or INCORRECT
        response_upper = response.strip().upper()
        if "CORRECT" in response_upper and "INCORRECT" not in response_upper:
            return 1.0
        return 0.0
