"""Evaluation package."""

from humantext.eval.runner import run_evaluation
from humantext.eval.report import render_markdown_report

__all__ = ["render_markdown_report", "run_evaluation"]
