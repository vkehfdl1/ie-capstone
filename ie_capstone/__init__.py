"""IE Capstone Experiment - Socratic Learning Model for Python Debugging."""

from ie_capstone.app.gradio_app import create_app
from ie_capstone.dataset.parser import load_all_problems
from ie_capstone.llm.client import ClaudeClient
from ie_capstone.llm.judge import LLMJudge
from ie_capstone.llm.socratic_lm import SocraticLM
from ie_capstone.logging.session_logger import SessionLogger
from ie_capstone.models import (
    ExperimentSession,
    Message,
    PersonaType,
    Problem,
    ProblemAttempt,
)

__all__ = [
    "ClaudeClient",
    "ExperimentSession",
    "LLMJudge",
    "Message",
    "PersonaType",
    "Problem",
    "ProblemAttempt",
    "SessionLogger",
    "SocraticLM",
    "create_app",
    "load_all_problems",
]
