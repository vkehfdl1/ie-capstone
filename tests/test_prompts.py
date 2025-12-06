"""Tests for prompt generation."""

from ie_capstone.llm.prompts import get_judge_prompt, get_socratic_prompt
from ie_capstone.models import Problem


class TestGetSocraticPrompt:
    def setup_method(self):
        self.problem = Problem(
            id=1,
            description="Write a search function",
            buggy_code="def search(x): return x",
            bug_description="Missing return value",
            expected_fixes=["Add proper return"],
            unit_tests=["assert search(1) == 1"],
        )

    def test_neutral_prompt_contains_required_sections(self):
        prompt = get_socratic_prompt("neutral", self.problem)
        assert "Write a search function" in prompt
        assert "def search(x): return x" in prompt
        assert "Missing return value" in prompt
        assert "Add proper return" in prompt
        assert "assert search(1) == 1" in prompt

    def test_neutral_prompt_has_formal_tone(self):
        prompt = get_socratic_prompt("neutral", self.problem)
        assert "third-person" in prompt.lower() or "The student" in prompt
        assert "Do NOT use emojis" in prompt

    def test_emotional_prompt_contains_required_sections(self):
        prompt = get_socratic_prompt("emotional", self.problem)
        assert "Write a search function" in prompt
        assert "def search(x): return x" in prompt
        assert "Missing return value" in prompt

    def test_emotional_prompt_has_friendly_tone(self):
        prompt = get_socratic_prompt("emotional", self.problem)
        assert "friendly" in prompt.lower() or "encouraging" in prompt.lower()
        assert "emoji" in prompt.lower()

    def test_prompts_warn_not_to_reveal_answer(self):
        neutral = get_socratic_prompt("neutral", self.problem)
        emotional = get_socratic_prompt("emotional", self.problem)
        assert "NEVER reveal" in neutral or "DO NOT REVEAL" in neutral
        assert "NEVER reveal" in emotional or "DO NOT REVEAL" in emotional


class TestGetJudgePrompt:
    def setup_method(self):
        self.problem = Problem(
            id=1,
            description="Test problem",
            buggy_code="def foo(): return 0",
            bug_description="Returns wrong value",
            expected_fixes=["return 1"],
            unit_tests=["assert foo() == 1"],
        )

    def test_judge_prompt_contains_all_sections(self):
        prompt = get_judge_prompt(self.problem, "def foo(): return 1")
        assert "def foo(): return 0" in prompt  # Original buggy code
        assert "Returns wrong value" in prompt  # Bug description
        assert "return 1" in prompt  # Expected fix
        assert "def foo(): return 1" in prompt  # Student code
        assert "assert foo() == 1" in prompt  # Unit tests

    def test_judge_prompt_asks_for_correct_or_incorrect(self):
        prompt = get_judge_prompt(self.problem, "def foo(): return 1")
        assert "CORRECT" in prompt
        assert "INCORRECT" in prompt

    def test_judge_prompt_with_multiple_fixes(self):
        problem = Problem(
            id=1,
            description="Test",
            buggy_code="code",
            bug_description="bug",
            expected_fixes=["Fix 1", "Fix 2", "Fix 3"],
            unit_tests=["test1", "test2"],
        )
        prompt = get_judge_prompt(problem, "student code")
        assert "Fix 1" in prompt
        assert "Fix 2" in prompt
        assert "Fix 3" in prompt
