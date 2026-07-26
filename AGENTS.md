# InternFlow development guide

## Product

InternFlow is a privacy-friendly, open-source internship application tracker for
students. The first release must make the full job-tracking workflow reliable
before adding AI features.

## Architecture

- Keep a modular Django monolith. Do not introduce microservices.
- Use server-rendered Django templates and HTMX for focused interactions.
- Keep JavaScript optional and small. Core workflows must work without HTMX.
- Use SQLite for the zero-config local experience and PostgreSQL in containers
  and production.
- Keep every query scoped to the authenticated user.
- Put business rules in models/forms/services rather than templates.
- Prefer Django built-ins before adding dependencies.

## Commands

- Install: `uv sync --locked --dev`
- Database: `uv run python manage.py migrate`
- Development: `uv run python manage.py runserver`
- Tests: `uv run pytest`
- Coverage: `uv run pytest --cov`
- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Format: `uv run ruff format .`
- Django checks: `uv run python manage.py check`
- Production checks: `uv run python manage.py check --deploy`

## Definition of done

A change is complete only when:

1. Its user-visible acceptance criteria work.
2. Ownership and permission boundaries are covered by tests.
3. Tests, lint, formatting, migrations, and Django checks pass.
4. User-facing behavior and setup documentation are current.
5. No secret, credential, personal email, or generated database is committed.

Never skip or weaken a check to make a build pass. Fix the underlying problem.

## UX

- Write concise Chinese product copy with accessible labels.
- Support keyboard navigation, visible focus, reduced motion, and small screens.
- Use realistic demo content, not lorem ipsum.
- Empty, loading, validation, and error states are part of each feature.

## Git

- Keep commits small and coherent.
- Use imperative commit subjects.
- Never rewrite user-authored history or force-push.
- Update `docs/interview-notes.md` when an architectural decision or useful
  interview topic appears.
