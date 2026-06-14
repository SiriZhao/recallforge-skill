# Security Policy

## Reporting Security Issues

Please do not open public issues for sensitive security reports. If this project is hosted under your GitHub account, configure a private security contact or GitHub Security Advisories, then report issues there.

If no private channel is configured yet, open a minimal public issue saying that you have a security concern without including exploit details, secrets, private files, or personal data.

## Sensitive Data Rules

Do not commit:

- API keys or access tokens
- `.env` files
- student names, IDs, grades, or private records
- private course materials
- restricted exams or leaked questions
- paid copyrighted materials
- OCR caches or generated outputs containing private material

Use `.env.example` for configuration examples. Keep real secrets only in local environment variables or secret managers.
