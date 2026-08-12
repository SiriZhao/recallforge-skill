"""Round 7: Naive ChatGPT Benchmark + full acceptance harness.

Compares the Exam Review Skill pipeline against an honest naive one-shot baseline
on the SAME source materials. No cheating: identical files, identical inputs,
no manual correction of either side, same grading standard.
"""

from . import metrics, naive

__all__ = ["metrics", "naive"]
