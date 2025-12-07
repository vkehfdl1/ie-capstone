"""Parser for the Socratic Debugging Benchmark and TreeInstruct datasets."""

import re
from pathlib import Path

from ie_capstone.config import DATA_DIR, TREEINSTRUCT_DATA_DIR
from ie_capstone.models import Problem


def extract_tag_content(text: str, tag_name: str) -> str:
    """
    Extract content between <tag_name> and </tag_name>.

    Args:
        text: Full file content
        tag_name: Name of the tag (e.g., "problem", "bug_code")

    Returns:
        Stripped content between tags, or empty string if tag not found
    """
    pattern = rf"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def strip_line_numbers(code: str) -> str:
    """
    Strip line numbers from code (e.g., "1. def foo():" -> "def foo():").

    The dataset has line numbers in format "N. " at the start of each line.

    Args:
        code: Code with line numbers

    Returns:
        Code without line numbers
    """
    lines = code.split("\n")
    stripped_lines = []
    for line in lines:
        # Match pattern like "1. ", "2. ", "10. " at start of line
        stripped = re.sub(r"^\d+\.\s?", "", line)
        stripped_lines.append(stripped)
    return "\n".join(stripped_lines)


def parse_bug_fixes(bug_fixes_content: str) -> list[str]:
    """
    Parse bug fixes content into list of individual fixes.

    Args:
        bug_fixes_content: Content from <bug_fixes> tag

    Returns:
        List of individual fix descriptions
    """
    if not bug_fixes_content.strip():
        return []

    # Split by newlines and filter empty lines
    lines = [line.strip() for line in bug_fixes_content.split("\n") if line.strip()]

    # Group multi-line fixes (like code blocks)
    fixes = []
    current_fix = []

    for line in lines:
        # Check if this is a new fix (starts with common patterns)
        if (
            line.startswith("Replace")
            or line.startswith("After")
            or line.startswith("Insert")
            or line.startswith("Remove")
            or line.startswith("Change")
            or line.startswith("Add")
        ):
            if current_fix:
                fixes.append("\n".join(current_fix))
            current_fix = [line]
        else:
            current_fix.append(line)

    if current_fix:
        fixes.append("\n".join(current_fix))

    return fixes if fixes else [bug_fixes_content.strip()]


def parse_unit_tests(unit_tests_content: str) -> list[str]:
    """
    Parse unit tests content into list of assert statements.

    Args:
        unit_tests_content: Content from <unit_tests> tag

    Returns:
        List of assert statements
    """
    if not unit_tests_content.strip():
        return []

    lines = [line.strip() for line in unit_tests_content.split("\n") if line.strip()]
    return [line for line in lines if line.startswith("assert")]


def parse_problem_file(file_path: Path) -> Problem:
    """
    Parse a single problem file with XML-like tags.

    Args:
        file_path: Path to the .txt file

    Returns:
        Problem object with all extracted fields

    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Problem file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")

    # Extract problem ID from filename (e.g., "1.txt" -> 1)
    problem_id = int(file_path.stem)

    # Extract all tagged content
    description = extract_tag_content(text, "problem")
    buggy_code_raw = extract_tag_content(text, "bug_code")
    buggy_code = strip_line_numbers(buggy_code_raw)
    bug_description = extract_tag_content(text, "bug_desc")
    bug_fixes_raw = extract_tag_content(text, "bug_fixes")
    unit_tests_raw = extract_tag_content(text, "unit_tests")
    example_dialogue = extract_tag_content(text, "dialogue")

    return Problem(
        id=problem_id,
        description=description,
        buggy_code=buggy_code,
        bug_description=bug_description,
        expected_fixes=parse_bug_fixes(bug_fixes_raw),
        unit_tests=parse_unit_tests(unit_tests_raw),
        example_dialogue=example_dialogue,
    )


def extract_treeinstruct_section(text: str, section_name: str) -> str:
    """
    Extract content from TreeInstruct format (section: --- ... ---).

    Args:
        text: Full file content
        section_name: Name of the section (e.g., "problem", "buggy_code")

    Returns:
        Stripped content between markers, or empty string if not found
    """
    pattern = rf"{section_name}: ---\n{section_name}:\n?(.*?)---"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def parse_treeinstruct_file(file_path: Path, problem_id: int) -> Problem:
    """
    Parse a TreeInstruct format problem file.

    Args:
        file_path: Path to the .txt file
        problem_id: ID to assign to this problem

    Returns:
        Problem object with all extracted fields

    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Problem file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")

    # Extract all sections
    description = extract_treeinstruct_section(text, "problem")
    buggy_code_raw = extract_treeinstruct_section(text, "buggy_code")
    buggy_code = strip_line_numbers(buggy_code_raw)
    bug_description = extract_treeinstruct_section(text, "bug_desc")
    bug_fixes_raw = extract_treeinstruct_section(text, "bug_fixes")

    # TreeInstruct doesn't have unit tests, so we leave empty
    unit_tests: list[str] = []

    return Problem(
        id=problem_id,
        description=description,
        buggy_code=buggy_code,
        bug_description=bug_description,
        expected_fixes=parse_bug_fixes(bug_fixes_raw),
        unit_tests=unit_tests,
        example_dialogue="",
    )


def load_socratic_problems() -> list[Problem]:
    """
    Load problems from Socratic Debugging Benchmark (1.txt, 2.txt, 3.txt).

    Returns:
        List of Problem objects with IDs 1-3
    """
    problems = []
    for i in range(1, 4):  # 1, 2, 3
        file_path = DATA_DIR / f"{i}.txt"
        if file_path.exists():
            problems.append(parse_problem_file(file_path))
    return problems


def load_treeinstruct_problems() -> list[Problem]:
    """
    Load problems from TreeInstruct dataset.

    Returns:
        List of Problem objects with IDs 4-6
    """
    # TreeInstruct files and their assigned IDs
    treeinstruct_files = [
        ("9-palindrome-number.py.txt", 4),
        ("45-jump-game-ii.py.txt", 5),
        ("463-island-perimeter.py.txt", 6),
    ]

    problems = []
    for filename, problem_id in treeinstruct_files:
        file_path = TREEINSTRUCT_DATA_DIR / filename
        if file_path.exists():
            problems.append(parse_treeinstruct_file(file_path, problem_id))
    return problems


def load_all_problems() -> list[Problem]:
    """
    Load all 6 problems from both datasets.

    Returns:
        List of Problem objects ordered by ID (1-6)
        - Problems 1-3: Socratic Debugging Benchmark
        - Problems 4-6: TreeInstruct Dataset
    """
    problems = []

    # Load from Socratic Debugging Benchmark (IDs 1-3)
    problems.extend(load_socratic_problems())

    # Load from TreeInstruct Dataset (IDs 4-6)
    problems.extend(load_treeinstruct_problems())

    return sorted(problems, key=lambda p: p.id)
