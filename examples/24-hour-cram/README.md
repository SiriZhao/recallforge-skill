# 24-hour cram scenario

Two exams in 24-48 hours. The cram engine must produce genuinely different tiers
(24h / 3h / 1h / 30m) and the orchestrator must coordinate both near exams while
maintaining far courses.

```python
import sys; sys.path.insert(0, ".")
from pathlib import Path
from examples.examples_common import add_course_with_evidence, make_workspace

root = make_workspace(Path("example"), locale="zh-CN", daily_hours=6)
add_course_with_evidence(root, course_id="probability", name="概率论",
    exam_date="2026-06-19", target_score=85,
    topics=[("central_limit_theorem", "中心极限定理", "CLT"), ("conditional_probability", "条件概率", "conditional probability")])
add_course_with_evidence(root, course_id="organic-chemistry", name="有机化学",
    exam_date="2026-06-20", target_score=80,
    topics=[("esterification", "酯化反应", "esterification"), ("neutralization", "中和反应", "neutralization")])
add_course_with_evidence(root, course_id="botany", name="植物学",
    exam_date="2026-06-26", target_score=70,
    topics=[("photosynthesis", "光合作用", "photosynthesis")])
```

Run:

```bash
python -m exam_review_skill workspace report --dir ./example --type 1-hour-cram --course probability
python -m exam_review_skill workspace report --dir ./example --type 30-min-rescue --course probability
python -m exam_review_skill workspace plan-v4 --dir ./example --date 2026-06-18
```

Expected: 30-min rescue keeps ONLY S-level core formulas/conditions/traps; the
24h/3h/1h/30m modes each contain fewer items; both near courses get emergency
cram blocks while botany keeps maintenance.
