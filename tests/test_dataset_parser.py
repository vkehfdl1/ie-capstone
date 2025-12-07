"""Tests for dataset parser."""

import pytest

from ie_capstone.config import DATA_DIR, TREEINSTRUCT_DATA_DIR
from ie_capstone.dataset.parser import (
    extract_tag_content,
    extract_treeinstruct_section,
    load_all_problems,
    parse_bug_fixes,
    parse_problem_file,
    parse_treeinstruct_file,
    parse_unit_tests,
    strip_line_numbers,
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


class TestStripLineNumbers:
    def test_strip_simple_line_numbers(self):
        code = "1. def foo():\n2.     return 1"
        result = strip_line_numbers(code)
        assert result == "def foo():\n    return 1"

    def test_strip_double_digit_line_numbers(self):
        code = "10. line ten\n11. line eleven"
        result = strip_line_numbers(code)
        assert result == "line ten\nline eleven"

    def test_no_line_numbers(self):
        code = "def foo():\n    return 1"
        result = strip_line_numbers(code)
        assert result == "def foo():\n    return 1"

    def test_preserve_indentation_after_number(self):
        code = "1. def foo():\n2.  x = 1\n3.   return x"
        result = strip_line_numbers(code)
        assert result == "def foo():\n x = 1\n  return x"


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
    """Tests for Socratic Debugging Benchmark parser (problems 1-3)."""

    def test_parse_problem_1(self):
        problem = parse_problem_file(DATA_DIR / "1.txt")
        assert problem.id == 1
        assert "search(x: int, seq: List[int])" in problem.description
        assert "def search(x, seq):" in problem.buggy_code
        assert len(problem.unit_tests) > 0

    def test_parse_problem_2(self):
        problem = parse_problem_file(DATA_DIR / "2.txt")
        assert problem.id == 2
        assert "factorial" in problem.description.lower()
        assert "def factorial(n):" in problem.buggy_code

    def test_parse_problem_3(self):
        problem = parse_problem_file(DATA_DIR / "3.txt")
        assert problem.id == 3
        assert "turn_clockwise" in problem.description or "방위" in problem.description

    def test_parse_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_problem_file(DATA_DIR / "999.txt")


class TestExtractTreeinstructSection:
    def test_extract_problem_section(self):
        text = """problem: ---
problem:
This is a test problem.
---"""
        result = extract_treeinstruct_section(text, "problem")
        assert "This is a test problem" in result

    def test_extract_buggy_code_section(self):
        text = """buggy_code: ---
buggy_code:
1. def foo():
2.     return 1
---"""
        result = extract_treeinstruct_section(text, "buggy_code")
        assert "def foo():" in result

    def test_extract_missing_section_returns_empty(self):
        text = """problem: ---
problem:
Test
---"""
        result = extract_treeinstruct_section(text, "nonexistent")
        assert result == ""


class TestParseTreeinstructFile:
    """Tests for TreeInstruct dataset parser (problems 4-6)."""

    def test_parse_palindrome_number(self):
        problem = parse_treeinstruct_file(TREEINSTRUCT_DATA_DIR / "9-palindrome-number.py.txt", 4)
        assert problem.id == 4
        assert "회문" in problem.description or "palindrome" in problem.description.lower()
        assert "isPalindrome" in problem.buggy_code
        assert len(problem.expected_fixes) > 0

    def test_parse_jump_game(self):
        problem = parse_treeinstruct_file(TREEINSTRUCT_DATA_DIR / "45-jump-game-ii.py.txt", 5)
        assert problem.id == 5
        assert "점프" in problem.description or "jump" in problem.description.lower()
        assert "def jump" in problem.buggy_code

    def test_parse_island_perimeter(self):
        problem = parse_treeinstruct_file(TREEINSTRUCT_DATA_DIR / "463-island-perimeter.py.txt", 6)
        assert problem.id == 6
        assert "섬" in problem.description or "둘레" in problem.description
        assert "islandPerimeter" in problem.buggy_code

    def test_treeinstruct_has_no_unit_tests(self):
        problem = parse_treeinstruct_file(TREEINSTRUCT_DATA_DIR / "9-palindrome-number.py.txt", 4)
        assert problem.unit_tests == []

    def test_treeinstruct_code_has_no_line_numbers(self):
        problem = parse_treeinstruct_file(TREEINSTRUCT_DATA_DIR / "9-palindrome-number.py.txt", 4)
        lines = problem.buggy_code.split("\n")
        import re

        for line in lines:
            assert not re.match(r"^\d+\.\s", line), f"Line number found: {line}"


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
            # Note: TreeInstruct problems (4-6) don't have unit_tests
            if problem.id <= 3:
                assert len(problem.unit_tests) > 0

    def test_buggy_code_has_no_line_numbers(self):
        problems = load_all_problems()
        import re

        for problem in problems:
            lines = problem.buggy_code.split("\n")
            for line in lines:
                # Line should not start with "1. ", "2. ", etc.
                assert not re.match(r"^\d+\.\s", line), f"Line number found: {line}"

    def test_socratic_problems_are_1_to_3(self):
        problems = load_all_problems()
        socratic = [p for p in problems if p.id <= 3]
        assert len(socratic) == 3
        # Socratic problems have unit tests
        for p in socratic:
            assert len(p.unit_tests) > 0

    def test_treeinstruct_problems_are_4_to_6(self):
        problems = load_all_problems()
        treeinstruct = [p for p in problems if p.id >= 4]
        assert len(treeinstruct) == 3
        # TreeInstruct problems don't have unit tests
        for p in treeinstruct:
            assert p.unit_tests == []
