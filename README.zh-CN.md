<p align="center"><img src="assets/brand/recallforge-banner.svg" alt="RecallForge — AI Exam Review Skill" width="100%"></p>

<p align="center"><strong>简体中文</strong> · <a href="README.md">English</a></p>

# RecallForge — AI Exam Review Skill

**将课程资料锻造成真正可用于考试的知识体系。**

RecallForge 是装载到 Codex 和兼容 Agent Skills 宿主中的 AI 复习 Skill。安装一次 `recallforge` 文件夹后，就在宿主 AI 中完成知识重构、主动回忆、薄弱点诊断、针对性练习和模拟考试。它不是网页应用、独立聊天软件、API 服务，也不需要运行单独程序。

## 三分钟安装

到 [Releases](https://github.com/SiriZhao/recallforge-skill/releases/latest) 下载 `recallforge-skill-v2.1.0.zip` 并解压。解压后会看到 `recallforge` 文件夹；把它复制到：

- **Windows：** `%USERPROFILE%\.agents\skills\recallforge`
- **macOS / Linux：** `~/.agents/skills/recallforge`

不需要安装 Python、npm、API Key 或 RecallForge 独立程序。

| 你的情况 | 选什么 |
|---|---|
| 只想开始使用 | Release ZIP |
| Windows 且想最快安装 | ZIP 中的 `install.ps1` |
| macOS/Linux | ZIP 中的 `install.sh` |
| 开发者 | Git clone + 项目级安装 |
| 使用 Plugin 流程 | `recallforge-plugin-v2.1.0.zip` |

Windows PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

macOS/Linux 终端：

```bash
bash ./scripts/install.sh
```

## 30 秒确认安装成功

1. 打开一个**新的 Codex 对话**，让 Codex 自动发现新 Skill。
2. 输入：`$recallforge self-test`
3. 看到：`Status: READY`

这表示 RecallForge 已成功调用、读取内置概率论微型资料、建立知识结构、生成主动回忆题和考试型练习。没有成功请看[故障排查](docs/troubleshooting.md)。

## 第一次真实复习

```text
$recallforge
我要准备一次考试。
课程：[课程名称]
考试时间：[可选]
复习资料：[上传文件或粘贴笔记]
请先分析资料并建立面向考试的知识结构，然后通过主动回忆逐步带我复习，识别我的薄弱知识点。不要一次性把所有内容全部输出给我。
```

考前冲刺：

```text
$recallforge
我距离考试只有 90 分钟。请优先安排最有价值的知识点，用主动回忆测试我，并集中修复错误和薄弱点。
```

## 自动触发与显式调用

- **第一次最推荐：**显式输入 `$recallforge`，最容易确认安装和调用成功。
- **自动触发：**当你提到期末/期中复习、课程或讲义、主动回忆、薄弱知识点、模拟考试、学习指南或考试练习时，Codex 可能自动选择 RecallForge。
- 自动触发由宿主的匹配机制决定，不能保证每次都触发；没触发并不表示安装失败，请直接使用 `$recallforge`。
- 代码审查、合同审查、只翻译笔记、普通摘要等任务不应触发 RecallForge。

## 两分钟功能测试

复制以下内容；如未自动触发，请在首行加 `$recallforge`：

```text
我要复习一个概率论小测验。这是我的笔记：条件概率表示在事件 B 已发生时事件 A 发生的概率：P(A|B)=P(A∩B)/P(B)。如果 A 与 B 独立：P(A∩B)=P(A)P(B)。贝叶斯公式：P(A|B)=P(B|A)P(A)/P(B)。请使用 RecallForge 帮我复习这些内容。
```

正常结果应包含：知识结构、考试重点、主动回忆、至少一道练习题、下一步建议。如果只得到普通摘要，请显式使用 `$recallforge` 后重试。

## 仅在一个项目中安装

开发者可把 `skill/recallforge` 复制到：

```text
你的项目/.agents/skills/recallforge/SKILL.md
```

这样 RecallForge 只在该项目中可用。完整 Windows/macOS/Linux 指南、更新、卸载与 Codex 说明见[中文 Codex 教程](docs/codex.zh-CN.md)。

## 兼容性

| Host | 状态 | 已验证 |
|---|---|---|
| Codex 本地 Skill | 支持 | 是：安装包、安装脚本和发现目录已验证 |
| Codex Skill Installer | 支持 | 是：已按官方 GitHub 安装契约设计 |
| Codex Plugin | 支持 | 本地 manifest 和包结构已验证 |
| 其他 Agent Skills 宿主 | 标准兼容 | 未逐一验证 |
| ChatGPT Desktop UI | 含 OpenAI metadata | 未在 UI 中实测 |

RecallForge 的价值不在于“总结 PDF”，而在于：资料 → 知识结构 → 考试优先级 → 主动回忆 → 薄弱点 → 针对性复习 → 模拟考试的学习闭环。
