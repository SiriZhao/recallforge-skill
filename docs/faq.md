# FAQ

### My PDF is scanned. What happens?
Each page is checked separately. Image-only or unreliable pages route to host vision; optional local OCR can recover text when explicitly enabled.

### My slides are mostly images. Will text extraction be enough?
No. RecallForge preserves native slide text but asks the host to inspect rendered slides for layout, arrows, comparisons, and diagrams.

### What if a formula is recognized incorrectly?
Native, OCR, and vision interpretations remain separate. A conflict lowers confidence and should be shown with its source so you can provide a clearer crop.

### Can it understand chemical structures or biological diagrams?
There is a host-vision path that preserves them as visual concepts. Quality depends on the host and source image; it is not claimed as universally verified.

### Can it read handwriting?
Potentially through host vision or optional OCR, but handwriting is labeled as user/unknown annotation and never treated as a verified answer automatically.

### Does it support Chinese or mixed Chinese-English material?
The IR and fixtures support Chinese, English, and mixed-language hints. Actual scan recognition depends on host vision or the optional OCR engine/language data installed by the user.

### Can I upload a 300-page PDF or a whole semester?
Start with a catalog and fast scan. RecallForge should build a course map and deepen priority chunks instead of placing everything in context at once. Host upload/context limits still apply.

### Does RecallForge OCR every page?
No. Reliable digital text stays native. OCR is only an optional fallback for pages that need it.

### Where does my material go?
RecallForge runs no server or upload service. Processing follows the policies of your selected AI host/model provider. Optional local preprocessing stays wherever you configure its workspace.

### Why was a page marked uncertain?
Typical reasons are low resolution, conflicting text/vision, complex formulas, multi-column order, overlapping handwriting, or unrecoverable table structure.

### Why did I only get a summary?
Invoke `$recallforge` explicitly, ask it to inspect material first, and request diagnostic recall. Confirm it appears in `/skills` where that surface is available.

### Is local OCR or Python required?
No for the core Skill. Python and local OCR are optional developer/local-preprocessing paths.

### Why can’t `/skills` find RecallForge?
Verify that the final path is `.agents/skills/recallforge/SKILL.md`, not a nested `recallforge/recallforge/SKILL.md`, then start a new Codex turn or restart the host.
