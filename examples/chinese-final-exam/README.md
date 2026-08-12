# Chinese university final exam

一个中文大学期末复习场景：一门《概率论》课程，含中文课件、教材和往年真题。

## Build the scenario

```bash
python -m exam_review_skill workspace init --dir ./example --locale zh-CN --daily-hours 6
python -m exam_review_skill workspace add-course --dir ./example --course probability \
  --name "概率论" --exam-date 2026-06-19 --target-score 85
```

Then ingest materials (or run the fixture builder below) and build the exam brain:

```bash
python -m exam_review_skill workspace build --dir ./example --course probability --days-to-exam 3
python -m exam_review_skill workspace material-report --dir ./example --course probability
python -m exam_review_skill workspace tutor --dir ./example --course probability --topic central_limit_theorem
python -m exam_review_skill workspace quiz --dir ./example --course probability --mode s-priority --count 5
python -m exam_review_skill workspace cram --dir ./example --course probability --mode 30m
```

## Fixture builder

```python
import sys; sys.path.insert(0, ".")
from pathlib import Path
from examples.examples_common import add_course_with_evidence, make_workspace

root = make_workspace(Path("example"), locale="zh-CN", daily_hours=6)
add_course_with_evidence(
    root,
    course_id="probability",
    name="概率论",
    exam_date="2026-06-19",
    target_score=85,
    topics=[
        ("central_limit_theorem", "中心极限定理", "Central Limit Theorem"),
        ("conditional_probability", "条件概率", "conditional probability"),
        ("normal_distribution", "正态分布", "normal distribution"),
    ],
    extra_evidence=[{
        "evidence_id": "EV-exam", "course_id": "probability",
        "source_file": "past_exam_2024.pdf", "document_type": "pdf",
        "page_or_slide": "1", "heading": "期末试卷", "source_language": "zh-CN",
        "extraction_method": "multimodal", "confidence": 0.8, "evidence_weight": 2.0,
        "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
        "content": {"text": "", "formula_signals": [],
                    "exam_structure": [
                        {"question_number": "1", "body": "中心极限定理计算", "question_type": "calculation", "score": "15"},
                        {"question_number": "2", "body": "条件概率简答", "question_type": "short answer", "score": "10"},
                    ]},
    }],
)
```

Expected: topics fuse zh/en names into one model; the risk radar ranks
central_limit_theorem; tutor + quiz + cram all run in Chinese.
