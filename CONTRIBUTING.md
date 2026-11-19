# Contributing to Reyal

## Source of Truth

`CONTRIBUTING.md` is the single source of truth for project workflow and contribution rules.

## Git Workflow

Use GitHub Flow with one permanent branch per Frappe version:

- `v16` for Frappe v16; the default branch, where new work goes
- `v15` for Frappe v15; fixes for sites still on v15

Both are protected: changes reach them only through pull requests whose required checks pass.

### Starting work

Branch from the version branch your change targets, here `v16`:

```bash
git checkout v16
git pull origin v16
git checkout -b feat/my-change
```

A change both versions need goes in two pull requests, one per branch.

Branch prefixes:

- `feat/` for new functionality
- `fix/` for bug fixes
- `chore/` for maintenance/config/dependency work
- `refactor/` for structure-only changes (no behavior change)

### Committing

```bash
git add <specific-files>
git commit -m "type: short description"
```

Commit types: `feat`, `fix`, `bump`, `chore`, `refactor`, `docs`.

### Local quality checks

Run these checks before opening a pull request:

```bash
uv run --with ruff ruff check .
uv run --with ruff ruff format --check .
uv run --with pytest pytest
```

Ruff checks Python lint rules and formatting; pytest runs the automated test suite.

### Pull requests

- Never push directly to `v15` or `v16`.
- Open a PR for every change, targeting the version branch it was branched from.
- Before opening a PR, run local validation on your target site:

```bash
bench --site <site> migrate
bench --site <site> clear-cache
bench restart
```

- Confirm your feature works locally after these commands.
- If the target branch moved while you were working, rebase before opening/updating the PR:

```bash
git fetch origin
git rebase origin/v16
```

### After merge

Delete the feature branch locally and on origin.

## Versioning and Releases

- Bump `reyal_core/__init__.py` (`__version__`) with each PR.
- Use each version number once across both branches: check `git tag` and both branches' `CHANGELOG.md` before bumping, so a `v15` fix never reuses a number already taken on `v16`.
- Keep `CHANGELOG.md` updated.
- After merge to a version branch, tag the release from it:

```bash
git checkout v16 && git pull origin v16
git tag v<version>
git push origin v<version>
```

Tag must match `__version__` prefixed with `v`.

## Deployment

After merging to a version branch, on each site running that Frappe version:

```bash
bench --site <site> migrate
bench --site <site> clear-cache
bench restart
```

## AI Assistant Instruction Files

Local AI assistant files (for example `CLAUDE.md` and `CODEX.md`) are allowed for personal tooling, but:

- They must be derived from this `CONTRIBUTING.md`.
- They must not contain extra policy that conflicts with this file.
- They must never be tracked or pushed to GitHub.

This repository ignores these local files via `.gitignore`.

If one is ever tracked by mistake, untrack it without deleting your local copy:

```bash
git rm --cached CLAUDE.md CODEX.md
```
