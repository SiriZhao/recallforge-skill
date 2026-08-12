from __future__ import annotations

from dataclasses import asdict, dataclass, field
from dataclasses import field as _field
from datetime import date, datetime
from typing import Any


def _list(value: Any) -> list:
    return value if isinstance(value, list) else ([] if value is None else [value])


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# V2 state models (Round 1: multi-course workspace + bilingual foundation)
# All schema keys are stable English identifiers. UI/output localize later.
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """ISO-8601 timestamp with timezone, second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class WorkspaceState:
    workspace_id: str
    user_locale: str = "zh-CN"
    content_language: str = "auto"
    output_language: str = "zh-CN"
    daily_total_hours: float = 6.0
    courses: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class ExamCalendarEntry:
    course_id: str
    exam_date: str | None = None
    exam_time: str | None = None
    status: str = "scheduled"
    weight: float = 1.0
    note: str | None = None


@dataclass
class ExamCalendar:
    workspace_id: str
    entries: list[ExamCalendarEntry] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class CourseManifest:
    course_id: str
    course_name: str
    course_name_localized: dict[str, str] = field(default_factory=dict)
    source_languages: list[str] = field(default_factory=list)
    exam_date: str | None = None
    exam_time: str | None = None
    target_score: int = 80
    current_estimated_score: int | None = None
    daily_preference: float = 1.0
    importance_override: float | None = None
    material_count: int = 0
    topic_count: int = 0
    status: str = "active"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class CourseStudentState:
    student_id: str = "student-default"
    course_id: str = ""
    mastery: dict[str, dict] = field(default_factory=dict)
    weak_points: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)
    wrong_patterns: list[str] = field(default_factory=list)
    review_history: list[dict] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class CourseWrongbook:
    course_id: str = ""
    entries: list[dict] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class DocumentIndex:
    course_id: str = ""
    documents: list[dict] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class KnowledgeGraph:
    course_id: str = ""
    concepts: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class ExamModel:
    course_id: str = ""
    exam_points: list[dict] = field(default_factory=list)
    past_exam_refs: list[dict] = field(default_factory=list)
    coverage: dict[str, float] = field(default_factory=dict)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class CourseStudyPlan:
    course_id: str = ""
    plan: list[dict] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)


@dataclass
class TerminologyMapState:
    course_id: str = ""
    terms: dict[str, dict] = field(default_factory=dict)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class SessionRecord:
    session_id: str
    course_id: str
    date: str
    kind: str
    items: list[dict] = field(default_factory=list)
    answers: list[dict] = field(default_factory=list)
    diagnosis: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=_now_iso)
    ended_at: str | None = None


@dataclass
class DayOverride:
    date: str
    skip_courses: list[str] = field(default_factory=list)
    total_hours: float | None = None
    course_hours: dict[str, float] = field(default_factory=dict)
    target_scores: dict[str, int] = field(default_factory=dict)
    exam_date_changes: dict[str, str] = field(default_factory=dict)
    note: str | None = None


@dataclass
class PlanBlock:
    block_id: str
    course_id: str
    start: str
    end: str
    kind: str
    why: str
    risk: str
    goal: str
    done_when: str
    source: str = "planner"
    topic_id: str | None = None
    topic_name: str | None = None
    practice: str | None = None


@dataclass
class GlobalStudyPlan:
    workspace_id: str
    date: str
    total_hours: float
    blocks: list[PlanBlock] = field(default_factory=list)
    allocation: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    overrides_applied: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)


@dataclass
class CourseSignal:
    """Transparent scheduling signal for one course (heuristic, not a precise model)."""
    course_id: str
    days_to_exam: int | None
    urgency: float
    target_gap: float
    mastery_gap: float
    risk_signal: float
    expected_gain: float
    learning_cost_hours: float
    forgetting_risk: float
    unfinished_work: float
    coverage: float | None
    priority: float = 0.0
    allocation_hours: float = 0.0


# ---------------------------------------------------------------------------
# V3 exam-brain models (Round 3: Topic-centric knowledge + exam intelligence)
# Chunk/evidence is the proof; Topic is the core object.
# ---------------------------------------------------------------------------


@dataclass
class TopicField:
    """One evidence-backed field value on a topic (definition, formula, mistake...).

    Text is always a verbatim substring of the source evidence (hallucination
    guard), and every field carries the evidence ids that support it.
    """

    text: str
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5
    signals: list[str] = field(default_factory=list)  # e.g. formula ambiguity signals
    source_language: str | None = None


@dataclass
class KnowledgeTopic:
    """The core knowledge object. Replaces chunk-bag topics from v0.

    topic_id is a stable canonical key (derived from the terminology map or the
    normalized canonical name). All names/aliases are preserved; cross-language
    fusion confidence is explicit and never silently overwrites different concepts.
    """

    topic_id: str
    canonical_name: str
    localized_names: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    chapter: str | None = None
    prerequisites: list[str] = field(default_factory=list)  # topic_ids (evidence-backed)
    definitions: list[TopicField] = field(default_factory=list)
    formulas: list[TopicField] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    methods: list[TopicField] = field(default_factory=list)
    common_mistakes: list[TopicField] = field(default_factory=list)
    question_types: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)  # evidence ids (citations)
    teacher_emphasis: str = "unknown"  # observed | strongly_inferred | inferred | unknown
    teacher_emphasis_refs: list[str] = field(default_factory=list)
    past_exam_links: list[dict] = field(default_factory=list)  # [{exam_set_id, question_number, year}]
    fusion_confidence: float = 0.3
    source_confidence: float = 0.3
    inferred: bool = True
    created_at: str = field(default_factory=_now_iso)


@dataclass
class KnowledgeEdge:
    """Real, evidence-backed graph edge. `prerequisite` is only created from
    explicit text evidence - never from adjacency ordering (v0 fake-graph fix)."""

    source: str
    target: str
    relation: str  # prerequisite | related_to | part_of | often_confused_with | used_in
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class PastExamQuestion:
    exam_set_id: str
    question_number: str
    body: str = ""
    question_type: str = "unknown"
    score: str | None = None
    topics: list[str] = field(default_factory=list)  # topic_ids
    subtopics: list[str] = field(default_factory=list)
    difficulty: int = 2
    methods: list[str] = field(default_factory=list)
    common_traps: list[str] = field(default_factory=list)
    solution: str | None = None
    evidence_ref: str = ""
    year: str | None = None
    confidence: float = 0.5


@dataclass
class PastExamSet:
    exam_set_id: str
    source_file: str
    year: str | None = None
    questions: list[PastExamQuestion] = field(default_factory=list)
    evidence_ref: str = ""


@dataclass
class ExamPointModel:
    """One testable exam point, kept in exam_model.json - separate from the
    course knowledge model. likelihood_estimate is an ordinal heuristic (a
    transparent score), explicitly NOT a statistical probability."""

    exam_point_id: str
    topic_id: str
    topic_name: str
    importance: int = 3
    likelihood_estimate: float = 0.5  # heuristic score 0..1, not a real probability
    confidence: float = 0.3
    expected_score_range: list[int] = field(default_factory=lambda: [0, 0])
    question_types: list[str] = field(default_factory=list)
    teacher_emphasis: str = "unknown"
    past_exam_frequency: int = 0
    learning_cost: float = 1.0  # hours
    evidence: list[str] = field(default_factory=list)  # evidence ids
    past_exam_questions: list[dict] = field(default_factory=list)
    priority: str = "C"  # S/A/B/C (assigned by the explainable risk radar)
    priority_rationale: list[str] = field(default_factory=list)
    inferred: bool = True


@dataclass
class TeacherStyle:
    """Teacher style analysis with explicit evidence tiers:
    observed | strongly_inferred | inferred | unknown. No unsupported claims."""

    course_id: str = ""
    chapter_frequency: dict[str, int] = field(default_factory=dict)
    question_type_frequency: dict[str, int] = field(default_factory=dict)
    calc_vs_proof: dict[str, float] = field(default_factory=dict)  # {"calc": x, "proof": y}
    conceptual_vs_procedural: dict[str, float] = field(default_factory=dict)
    homework_reuse: bool | None = None
    parameter_variation: bool | None = None
    integrated_questions: int = 0
    trap_style: list[str] = field(default_factory=list)
    tier: str = "unknown"
    claims: list[dict] = field(default_factory=list)  # [{claim, tier, evidence_refs}]
    evidence_refs: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class ExamConflict:
    """A detected contradiction between sources. Never silently overwritten."""

    conflict_id: str
    topic_id: str | None = None
    question_number: str | None = None
    field: str = "definition"  # definition | formula | answer | method
    alternatives: list[dict] = _field(default_factory=list)  # [{text, source_file, source_type, date, evidence_ref}]
    resolved: bool = False
    chosen: dict | None = None
    resolution_reason: str = ""
    detected_at: str = _field(default_factory=_now_iso)


@dataclass
class CoverageReport:
    course_id: str = ""
    material_coverage: dict = field(default_factory=dict)
    chapter_coverage: dict = field(default_factory=dict)
    past_exam_coverage: dict = field(default_factory=dict)
    answer_coverage: dict = field(default_factory=dict)
    unresolved_documents: list[str] = field(default_factory=list)
    low_confidence_topics: list[str] = field(default_factory=list)
    verdict: str = "insufficient"
    generated_at: str = field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# V4 Student Model + Adaptive Planner (Round 4)
# ---------------------------------------------------------------------------


@dataclass
class TopicMastery:
    """Per-topic mastery. mastery is a composite (never equal to raw accuracy) and
    stays 'unknown' until real answer data exists. Never pretended to be 0.5."""

    topic_id: str
    mastery: str = "unknown"  # unknown | novice | developing | proficient
    mastery_score: float | None = None  # 0..1 composite, None while unknown
    confidence: float = 0.0
    questions_attempted: int = 0
    accuracy: float | None = None
    difficulty_coverage: dict[str, int] = field(default_factory=dict)  # {"1": n, "2": n, ...}
    hint_dependency: float | None = None  # fraction of correct answers that needed a hint
    last_reviewed: str | None = None
    wrong_count: int = 0
    mistake_types: list[str] = field(default_factory=list)
    forgetting_risk: float = 0.0
    transfer_performance: dict[str, int] = field(default_factory=dict)  # {"same_form": n, "new_form": n}
    question_type_coverage: dict[str, int] = field(default_factory=dict)
    updated_at: str = field(default_factory=_now_iso)

    def to_state(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "mastery": self.mastery,
            "mastery_score": self.mastery_score,
            "confidence": self.confidence,
            "questions_attempted": self.questions_attempted,
            "accuracy": self.accuracy,
            "difficulty_coverage": self.difficulty_coverage,
            "hint_dependency": self.hint_dependency,
            "last_reviewed": self.last_reviewed,
            "wrong_count": self.wrong_count,
            "mistake_types": self.mistake_types,
            "forgetting_risk": self.forgetting_risk,
            "transfer_performance": self.transfer_performance,
            "question_type_coverage": self.question_type_coverage,
            "updated_at": self.updated_at,
        }


@dataclass
class StudentModel:
    """Persistent per-course student model. Only real answer sessions may mutate it."""

    course_id: str
    student_id: str = "student-default"
    topics: dict[str, TopicMastery] = field(default_factory=dict)
    weak_points: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)
    wrong_patterns: list[str] = field(default_factory=list)
    review_history: list[dict] = field(default_factory=list)
    diagnostic_completed: bool = False
    last_updated: str = field(default_factory=lambda: date.today().isoformat())

    def to_state(self) -> dict:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "topics": {tid: tm.to_state() for tid, tm in self.topics.items()},
            "weak_points": self.weak_points,
            "strong_points": self.strong_points,
            "wrong_patterns": self.wrong_patterns,
            "review_history": self.review_history,
            "diagnostic_completed": self.diagnostic_completed,
            "last_updated": self.last_updated,
        }


@dataclass
class StudyBlock:
    """One concrete study block: course, topic, duration, reason, task, practice,
    and completion criterion - the unit the orchestrator schedules."""

    block_id: str
    course_id: str
    topic_id: str
    topic_name: str
    duration_hours: float
    reason: str
    task: str
    practice: str
    completion_criterion: str
    kind: str = "study"  # study | review | practice | cram | maintenance | diagnostic | wrongbook
    start: str | None = None
    end: str | None = None
    priority: str = "C"
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class CoursePlan:
    """Single-course adaptive plan - the decision 'what to study next in this course'."""

    course_id: str
    blocks: list[StudyBlock] = field(default_factory=list)
    strategy: str = "unknown"
    generated_at: str = field(default_factory=_now_iso)
    rationale: list[str] = field(default_factory=list)


@dataclass
class DiagnosticItem:
    topic_id: str
    topic_name: str
    reason: str
    question_type: str = "short_answer"
    difficulty: int = 2


@dataclass
class DiagnosticPlan:
    course_id: str
    items: list[DiagnosticItem] = field(default_factory=list)
    estimated_minutes: int = 15
    rationale: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)


@dataclass
class ReplanEvent:
    """A dynamic event that should trigger re-planning."""

    event_type: str  # quiz_completed | wrong_answer | topic_mastered | new_material |
    # | new_past_exam | exam_rescheduled | hours_changed | target_changed | course_completed
    course_id: str | None = None
    detail: dict = field(default_factory=dict)
    occurred_at: str = field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# V5 Tutor + Quiz + Diagnosis + Wrongbook + Cram (Round 5)
# ---------------------------------------------------------------------------


@dataclass
class TutorSection:
    """One section of a tutor explanation."""

    title: str
    content: str
    kind: str = "text"  # text | formula | list | check
    evidence_refs: list[str] = field(default_factory=list)
    supplementary: bool = False  # True => clearly marked "Supplementary explanation"


@dataclass
class TutorResponse:
    """A structured, course-first tutor explanation."""

    topic_id: str
    topic_name: str
    sections: list[TutorSection] = field(default_factory=list)
    check_question: str | None = None
    check_question_topic_id: str | None = None
    language: str = "zh-CN"
    evidence_refs: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)


@dataclass
class QuizQuestion:
    """A generated quiz question with provenance and adaptive level."""

    question_id: str
    topic_id: str
    topic_name: str
    question_type: str  # multiple_choice | fill_blank | short_answer | calculation | derivation | essay | diagram
    level: int  # 1 Recall | 2 Standard | 3 Variant | 4 Transfer
    question_text: str
    correct_answer: str = ""
    explanation: str = ""
    options: list[str] = field(default_factory=list)
    common_trap: str | None = None
    derived_from: str | None = None  # provenance: source question id / evidence id
    source_question: str | None = None
    variation_type: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    question_language: str = "zh-CN"
    explanation_language: str = "zh-CN"


@dataclass
class GradingResult:
    """Result of grading one answer, including process analysis."""

    question_id: str
    correct: bool
    score: float  # 0..1
    feedback: str
    process_analysis: str = ""
    mistake_type: str = "unknown"  # diagnosis taxonomy
    concept_gap_topic: str | None = None
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class DiagnosisResult:
    """A diagnosis with a taxonomy category and remediation path."""

    topic_id: str
    diagnosis: str  # concept_gap | formula_recall | condition_misread | prerequisite_gap |
    # calculation_error | algebra_error | sign_error | unit_error | reasoning_jump |
    # question_misread | method_selection | memory_failure | careless_error | unknown
    severity: int  # 1..3
    evidence_refs: list[str] = field(default_factory=list)
    prerequisite_fix: list[str] = field(default_factory=list)  # topic_ids to review
    explanation: str = ""


@dataclass
class RetrySchedule:
    """When to re-practice a wrong topic, based on mistake type, severity,
    repeat count, mastery, and exam proximity."""

    topic_id: str
    next_review_days: int
    next_review_date: str
    reason: str
    priority: str = "C"


@dataclass
class CramItem:
    """One item in a cram plan."""

    course_id: str
    topic_id: str
    topic_name: str
    kind: str  # formula | condition | definition | answer_template | mistake | trap | s_risk
    content: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class CramPlan:
    """A time-constrained cram plan. Different modes are genuinely different."""

    course_id: str
    mode: str  # 7d | 3d | 24h | 3h | 1h | 30m
    hours_left: float | None = None
    items: list[CramItem] = field(default_factory=list)
    focus_topics: list[str] = field(default_factory=list)
    priority: str = "S"
    rationale: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)
