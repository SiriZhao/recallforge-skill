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

尚未完成。维护者必须在独立的 Codex 会话中按[正式宿主验收协议](manual-verification.zh-CN.md)执行真实 E2E。机器可读证据模板位于 [verification/host-verification-template.json](../verification/host-verification-template.json)。
