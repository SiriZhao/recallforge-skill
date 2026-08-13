# 小白入门

RecallForge 在 AI 宿主内部运行。核心 Skill 不需要 Python、API Key 或独立程序。

## 1. 安装

快速版：从[最新正式 Release](https://github.com/SiriZhao/recallforge-skill/releases/latest)下载 `recallforge-skill-v2.2.0.zip`，解压后将 `recallforge` 复制到 Windows 的 `%USERPROFILE%\.agents\skills`，或 macOS/Linux 的 `~/.agents/skills`。

完整平台步骤见 [Codex 中文指南](codex.zh-CN.md)。

## 2. 验证

新建 Codex 对话，输入 `$recallforge self-test`。看到 `Status: READY` 再继续；否则看[故障排查](troubleshooting.md)。

## 3. 准备第一组资料

第一次建议上传一个章节、一份课件或几页往年题。PPTX、数字/扫描 PDF、PNG/JPG/JPEG/WEBP、DOCX、TXT 和 Markdown 均有摄取路径，但扫描和视觉资料的最终理解能力取决于宿主视觉。

请删除不必要的隐私信息，只使用自己拥有或获得授权的资料。

## 4. 先检查资料

```text
$recallforge inspect-materials
请先检查这些资料，不要开始复习。告诉我实际检测到的资料类型、
宿主能够确认的页数或幻灯片数、扫描/图示较多的部分、识别问题和下一步建议。
```

RecallForge 不应编造文件数量，也不能把读不清的页面假装成已处理。

## 5. 建立课程结构

```text
$recallforge
以这些资料作为当前课程的主要范围，建立简洁、有来源依据的课程结构。
标记缺失范围和互相冲突的定义，不要先输出长篇摘要。
```

## 6. 开始诊断式主动回忆

```text
一次只问我一道题，等我回答后再解释。只记录我通过回答真实暴露的薄弱点。
```

## 7. 自适应修复

每次回答后，RecallForge 应说明错误类型、给出短修复并追问一道相邻问题。没有用户回答时，不应宣称已经掌握。

## 8. 模拟考试

```text
$recallforge
只根据我提供的资料生成模拟考试，不要先公布答案。
我作答后再评分、解释错误，对争议内容显示来源，并生成最后的针对性复习。
```

## 9. 修复识别问题

公式、扫描页、表格或图示被标记不确定时，上传更清晰的局部截图或原页。宿主视觉是首选；本地 OCR 只是可选文字恢复后备，不是核心 Skill 的必需项。参见[资料指南](materials.zh-CN.md)和[多模态指南](multimodal.zh-CN.md)。
