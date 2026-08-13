# 人工宿主验收（2–3 分钟）

安装候选 Skill 后新建 Codex 对话。

1. 运行 `/skills`，记录是否出现 `recallforge`。
2. 运行 `$recallforge self-test`。只有结果以 `Status: READY` 结束，并包含规定的概率主题、主动回忆题、练习题和下一步时才通过。
3. 上传 `skill/recallforge/assets/self-test/multimodal/probability-slide.svg`，运行 `$recallforge multimodal-test`。
4. 只有宿主识别 `P(A|B) = P(A ∩ B) / P(B)`、区分表格中的独立与互斥、说明箭头表示除以 `P(B)` 的归一化关系、生成一题有来源的主动回忆题，并以 `Status: MULTIMODAL_READY` 结束时才通过。
5. 宿主不能查看测试图时记录 `HOST_CAPABILITY_UNAVAILABLE`，不要把 Skill 本身判为失败。
6. 上传一张项目自制扫描页，运行 `$recallforge inspect-materials`，确认看不清的部分被报告而不是被编造。

记录宿主/版本、系统、日期、文本结果、多模态结果和识别警告。不要记录私人资料或凭据。
