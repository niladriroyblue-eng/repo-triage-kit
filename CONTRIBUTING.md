# Contributing

Thanks for helping improve the maintainer workflow.

## Contribution guidelines

- Keep triage signals explainable and optional.
- Preserve read-only behavior. Any proposed write action needs a separate design review and explicit opt-in.
- Do not add network destinations or runtime dependencies without explaining the need.
- Use fictional repository and issue data in documentation and examples.
- Keep tokens out of command-line arguments, logs, fixtures, and pull requests.
- Include a clear problem statement and user-facing behavior in pull requests.

## Local development

Install with `python -m pip install -e .`. Run `repo-triage --input examples/sample-issues.json` to generate a sample report.
