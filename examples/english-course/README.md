# English-language course

An English-language course (e.g. Linear Algebra) with an en-US UI, showing English
questions with Chinese explanations (independent question/explanation language).

```bash
python -m exam_review_skill workspace init --dir ./example --locale en-US --daily-hours 5
python -m exam_review_skill workspace add-course --dir ./example --course linear-algebra \
  --name "Linear Algebra" --exam-date 2026-06-20 --target-score 75
```

```python
import sys; sys.path.insert(0, ".")
from pathlib import Path
from examples.examples_common import add_course_with_evidence, make_workspace

root = make_workspace(Path("example"), locale="en-US", daily_hours=5)
add_course_with_evidence(
    root,
    course_id="linear-algebra",
    name="Linear Algebra",
    exam_date="2026-06-20",
    target_score=75,
    topics=[
        ("matrix", "矩阵", "matrix"),
        ("eigenvalue", "特征值", "eigenvalue"),
        ("linear_transformation", "线性变换", "linear transformation"),
    ],
)
```

Run:

```bash
python -m exam_review_skill workspace quiz --dir ./example --course linear-algebra \
  --mode mixed --question-language en-US --explanation-language zh-CN
python -m exam_review_skill workspace dashboard --dir ./example
```

Expected: the dashboard renders in English; quiz questions are English while the
explanations are Chinese (bilingual output mode).
