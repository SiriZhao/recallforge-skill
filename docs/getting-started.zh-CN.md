# RecallForge 中文入门教程

RecallForge 用你自己的课程资料建立考试复习闭环：资料理解、知识重构、主动回忆、错因诊断与复习计划。它不是代做考试题的服务，也不能替代课程要求核对。

## 开始前

你需要 Python 3.10 或更高版本。Windows 用户可以从 [python.org](https://www.python.org/downloads/) 安装，并在安装时勾选 **Add Python to PATH**。macOS/Linux 可用 `python3 --version` 查看版本。

建议使用你拥有或被授权使用的笔记、讲义、教学大纲、学习指南、少量教材摘录和允许使用的往年题。核心流程支持 TXT；PDF、DOCX、PPTX、图片和 OCR 需要额外安装 ingestion 依赖。扫描件和图片为主的资料还需要配置多模态提供方。

## 安装

1. 打开 [Releases 页面](https://github.com/SiriZhao/recallforge-skill/releases/latest)。
2. 下载 `recallforge-skill-v2.0.0.zip` 并解压。
3. 在解压目录打开 PowerShell 或终端。
4. 运行 `python -m pip install .`。
5. 运行 `recallforge --help`。

出现 `workspace` 命令列表即安装成功。Windows 找不到 `python` 时，请改用 `py -m pip install .` 和 `py -m recallforge --help`。

如需解析更多格式，运行 `python -m pip install ".[ingestion]"`。这只会安装 Python 库，不会配置 API Key，也不会上传资料。

## 第一次复习：概率论

新建 `materials` 文件夹，并放入一个短文本 `probability-notes.txt`，例如：

```text
中心极限定理：在满足独立等假设时，大量随机变量标准化后的和近似服从正态分布。老师特别强调先检查适用条件。
```

在你希望保存复习空间的位置运行：

```bash
recallforge workspace init --dir ./probability-review --locale zh-CN --daily-hours 3
recallforge workspace add-course --dir ./probability-review --course probability --name "概率论" --exam-date 2026-12-18 --target-score 80
recallforge workspace ingest --dir ./probability-review --course probability --input ./materials
recallforge workspace build --dir ./probability-review --course probability --days-to-exam 7
recallforge workspace material-report --dir ./probability-review --course probability
```

最后的报告是第一项验证：它会列出资料、提示缺口或未解决页面，并给出有证据边界的下一步。没有真实答题记录时，它不应假装你已经准备充分。

接着学习并进行主动回忆：

```bash
recallforge workspace tutor --dir ./probability-review --course probability --topic central_limit_theorem
recallforge workspace quiz --dir ./probability-review --course probability --mode mixed --count 3
```

答题后记录真实结果。确实答对才加 `--correct`；答错则不加，并可补充答案：

```bash
recallforge workspace answer --dir ./probability-review --course probability --topic central_limit_theorem --correct
```

## 推荐节奏

这不是强制日程，而是推荐顺序：

1. **整理资料**：导入并查看资料报告。
2. **建立结构**：构建知识和考试模型，查看覆盖与优先级。
3. **主动回忆**：先用讲解修补缺口，再用测验从记忆中提取。
4. **修复薄弱点**：记录错题，回看错题本，让下一次计划聚焦薄弱点。
5. **考前准备**：使用模拟考试报告或 `cram` 限时冲刺。

快速查漏补缺可从 `workspace diagnostic` 开始，再运行 `workspace quiz --mode weak-topic`。多门课在同一周考试时，把课程都加入同一个 workspace，然后用 `workspace plan-v4`。

## 常见问题

**Skill 没有“自动触发”。** RecallForge 是本地 CLI 包。先用 `recallforge --help` 验证安装，再直接运行命令。某些 AI 工具可读取 `SKILL.md`，但本仓库不承诺所有 AI 客户端都能自动发现。

**PDF 太大或是扫描件。** 先使用与考试相关的章节，必要时拆分文件。安装 ingestion 依赖；只有在接受资料处理方式时再配置提供方。无法读取的页面会显示为 unresolved，不会被编造。

**中文课程和英文课程能用吗？** 能。使用 `--locale zh-CN` 或 `--locale en-US`；混合语言术语也支持。

**如何更新、卸载？** 下载新版本后再次运行 `python -m pip install .`。卸载命令包使用 `python -m pip uninstall recallforge-skill`。复习空间是本地学习数据，如不再需要请自行删除对应文件夹。

仍有问题请查看[故障排查](troubleshooting.md)，或在 GitHub 提 Issue；不要附 API Key 或私人课程资料。
