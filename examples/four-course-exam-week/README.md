# Four-course exam week

A realistic exam week: Probability (tomorrow), Organic Chemistry (2 days), Calculus
(3 days), Botany (8 days). The orchestrator must NOT split time evenly, and must not
starve the far course.

```bash
python -m recallforge workspace init --dir ./example --locale zh-CN --daily-hours 6
```

```python
import sys; sys.path.insert(0, ".")
from pathlib import Path
from examples.examples_common import add_course_with_evidence, make_workspace

root = make_workspace(Path("example"), locale="zh-CN", daily_hours=6)
courses = [
    ("probability", "概率论", "2026-06-19", 85,
     [("central_limit_theorem", "中心极限定理", "CLT"), ("conditional_probability", "条件概率", "conditional probability")]),
    ("organic-chemistry", "有机化学", "2026-06-20", 80,
     [("esterification", "酯化反应", "esterification"), ("neutralization", "中和反应", "neutralization")]),
    ("calculus", "微积分", "2026-06-21", 60,
     [("limits", "极限", "limits"), ("derivatives", "导数", "derivatives")]),
    ("botany", "植物学", "2026-06-26", 70,
     [("photosynthesis", "光合作用", "photosynthesis"), ("transpiration", "蒸腾作用", "transpiration")]),
]
for course_id, name, exam_date, target, topics in courses:
    add_course_with_evidence(root, course_id=course_id, name=name,
                             exam_date=exam_date, target_score=target, topics=topics)
```

Run:

```bash
python -m recallforge workspace plan-v4 --dir ./example --date 2026-06-18
python -m recallforge workspace dashboard --dir ./example --date 2026-06-18
```

Expected: probability and organic get more time than botany (not a 3h/3h split);
botany still keeps a minimum maintenance block; the dashboard shows tomorrow/2
days/3 days/8 days with honest readiness.
