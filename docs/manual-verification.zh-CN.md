# 正式宿主验收协议

这是 v2.2 正式发布前的真实宿主 Release Gate。维护者或受信任的评审人员必须在**独立的 Codex 新会话**中执行，不能从 Codex 内部递归启动 Codex。

## 必做测试

1. 运行 `/skills`，确认出现 `recallforge`。
2. 运行 `$recallforge self-test`。只有结果以 `Status: READY` 结束，并包含规定的概率主题、一道主动回忆题、一道考试型练习和下一步时才通过。
3. 上传 `skill/recallforge/assets/self-test/multimodal/probability-slide.svg`，运行 `$recallforge multimodal-test`。
   - PASS：宿主识别 `P(A|B) = P(A ∩ B) / P(B)`，区分表格中的独立事件与互斥事件，说明箭头表示按 `P(B)` 归一化，生成一道有来源的主动回忆题，并以 `Status: MULTIMODAL_READY` 结束。
   - 宿主无法查看测试图时记录 `HOST_CAPABILITY_UNAVAILABLE`，不要把 Skill 本身判为失败。
4. 上传项目自制 `lecture.pptx`、扫描 PDF 和往年试卷 PDF，然后运行：

   ```text
   $recallforge
   先检查这些资料，再建立课程结构，并开始一轮简短诊断复习。
   ```

   只有真实观察到资料检查、来源结构、知识重构和主动回忆才算 PASS；不能仅因为 `$recallforge` 接受了输入就通过。

## 证据

复制 [verification/host-verification-template.json](../verification/host-verification-template.json) 并填写：

- 宿主名称和版本
- 操作系统
- 日期
- RecallForge commit
- 安装方式
- 每个测试结果和简短证据
- 识别警告

不要包含姓名、邮箱、本机用户目录、私人路径、凭据或私人学习资料。完成后的文件在脱敏并由维护者决定公开前不要提交到仓库。
