# Contributing to Reyal Core

## Source of Truth

`CONTRIBUTING.md` is the single source of truth for project workflow and contribution rules.

## Git Workflow

Use GitHub Flow with `main` as the only permanent branch.

### Starting work

```bash
git checkout main
git pull origin main
git checkout -b feat/my-change
```

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

### Pull requests

- Never push directly to `main`.
- Open a PR for every change.
- If `main` moved while you were working, rebase before opening/updating the PR:

```bash
git fetch origin
git rebase origin/main
```

### After merge

Delete the feature branch locally and on origin.

## Versioning and Releases

- Bump `reyal_core/__init__.py` (`__version__`) with each PR.
- Keep `CHANGELOG.md` updated.
- After merge to `main`, tag the release:

```bash
git checkout main && git pull origin main
git tag v<version>
git push origin v<version>
```

Tag must match `__version__` prefixed with `v`.

## Deployment

After merging to `main`:

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
