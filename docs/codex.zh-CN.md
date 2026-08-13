# 在 Codex 中使用 RecallForge

RecallForge 是 Codex Skill。它不需要 Python、API Key 或独立程序；Codex 在对话中读取 `SKILL.md` 和附带参考资料。

## 安装

### Windows

下载并解压 `recallforge-skill-v2.1.2.zip`。在文件资源管理器地址栏输入 `%USERPROFILE%\.agents\skills`，按需要创建文件夹，将解压得到的 `recallforge` 文件夹复制进去。最终必须是：`%USERPROFILE%\.agents\skills\recallforge\SKILL.md`。

也可在解压目录打开 PowerShell，运行：`powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1`。

### macOS

Finder 按 Shift-Command-G，输入 `~/.agents/skills`，按需要创建该目录，再复制 `recallforge`。其中 `~` 表示你的用户主目录。

### Linux

```bash
mkdir -p ~/.agents/skills
cp -R /path/to/extracted/recallforge ~/.agents/skills/
```

macOS/Linux 也可从解压目录运行：`bash ./scripts/install.sh`。

## 验证与开始

开启一个新的 Codex 对话；Codex 会自动发现本地 Skills。如果你使用的界面提供 Skills 选择器，确认其中有 **RecallForge**。然后输入：

```text
$recallforge self-test
```

出现 `Status: READY` 即安装正确。本环境没有可截图的 Codex UI，因此没有把示意图伪装成真实 UI 截图。

更新时下载新 ZIP，仅替换 `recallforge` 文件夹，开新对话并重新 self-test。卸载时只删除 `recallforge` 文件夹，绝不要删除整个 `.agents/skills`。
