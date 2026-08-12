"""Real-file benchmark fixtures (Round 7).

Each fixture writes REAL material files to disk so the naive baseline and the Skill
pipeline read the SAME files (no cheating). The Skill pipeline ingests those same
files through the real ingestion pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.knowledge.build import build_course_intelligence
from exam_review_skill.ingestion.pipeline import ingest_file
from exam_review_skill.ingestion.types import IngestOptions
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


@dataclass
class BenchmarkFixture:
    name: str
    workspace_root: Path
    materials_dir: Path
    courses: list[dict] = field(default_factory=list)
    source_files: list[Path] = field(default_factory=list)
    important_terms: list[str] = field(default_factory=list)
    locale: str = "zh-CN"


def _write_txt(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def build_chinese_fixture(root: Path) -> BenchmarkFixture:
    """Benchmark A: a Chinese probability course with a past exam."""
    materials = root / "materials"
    materials.mkdir(parents=True, exist_ok=True)
    _write_txt(
        materials / "课件_第五章_中心极限定理.txt",
        "第五章 中心极限定理\n"
        "中心极限定理是指大量独立随机变量之和近似服从正态分布。\n"
        "老师强调这是必考重点。易错：混淆CLT的适用条件，忘记n足够大。\n"
        "公式：Z = (x - μ) / (σ/√n)。",
    )
    _write_txt(
        materials / "教材_正态分布.txt",
        "正态分布（normal distribution）的性质\n"
        "均值 μ 与方差 σ²。标准正态分布。\n"
        "中心极限定理的证明用到正态分布。易错：σ 与 σ/√n 混淆。",
    )
    _write_txt(
        materials / "真题_2024.txt",
        "2024 期末考试\n"
        "一、计算题 1. 用中心极限定理计算样本均值概率（15分）\n"
        "二、简答题 2. 简述条件概率与独立事件的区别（10分）",
    )
    _write_txt(
        materials / "作业_第二章.txt",
        "作业：条件概率 P(A|B) = P(A∩B)/P(B)。\n"
        "易错：条件概率不等于交集概率。",
    )

    workspace_mod.create_workspace(root / "ws", user_locale="zh-CN", daily_total_hours=6)
    ws = root / "ws"
    workspace_mod.add_course_to_workspace(
        ws, course_id="probability", course_name="概率论",
        exam_date="2026-06-19", target_score=85,
    )
    course_path = course_mod.course_dir(ws, "probability")
    tm = TerminologyMap(course_id="probability")
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem", aliases=["CLT"])
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    tm.add("normal_distribution", zh="正态分布", en="normal distribution")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    files = sorted(materials.glob("*.txt"))
    for path in files:
        ingest_file(ws, "probability", path, options=IngestOptions())
    build_course_intelligence(ws, "probability", days_to_exam=3)

    return BenchmarkFixture(
        name="chinese",
        workspace_root=ws,
        materials_dir=materials,
        courses=[{"course_id": "probability", "name": "概率论"}],
        source_files=files,
        important_terms=["中心极限定理", "条件概率", "正态分布", "CLT"],
        locale="zh-CN",
    )


def build_english_fixture(root: Path) -> BenchmarkFixture:
    """Benchmark B: an English linear-algebra course."""
    materials = root / "materials"
    materials.mkdir(parents=True, exist_ok=True)
    _write_txt(
        materials / "lecture_matrix.txt",
        "Lecture: Matrix operations\n"
        "A matrix is a rectangular array of numbers. Matrix multiplication is not commutative.\n"
        "Key exam point: determinant calculation. Common mistake: order of multiplication.",
    )
    _write_txt(
        materials / "textbook_eigenvalues.txt",
        "Chapter: Eigenvalues and eigenvectors\n"
        "An eigenvalue satisfies Ax = λx. The characteristic equation det(A - λI) = 0.\n"
        "Eigenvalues are frequently tested. Prerequisite: determinant.",
    )
    _write_txt(
        materials / "past_exam_2023.txt",
        "Final Exam 2023\n"
        "1. Compute the eigenvalues of a 2x2 matrix (12 points)\n"
        "2. State whether matrix multiplication is commutative (5 points)",
    )

    workspace_mod.create_workspace(root / "ws", user_locale="en-US", daily_total_hours=5)
    ws = root / "ws"
    workspace_mod.add_course_to_workspace(
        ws, course_id="linear-algebra", course_name="Linear Algebra",
        exam_date="2026-06-20", target_score=75,
    )
    course_path = course_mod.course_dir(ws, "linear-algebra")
    tm = TerminologyMap(course_id="linear-algebra")
    tm.add("matrix", zh="矩阵", en="matrix")
    tm.add("eigenvalue", zh="特征值", en="eigenvalue")
    tm.add("determinant", zh="行列式", en="determinant")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    files = sorted(materials.glob("*.txt"))
    for path in files:
        ingest_file(ws, "linear-algebra", path, options=IngestOptions())
    build_course_intelligence(ws, "linear-algebra", days_to_exam=3)

    return BenchmarkFixture(
        name="english",
        workspace_root=ws,
        materials_dir=materials,
        courses=[{"course_id": "linear-algebra", "name": "Linear Algebra"}],
        source_files=files,
        important_terms=["matrix", "eigenvalue", "determinant"],
        locale="en-US",
    )


def build_mixed_multi_fixture(root: Path) -> BenchmarkFixture:
    """Benchmark C: mixed-language, multi-course, past exams, and a scanned page.

    - probability: Chinese materials (zh PPT-style txt + en textbook) + past exam
    - organic-chemistry: English materials
    - scanned.pdf: an image-only page (multimodal path; synthetic provider in demo
      mode because no API key is present in this environment - documented honestly)
    """
    materials = root / "materials"
    materials.mkdir(parents=True, exist_ok=True)
    # probability: mixed zh/en
    _write_txt(
        materials / "概率课件.txt",
        "贝叶斯公式（Bayes' theorem）\n"
        "P(A|B) = P(B|A) P(A) / P(B)。条件概率的重要应用。\n"
        "老师强调这是高频考点。易错：忘记先验概率。",
    )
    _write_txt(
        materials / "probability_textbook_en.txt",
        "Bayes' theorem is used for conditional probability. It requires a known prior.\n"
        "Common mistake: confusing P(A|B) with P(B|A).",
    )
    _write_txt(
        materials / "概率真题_2024.txt",
        "2024 期末\n"
        "1. 用贝叶斯公式计算后验概率（15分）\n"
        "2. 简述条件概率定义（10分）",
    )
    # organic-chemistry: English
    _write_txt(
        materials / "organic_lecture.txt",
        "Organic Chemistry: Esterification\n"
        "Esterification is the reaction of a carboxylic acid with an alcohol.\n"
        "Exam point: reaction conditions (acid catalyst). Common trap: forgetting water removal.",
    )
    _write_txt(
        materials / "organic_exam_2023.txt",
        "Organic Chemistry Final 2023\n"
        "1. Write the esterification reaction and its conditions (10 points)\n"
        "2. Name the functional group in a given structure (5 points)",
    )
    # scanned page (image-only PDF)
    try:
        from .ingestion_fixtures import make_scanned_pdf
        scanned = materials / "scanned_handout.pdf"
        make_scanned_pdf(scanned, text="Bayes theorem formula summary")
    except Exception:
        scanned = None

    workspace_mod.create_workspace(root / "ws", user_locale="zh-CN", daily_total_hours=6)
    ws = root / "ws"

    workspace_mod.add_course_to_workspace(
        ws, course_id="probability", course_name="概率论 / Probability",
        exam_date="2026-06-19", target_score=85,
    )
    course_path = course_mod.course_dir(ws, "probability")
    tm = TerminologyMap(course_id="probability")
    tm.add("bayes_theorem", zh="贝叶斯公式", en="Bayes' theorem", aliases=["Bayes公式"])
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    workspace_mod.add_course_to_workspace(
        ws, course_id="organic-chemistry", course_name="Organic Chemistry",
        exam_date="2026-06-20", target_score=80,
    )
    org_path = course_mod.course_dir(ws, "organic-chemistry")
    tm_org = TerminologyMap(course_id="organic-chemistry")
    tm_org.add("esterification", zh="酯化反应", en="esterification")
    tm_org.add("functional_group", zh="官能团", en="functional group")
    course_mod._write_json(org_path / "terminology_map.json", tm_org.to_state())

    files: list[Path] = []
    for path in sorted(materials.glob("*.txt")):
        if "probability" in path.stem or "概率" in path.stem or "真题" in path.stem:
            ingest_file(ws, "probability", path, options=IngestOptions())
        else:
            ingest_file(ws, "organic-chemistry", path, options=IngestOptions())
        files.append(path)

    if scanned is not None:
        # scanned page -> multimodal path with synthetic provider (demo mode).
        # Synthetic records are clearly flagged and never enter real state in the
        # default mode; for the benchmark we allow demo mode and count the page as
        # "routed to vision" (honest multimodal-routing evidence without an API key).
        ingest_file(
            ws, "probability", scanned,
            options=IngestOptions(provider_name="synthetic", store_mode="demo"),
        )
        files.append(scanned)

    build_course_intelligence(ws, "probability", days_to_exam=3)
    build_course_intelligence(ws, "organic-chemistry", days_to_exam=3)

    return BenchmarkFixture(
        name="mixed-multi",
        workspace_root=ws,
        materials_dir=materials,
        courses=[
            {"course_id": "probability", "name": "概率论 / Probability"},
            {"course_id": "organic-chemistry", "name": "Organic Chemistry"},
        ],
        source_files=files,
        important_terms=["贝叶斯公式", "条件概率", "Bayes' theorem", "esterification", "functional group"],
        locale="zh-CN",
    )
