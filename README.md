# Repo Triage Kit

**A read-only triage snapshot for GitHub maintainers.**

**Release status: beta (0.1.0b1).** This is an early release. CLI options and report output may change before a stable release. Please report problems through GitHub Issues and avoid relying on the output as an automated priority score.

Repo Triage Kit turns open GitHub issues and pull requests into a small, explainable review queue. It flags unanswered items, unlabeled items, and stale activity so maintainers can decide what deserves attention. It never labels, assigns, closes, or comments on work.

## Why this exists

Maintainers often have to find unanswered reports and stalled changes across a growing repository. This tool focuses on a few transparent metadata signals, keeps the result in a Markdown or JSON report, and leaves every decision with a human.

## What it does

- Reads open issues and pull requests from the GitHub API, or a local JSON export.
- Flags items with no response, no labels, or stale activity using configurable day thresholds.
- Produces Markdown for a GitHub Actions job summary or JSON for other tools.
- Uses Python's standard library at runtime; no LLM or third-party service is involved.
- Uses read-only GitHub permissions in the included workflow example.

## Beta scope

This beta is intentionally small: it reports three transparent signals and leaves decisions to maintainers. It has not yet established a public user base or adoption record. Feedback from real maintainers should guide what becomes stable and what changes next.

## Quick start

Requires Python 3.11 or newer.

```sh
python -m pip install .
repo-triage --input examples/sample-issues.json --now 2026-11-02T12:00:00Z
```

To scan a public repository, no token is required for a small number of requests:

```sh
repo-triage --repo owner/name
```

For private repositories or higher API limits, provide a token with **read-only** access to repository issues and pull requests:

```sh
GITHUB_TOKEN=... repo-triage --repo owner/name --format json --output triage.json
```

The token is read from the environment and is never printed by the tool. Do not pass it as a command-line argument in shared terminals or logs.

## GitHub Action

The repository includes a composite action that writes a Markdown snapshot to the job summary. After publishing a versioned release, add the following permissions and workflow to a repository:

```yaml
name: Maintainer triage snapshot

on:
  workflow_dispatch:
  schedule:
    - cron: "17 8 * * 1"

permissions:
  issues: read
  pull-requests: read

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - uses: niladriroyblue-eng/repo-triage-kit@v0
        with:
          repository: ${{ github.repository }}
          token: ${{ github.token }}
```

Publish a `v0` release tag before using this example. The action makes read-only API requests and appends its report to `$GITHUB_STEP_SUMMARY`.

## Triage rules

By default, items are flagged when they have no comments after 7 days, have no labels after 7 days, or have no activity for 30 days. These are reminders for a human, not quality scores. Tune them with `--first-response-days` and `--stale-days`.

## Input format

`--input` accepts the array returned by GitHub's issues endpoint or an object with an `items` array and optional `repository` name. Records use standard GitHub issue fields such as `number`, `title`, `created_at`, `updated_at`, `comments`, `labels`, and `pull_request`.

## Privacy and safety

- The tool sends GitHub requests only to `api.github.com` when `--repo` is used.
- Local JSON mode makes no network requests.
- Reports contain issue and pull-request titles and URLs; treat them as repository data.
- The tool does not perform write operations or send data to an AI service.
- Review permissions before adding the Action to a repository. The included example grants only `issues: read` and `pull-requests: read`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep the project dependency-light, explain triage signals in plain language, and preserve the read-only behavior.

## License

MIT. See [LICENSE](LICENSE).
