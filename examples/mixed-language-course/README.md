# Mixed-language course

A course with Chinese PPT + English textbook (e.g. Probability). Both languages are
listed as source languages; the terminology map fuses them into one topic model.

```python
import sys; sys.path.insert(0, ".")
from pathlib import Path
from examples.examples_common import add_course_with_evidence, make_workspace

root = make_workspace(Path("example"), locale="zh-CN", daily_hours=6)
add_course_with_evidence(
    root,
    course_id="probability",
    name="概率论 / Probability",
    exam_date="2026-06-21",
    target_score=80,
    topics=[
        ("bayes_theorem", "贝叶斯公式", "Bayes' theorem"),
        ("conditional_probability", "条件概率", "conditional probability"),
    ],
)
```

Run:

```bash
python -m exam_review_skill workspace build --dir ./example --course probability
python -m exam_review_skill workspace material-report --dir ./example --course probability
```

Expected: `Bayes' theorem` / `贝叶斯公式` / `Bayes公式` resolve to one topic via the
terminology map; the knowledge model keeps both localized names.
