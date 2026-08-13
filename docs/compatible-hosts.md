# Compatible hosts

RecallForge Core is the portable `skill/recallforge/` folder: standard `SKILL.md`, references, self-test material, and optional OpenAI UI metadata. Codex is the primary verified host. Other Agent Skills hosts may load the core folder if they support this format, but they are not individually verified and may ignore `agents/openai.yaml`.

The skills-only Plugin is an OpenAI-specific adapter. It contains the same core Skill under `skills/recallforge/` and adds `.codex-plugin/plugin.json`; it does not include an MCP server, database, backend, or API service.
