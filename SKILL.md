---
name: exam-review-skill
description: Build a powerful exam-oriented review system from lecture slides, textbooks, notes, scanned papers, exercises, past exams, and teacher hints. Use this skill when the user wants to prepare for an exam, improve review efficiency, analyze course materials, generate exam-focused study plans, identify high-risk exam points, create past-exam variants, build a wrong-question notebook, or produce cram packs.
---

# exam-review-skill

核心口号：输入课程资料，输出提分路径。

## 1. Skill 目的

把课件、教材、课堂笔记、扫描试卷、往年题、作业、答案和老师画重点转化为考试导向的复习作战系统。优先生成考点图谱、风险雷达、自适应复习计划、真题变式、错题本、临考急救包和质量报告，而不是泛泛总结。

## 2. 适用场景

- 期末、补考、考研课程、闭卷/开卷考试复习。
- 用户资料很多但时间有限，需要压缩成抢分路径。
- 用户需要按目标分数调整策略：及格、80分、90分。
- 用户要分析往年题、老师命题风格、常见陷阱、薄弱点和错题。

## 3. 输入资料类型

支持 txt、md、pdf、pptx、docx、png、jpg、jpeg。资料可包含课件、教材、课堂笔记、实验手册、练习、答案、往年题、扫描试卷和老师强调重点。图片和扫描类资料应尝试 OCR；OCR 不可用时继续流程并写入 warning。

## 4. 输出文件类型

输出 Markdown、JSON、可选 DOCX、可选 PDF、基础 Anki CSV。完整运行输出 `00_资料来源与解析报告.md` 到 `15_考前30分钟速救版.md`，以及 `course_index.json`、`exam_graph.json`、`risk_radar.json`、`student_state.json`、`wrongbook.json` 和 `generation_report.md`。

## 5. 完整工作流

1. 摄入资料并保留文件名、页码、幻灯片编号、段落、标题、题号。
2. 自动分类为课件、教材、课堂笔记、往年题、练习、实验手册、答案、老师重点或 unknown。
3. 按章节、PPT页、PDF页、标题、题号、公式、语义边界和 token 限制智能分块。
4. 建立课程知识索引，合并重复 topic，保留来源。
5. 建立考试考点图谱，说明可能怎么考、常见陷阱和变式方向。
6. 计算考试风险雷达，按 S/A/B/C 排优先级。
7. 生成章节重点精讲、高频考点、真题映射、变式训练。
8. 诊断个人薄弱点；没有答题数据时标记 unknown 或 estimated。
9. 按考试日期、目标分数和每日时间生成复习计划与今日任务。
10. 生成专项训练、错题本、老师命题风格报告和临考急救包。
11. 运行质量检查，发现风险时 warning，不直接失败。

## 6. 来源引用规范

所有重要考点、题目、预测和建议都应尽量附来源。来源至少包含 `source_file`，可用时包含 `page_or_slide`、`question_number`、`heading` 和置信度。不允许丢失文件名、页码、幻灯片编号、题号。无来源 topic 必须 `inferred=true`；无来源高置信度结论必须降置信度或标记“需人工确认”。

## 7. 考试导向原则

不允许只做泛泛总结。不允许把所有资料当成一坨文本。不允许编造课程范围外内容。输出必须服务于考试提分，而不是百科式解释。优先回答：这个点会不会考、怎么考、值几分、怎么拿分、哪里会丢分、时间不够先看什么。

## 8. 复习效率原则

优先处理 S/A 风险项，先拿高概率基础分，再训练变式迁移。每个复习动作必须具体到内容、时间、题型和自测方式。用户时间不足时，自动压缩为抢分策略，放弃低收益 C 级内容。

## 9. 目标分数策略

- 及格保底：保定义、基础公式、来源题、步骤题，允许放弃低频难题。
- 80分稳妥：S/A 全覆盖，B 级抽查，往年题变式至少一轮。
- 90分冲刺：增加综合题、陷阱题、难度升级变式和老师风格推断。
- 考前一天：只看风险雷达、错题和急救包。
- 考前一小时：只看 S 级、公式条件、易错点和答题模板。

## 10. 失败降级策略

单个文件失败不能中断全流程。OCR 不可用、DOCX/PPTX/PDF 依赖缺失、LLM JSON 解析失败、真实 API 失败、资料缺页码、没有往年题、没有答题数据时，都应 graceful fallback，使用 MockLLMProvider 或规则生成，并在 `generation_report.md` 中记录 warning。

## 11. 禁止行为

- 禁止只输出 README 或空壳文件。
- 禁止把课程资料混成无来源大文本。
- 禁止丢失来源字段。
- 禁止脱离课程资料乱编考点、题目或答案。
- 禁止把无法确认的内容写成确定结论。
- 禁止输出与目标分数不匹配的复习计划。
- 禁止在 OCR 低置信度内容上生成高置信度结论。

## 12. 质量检查标准

检查所有文件是否被读取、所有章节是否有输出、考点是否有来源、题目是否超出资料范围、变式是否基于真实考点、老师风格判断是否有依据、是否存在无来源高置信度结论、OCR 低置信度内容是否被误用、输出文件是否缺失、JSON 是否有效、是否存在空泛总结、答案是否缺失、题干答案是否匹配、复习计划是否匹配目标分数。发现问题时不要直接失败，应标记 warning，输出可读报告，并对高风险内容标记“需人工确认”。

## CLI

完整运行：

```bash
python -m exam_review_skill run --input ./materials --output ./ExamReview_Output --course "课程名称" --exam-date "2026-06-25" --target-score 80 --daily-hours 4
```

临考急救包：

```bash
python -m exam_review_skill cram --state ./ExamReview_Output/student_state.json --hours-left 3
```

真题变式：

```bash
python -m exam_review_skill variants --input ./materials --output ./ExamReview_Output --count 20
```

复习计划：

```bash
python -m exam_review_skill plan --state ./ExamReview_Output/student_state.json --days-left 3 --daily-hours 4 --target-score 80
```

训练题：

```bash
python -m exam_review_skill quiz --state ./ExamReview_Output/student_state.json --mode s-priority --count 20
python -m exam_review_skill quiz --state ./ExamReview_Output/student_state.json --mode wrongbook --count 10
```
