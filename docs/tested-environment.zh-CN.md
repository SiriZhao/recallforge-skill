# 已验证环境

## CI 矩阵（通过）

GitHub Actions `Validate` 工作流在以下环境通过：

- Ubuntu 24.04，Python 3.10 和 3.11
- Windows Server 2025（windows-latest），Python 3.11
- macOS（macos-latest），Python 3.11

每个任务都会运行完整自动化测试、打包、Clean Room ZIP/Plugin 安装检查、原生资料摄取基准、官方 Skill/Plugin 校验，以及品牌和占位符扫描。

## 本地 OCR 参考

Windows 11、Python 3.14.3、Intel64 Family 6 Model 197、仅 CPU：

- Tesseract 5.5.0，官方 `eng` + `chi_sim` 语言数据
- RapidOCR 1.2.3（ONNX Runtime CPU）

完整结果：[benchmarks/results/ocr-windows-reference.json](../benchmarks/results/ocr-windows-reference.json) 和[本地 OCR 验证](ocr.zh-CN.md)。

## 包验证

- 官方 Skill 校验器：通过
- 官方 Plugin 校验器：通过
- Clean Room ZIP 安装到临时目标：通过
- Clean Room Plugin 解压和相对引用检查：通过
- SHA256SUMS 可复现：通过

## 宿主验证

已在独立 Codex 会话中由维护者在 Windows 11 上完成（EXTERNAL_MANUAL）：

- Codex 0.147.0
- RecallForge commit `1856c66`
- Candidate ZIP，用户级 Skill 安装
- `/skills` 发现：通过
- `$recallforge self-test`：通过（`Status: READY`）
- `$recallforge multimodal-test`：通过（`Status: MULTIMODAL_READY`）
- 功能测试：通过
- 真实资料 E2E：通过（16 份课件 + 30 页扫描历年试题 PDF；共 1047 个课件页/幻灯片 + 30 个试题页完成编目）
- 薄弱点反馈闭环：通过（诊断式主动回忆 → 薄弱点定位 → 纠正教学 → 跟进练习，包括用户请求从诊断模式切换到从零教学）

完整机器可读证据：[verification/host-verification-template.json](../verification/host-verification-template.json)。
