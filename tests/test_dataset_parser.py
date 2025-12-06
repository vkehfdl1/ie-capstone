"""Tests for dataset parser."""

import pytest

from ie_capstone.config import DATA_DIR
from ie_capstone.dataset.parser import (
    extract_tag_content,
    load_all_problems,
    parse_bug_fixes,
    parse_problem_file,
    parse_unit_tests,
)
from ie_capstone.models import Problem


class TestExtractTagContent:
    def test_extract_simple_tag(self):
        text = "<problem>This is a problem</problem>"
        result = extract_tag_content(text, "problem")
        assert result == "This is a problem"

    def test_extract_multiline_content(self):
        text = """<bug_code>
1. def foo():
2.     return 1
</bug_code>"""
        result = extract_tag_content(text, "bug_code")
        assert "def foo():" in result
        assert "return 1" in result

    def test_extract_missing_tag_returns_empty(self):
        text = "<problem>Test</problem>"
        result = extract_tag_content(text, "nonexistent")
        assert result == ""

    def test_extract_with_nested_content(self):
        text = "<dialogue>User: <code>print(x)</code></dialogue>"
        result = extract_tag_content(text, "dialogue")
        assert result == "User: <code>print(x)</code>"


class TestParseBugFixes:
    def test_single_fix(self):
        content = "Replace `<` with `<=` on line 3"
        fixes = parse_bug_fixes(content)
        assert len(fixes) == 1
        assert fixes[0] == "Replace `<` with `<=` on line 3"

    def test_multiple_fixes_newline_separated(self):
        content = """Replace `i` with `(i + 1)` in line 6.
Replace `range(n)` with `range(1, n + 1)` in line 5."""
        fixes = parse_bug_fixes(content)
        assert len(fixes) == 2
        assert "Replace `i` with `(i + 1)`" in fixes[0]
        assert "Replace `range(n)`" in fixes[1]

    def test_empty_content(self):
        fixes = parse_bug_fixes("")
        assert fixes == []


class TestParseUnitTests:
    def test_parse_asserts(self):
        content = """assert search(5, [-1, 5, 8, 10, 12]) == 1
assert search(-2, [-1, 57, 65]) == 0
assert search(0, [-120, 60, 78, 100]) == 1"""
        tests = parse_unit_tests(content)
        assert len(tests) == 3
        assert "search(5, [-1, 5, 8, 10, 12])" in tests[0]

    def test_empty_content(self):
        tests = parse_unit_tests("")
        assert tests == []


class TestParseProblemFile:
    def test_parse_problem_1(self):
        problem = parse_problem_file(DATA_DIR / "1.txt")
        assert problem.id == 1
        assert "search(x: int, seq: List[int])" in problem.description
        assert "def search(x, seq):" in problem.buggy_code
        assert "Replace `<` with `<=" in problem.expected_fixes[0]
        assert len(problem.unit_tests) > 0

    def test_parse_problem_2(self):
        problem = parse_problem_file(DATA_DIR / "2.txt")
        assert problem.id == 2
        assert "factorial" in problem.description.lower()
        assert "def factorial(n):" in problem.buggy_code

    def test_parse_problem_3(self):
        problem = parse_problem_file(DATA_DIR / "3.txt")
        assert problem.id == 3
        assert "compass" in problem.description.lower()

    def test_parse_problem_4(self):
        problem = parse_problem_file(DATA_DIR / "4.txt")
        assert problem.id == 4
        assert "my_func" in problem.buggy_code

    def test_parse_problem_5(self):
        problem = parse_problem_file(DATA_DIR / "5.txt")
        assert problem.id == 5
        assert "fibonacci" in problem.description.lower()

    def test_parse_problem_6(self):
        problem = parse_problem_file(DATA_DIR / "6.txt")
        assert problem.id == 6

    def test_parse_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_problem_file(DATA_DIR / "999.txt")


class TestLoadAllProblems:
    def test_load_all_six_problems(self):
        problems = load_all_problems()
        assert len(problems) == 6
        assert all(isinstance(p, Problem) for p in problems)

    def test_problems_ordered_by_id(self):
        problems = load_all_problems()
        ids = [p.id for p in problems]
        assert ids == [1, 2, 3, 4, 5, 6]

    def test_all_problems_have_required_fields(self):
        problems = load_all_problems()
        for problem in problems:
            assert problem.description
            assert problem.buggy_code
            assert problem.bug_description
            assert len(problem.expected_fixes) > 0
            assert len(problem.unit_tests) > 0
