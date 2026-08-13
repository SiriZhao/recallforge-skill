"""Round 3: Course Knowledge Model + Exam Intelligence (the exam brain).

KnowledgeTopic is the core object; evidence (chunks/pages) is only the proof. Cross-language
topic fusion, an evidence-grounded knowledge graph, a separate exam model, an
explainable risk radar, past-exam intelligence, teacher style, conflict handling,
and coverage reports all live here.
"""

from . import conflict, coverage, exam, graph, risk, teacher, topic

__all__ = ["conflict", "coverage", "exam", "graph", "risk", "teacher", "topic"]
