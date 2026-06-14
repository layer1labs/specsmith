# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Software engineering workflow skills — code review, TDD, debugging, security, etc."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="code-review",
        name="Code Review — systematic pull request review workflow",
        description=(
            "Structured checklist for reviewing pull requests: correctness, design, "
            "security, tests, and style. Use when reviewing a PR, conducting a self-review "
            "before requesting review, or establishing a team review standard."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "code-review",
            "pull-request",
            "pr",
            "review",
            "checklist",
            "quality",
            "security",
            "design",
        ],
        body="""\
# Code Review

A good review catches bugs, improves design, and shares knowledge.
A bad review is just style nitpicking. This skill focuses on what matters.

## When to use
- Reviewing someone else's PR
- Self-reviewing before requesting review
- Establishing or improving a team review standard

## Review priority order

### 1. Correctness (highest priority)
- Does the code do what the PR description says?
- Are edge cases handled? (null, empty, overflow, concurrent access)
- Are error paths handled and properly propagated?

### 2. Security
- SQL injection, XSS, SSRF, path traversal in any user input paths?
- Secrets or credentials hardcoded or logged?
- Authentication / authorisation checks on every new endpoint?
- Dependencies added — are they from trusted sources?

### 3. Design
- Does this change fit the existing architecture, or does it cut across it awkwardly?
- Is there unnecessary complexity? (could this be 10 lines instead of 100?)
- Are abstractions at the right level?
- Will this be easy to change in 6 months?

### 4. Tests
- Are there tests for the new behaviour?
- Do the tests actually fail if the code is wrong? (not just coverage theatre)
- Are edge cases and error paths tested?

### 5. Performance
- Any N+1 queries, missing indexes, or O(n²) loops on large inputs?
- Memory allocations inside hot loops?
- Blocking I/O in async code?

### 6. Style (lowest priority — automate this)
- If a formatter/linter is configured, it handles style automatically
- Only comment on style if it genuinely hurts readability

## Comment tone guide
| Intent | Example |
|--------|---------|
| Blocker | `[blocker] This will panic on empty input — must fix` |
| Suggestion | `[nit] Could simplify with list comprehension` |
| Question | `[?] Why does this need a mutex here?` |
| Praise | `[👍] Nice use of the existing abstraction` |

## Red flags that require a second look
- Any `# type: ignore` or `@ts-ignore` without explanation
- `TODO: fix this properly` in new code
- Disabled security checks (`nosec`, `skipcq`)
- `print()` or `console.log()` in non-test code
- Catch-all exception handlers that swallow errors

## Verification checklist
- [ ] Correctness verified against PR description
- [ ] Security checklist reviewed for input handling
- [ ] Tests cover the new behaviour and at least one failure mode
- [ ] No unreviewed dependency additions
- [ ] Performance implications considered for hot paths
""",
    ),
    SkillEntry(
        slug="test-driven-development",
        name="Test-Driven Development — red-green-refactor workflow",
        description=(
            "Strict TDD workflow: write a failing test first, make it pass, then refactor. "
            "Use when implementing new functionality, fixing bugs, or when feature scope "
            "is unclear and tests will help drive the design."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "tdd",
            "test-first",
            "red-green-refactor",
            "unit-test",
            "pytest",
            "jest",
            "design",
            "specification",
        ],
        body="""\
# Test-Driven Development

TDD is a design technique, not just a testing technique. The test specifies
the behaviour before the implementation forces any design decisions.

## When to use
- Implementing new functionality with clear acceptance criteria
- Fixing a bug (write a failing test that reproduces it first)
- When the scope is unclear — tests clarify the interface

## The cycle (strictly in this order)

```
RED   → Write a failing test that describes one behaviour
GREEN → Write the minimum code to make the test pass
REFACTOR → Clean up — the test stays green
```

Never skip RED. If you write code before a test, you are not doing TDD.

## Step 1: RED — write a failing test

```python
# test_calculator.py
def test_add_two_positive_numbers():
    calc = Calculator()
    assert calc.add(2, 3) == 5  # This MUST fail right now
```

Run it: `pytest test_calculator.py::test_add_two_positive_numbers`
Confirm it fails with `AttributeError` or `ImportError` — not a passing test.

## Step 2: GREEN — minimum viable implementation

```python
# calculator.py — write ONLY enough to pass this one test
class Calculator:
    def add(self, a, b):
        return a + b
```

Run the test again. It must now pass. Do NOT add more than this.

## Step 3: REFACTOR — clean up

- Extract common setup to `@pytest.fixture`
- Remove duplication
- Rename for clarity
- Tests stay green throughout

## One test at a time

Never write two failing tests at once. Focus on one behaviour:
- `test_add_two_positive_numbers`
- `test_add_returns_float_when_inputs_are_float`
- `test_add_raises_on_non_numeric_input`

## Common rationalizations
| Rationalization | Reality |
|---|---|
| "I'll write tests after I get it working" | "After" never comes; design becomes harder to test |
| "This code is too simple to test" | Simple code has simple tests — write them anyway |
| "The test is taking too long to write" | The design is hard to test — this is valuable signal |

## Verification checklist
- [ ] Test written BEFORE implementation
- [ ] Test confirmed failing before writing code
- [ ] Implementation passes test without modifying the test
- [ ] Refactoring completed with tests still green
- [ ] Edge cases and error conditions tested
""",
    ),
    SkillEntry(
        slug="debugging",
        name="Debugging — systematic error diagnosis and recovery",
        description=(
            "Structured approach to debugging: reproduce, isolate, hypothesise, verify, fix. "
            "Use when investigating any bug, error, or unexpected behaviour — especially "
            "before spending more than 10 minutes on a problem."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "debugging",
            "error",
            "bug",
            "diagnosis",
            "logging",
            "breakpoint",
            "traceback",
            "root-cause",
        ],
        body="""\
# Debugging

Debugging without a method is guessing. This skill gives you a method.

## When to use
- Any error, unexpected output, or failing test
- Before spending more than 10 minutes on a problem

## The method (always in this order)

### 1. Reproduce reliably
You cannot fix what you cannot reproduce. Find the minimal case:
- Which inputs / conditions trigger it?
- Does it happen every time or intermittently?
- What is the smallest code path that triggers it?

### 2. Read the error message (actually read it)
```
TypeError: unsupported operand type(s) for +: 'int' and 'str'
  File "app.py", line 42, in calculate_total
    total = base_price + discount
```
The message tells you: what went wrong, where, and often why.
Read the full traceback from the bottom up.

### 3. Isolate — binary search the codebase
```python
# Narrow down with bisect strategy
# Is the problem in the input? → print/log inputs at the entry point
# Is the problem in the processing? → log at midpoint
# Is the problem in the output? → log just before return
print(f"DEBUG input: {base_price=}, {discount=}")
```

### 4. Hypothesise and verify one hypothesis at a time
Write down your hypothesis before testing it:
- "I think `discount` is a string because it comes from JSON"
- Test: `print(type(discount), repr(discount))`
- Confirm or refute — don't move to the next hypothesis until this one is done

### 5. Use the right tool
| Situation | Tool |
|-----------|------|
| Python traceback | Read it; add `python -Xdev` for extra checks |
| Intermittent bug | Add structured logging; use `bisect` on git history |
| Wrong values | `pdb.set_trace()` or IDE debugger breakpoints |
| Performance | `cProfile`, `py-spy`, Chrome DevTools flame chart |
| Network issue | `curl -v`, Wireshark, `httpie` |
| Memory leak | `tracemalloc`, Valgrind, heapdump |

### 6. Fix the root cause, not the symptom
```python
# Symptom fix (wrong)
total = int(base_price) + int(discount)

# Root cause fix (right) — fix at the source where data enters
discount = float(request_data["discount"])  # type coercion at input boundary
```

## Rubber duck debugging
Explain the problem out loud (to a colleague, rubber duck, or AI) before
asking for help. The act of articulating it often reveals the cause.

## Verification checklist
- [ ] Bug reproduced with a minimal, reliable test case
- [ ] Root cause identified (not just a symptom)
- [ ] Fix applied at the root cause, not the symptom
- [ ] Regression test written to prevent recurrence
- [ ] Logs/print statements removed before committing
""",
    ),
    SkillEntry(
        slug="refactoring",
        name="Refactoring — improving code structure without changing behaviour",
        description=(
            "Safe refactoring workflow: test coverage first, small atomic changes, "
            "continuous verification. Use when improving readability, reducing duplication, "
            "extracting abstractions, or preparing code for a new feature."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "refactoring",
            "clean-code",
            "extract",
            "rename",
            "simplify",
            "dead-code",
            "duplication",
            "abstraction",
        ],
        body="""\
# Refactoring

Refactoring = improving code structure while keeping behaviour identical.
If behaviour changes, that is a bug fix, not a refactor.

## When to use
- Code is hard to understand or modify
- Duplication that slows down changes
- Preparing for a new feature (make it easy to change, then change it)
- After a bug fix (clean up the surrounding code)

## The non-negotiable prerequisite: tests

Do not refactor untested code without first writing characterisation tests:
```python
# Characterisation test: records what the code currently does
def test_legacy_calculate_price_for_known_inputs():
    # Whatever the current code returns, assert that
    assert calculate_price(100, 0.1) == 90.0  # observed output
```

## Safe refactoring steps

### Extract function
```python
# Before
total = (price * quantity) * (1 - discount) + shipping_cost

# After
def subtotal(price, quantity, discount):
    return (price * quantity) * (1 - discount)

total = subtotal(price, quantity, discount) + shipping_cost
```

### Replace magic number with named constant
```python
# Before
if retries > 3: ...

# After
MAX_RETRIES = 3
if retries > MAX_RETRIES: ...
```

### Inline variable (remove unnecessary intermediaries)
```python
# Before
result = calculate()
return result

# After
return calculate()
```

### Rename for clarity (use the language of the domain)
```python
# Before: x, data, temp, stuff, manager, handler, processor
# After: invoice, customer_id, unpaid_invoices, payment_processor
```

## Refactoring workflow
1. Confirm tests pass (green)
2. Make ONE small change
3. Run tests (must stay green)
4. Commit with message `refactor: <what you changed and why>`
5. Repeat

Never refactor and add features in the same commit.

## Red flags that need refactoring
- Functions > 20 lines with multiple responsibilities
- Deeply nested conditionals (> 3 levels)
- Duplicated code blocks
- Boolean parameters that flip behaviour: `process(data, True)`
- God classes with > 500 lines

## Verification checklist
- [ ] Tests green before starting
- [ ] Each change is atomic and tested immediately
- [ ] No behaviour changed (run the full test suite after)
- [ ] Commits separate from feature work
- [ ] Complexity metrics improved (function length, nesting depth)
""",
    ),
    SkillEntry(
        slug="security-hardening",
        name="Security Hardening — application security review and remediation",
        description=(
            "OWASP-aligned security review checklist for web apps, APIs, and CLIs. "
            "Use before any production deployment, after adding authentication/authorisation "
            "code, or when integrating third-party services or user-supplied input."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "security",
            "owasp",
            "injection",
            "xss",
            "csrf",
            "auth",
            "secrets",
            "dependency-audit",
            "hardening",
            "penetration-testing",
        ],
        body="""\
# Security Hardening

Security is not a feature — it's a property of the whole system.
This skill covers the top issues found in production code reviews.

## When to use
- Before any production deployment
- After adding authentication/authorisation code
- When integrating third-party services
- After a security incident or CVE disclosure

## OWASP Top 10 checklist

### 1. Injection (SQL, command, LDAP)
```python
# Never do this
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Always do this
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### 2. Broken authentication
- Passwords hashed with bcrypt/argon2 (never SHA-1/MD5)
- Session tokens are random (not sequential IDs)
- Failed login rate-limited and logged
- MFA available for privileged accounts

### 3. Sensitive data exposure
- HTTPS enforced everywhere (HSTS header set)
- PII not logged (mask or drop before logging)
- Secrets in environment variables, not code
- Database columns containing PII encrypted at rest

### 4. Insecure direct object references (IDOR)
```python
# Wrong: user can access any record by guessing IDs
@app.get("/invoice/{id}")
def get_invoice(id: int):
    return db.get(id)

# Right: always scope to authenticated user
@app.get("/invoice/{id}")
def get_invoice(id: int, user=Depends(get_current_user)):
    invoice = db.get(id)
    if invoice.owner_id != user.id:
        raise HTTPException(403)
    return invoice
```

### 5. Security misconfiguration
- Debug mode OFF in production
- Verbose error messages not shown to users
- CORS configured narrowly (not `*`)
- Security headers set: CSP, X-Frame-Options, HSTS

### 6. XSS (Cross-Site Scripting)
- All user input HTML-escaped on output
- Content-Security-Policy header blocks inline scripts
- `innerHTML` never used with user content

### 7. Insecure deserialisation
- Never `pickle.loads()` user-supplied data
- JSON schema validation on all API inputs
- File uploads restricted by MIME type and scanned

### 8. Vulnerable dependencies
```bash
# Python
pip-audit

# Node.js
npm audit

# GitHub Actions — enable Dependabot in repo settings
```

### 9. Insufficient logging and monitoring
- All authentication events logged (login, logout, failed attempts)
- All privilege escalation events logged
- Logs shipped to SIEM; alert on anomalies

## Quick wins (15 minutes each)
1. `pip-audit` or `npm audit` — fix critical/high CVEs
2. Add `Strict-Transport-Security`, `X-Content-Type-Options` headers
3. Check for hardcoded secrets: `git grep -E "(api_key|secret|password)\\s*=\\s*['\"]"`
4. Rotate any secrets found in git history immediately

## Verification checklist
- [ ] Dependency audit clean (no critical/high CVEs)
- [ ] All user inputs validated and sanitised
- [ ] No secrets in code or git history
- [ ] Authentication flows reviewed (login, session, MFA)
- [ ] IDOR checks on all resource endpoints
- [ ] Security headers configured
- [ ] Logging covers auth and privilege events
""",
    ),
    SkillEntry(
        slug="performance-optimization",
        name="Performance Optimization — profiling and resolving performance bottlenecks",
        description=(
            "Profiling-first workflow for performance work: measure, identify, fix, measure "
            "again. Use when an application is slow, when scaling issues appear, or before "
            "adding caching (which requires knowing what to cache)."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "performance",
            "profiling",
            "caching",
            "database",
            "n+1",
            "async",
            "memory",
            "latency",
            "throughput",
            "benchmark",
        ],
        body="""\
# Performance Optimization

Never optimise without profiling first. Guessing where the bottleneck is
wastes time and often makes code worse without improving performance.

## When to use
- Application is slow and users are complaining
- Scaling issues: works for 10 users, breaks at 1000
- Before adding caching (know what to cache)
- After a performance regression in CI

## Step 1: Measure baselines

Before touching any code, establish what "slow" means with numbers:
```bash
# HTTP endpoint
hey -n 1000 -c 50 http://localhost:8000/api/endpoint

# Python function
python -m timeit -s "from mymodule import fn" "fn(test_data)"
```

## Step 2: Profile — find the actual bottleneck

### Python
```bash
# CPU profiling
python -m cProfile -o profile.out myapp.py
python -m pstats profile.out  # then: sort cumulative, stats 20

# Continuous profiling (production-safe)
py-spy top --pid $(pgrep -f myapp)
```

### Node.js
```bash
node --prof app.js
node --prof-process isolate-*.log > profile.txt
```

### Database queries
```sql
-- PostgreSQL: find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 20;

-- Add EXPLAIN ANALYZE before any slow query
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

## Step 3: Fix the highest-impact issue first

### Database N+1 queries (most common)
```python
# N+1: hits the DB once per item
for order in orders:
    print(order.customer.name)  # separate query each time

# Fixed: eager-load in one query
orders = Order.objects.select_related("customer").all()
```

### Missing index
```sql
-- Check if a query does a full table scan
EXPLAIN SELECT * FROM orders WHERE customer_id = 123;
-- If Seq Scan → add index
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

### Unnecessary computation in loops
```python
# Bad: compiles regex on every iteration
for item in items:
    if re.match(r"\\d+", item):  # compiled fresh each time
        ...

# Good: compile once
PATTERN = re.compile(r"\\d+")
for item in items:
    if PATTERN.match(item):
        ...
```

### I/O-bound: make it async
```python
# Bad: sequential I/O
results = [await fetch(url) for url in urls]

# Good: parallel I/O
results = await asyncio.gather(*[fetch(url) for url in urls])
```

## Step 4: Measure again

Confirm the fix actually improved the metric. Revert if it did not.

## Verification checklist
- [ ] Baseline benchmark recorded before changes
- [ ] Profiler output analysed (not guessed)
- [ ] Change targets the hottest path in the profile
- [ ] After-fix benchmark shows measurable improvement
- [ ] No correctness regressions (test suite green)
""",
    ),
    SkillEntry(
        slug="api-design",
        name="API Design — REST, GraphQL, and gRPC API design principles",
        description=(
            "Principles and patterns for designing clean, consistent, and evolvable APIs. "
            "Use when designing a new API surface, reviewing an existing API for consistency, "
            "or choosing between REST, GraphQL, and gRPC."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "api",
            "rest",
            "graphql",
            "grpc",
            "openapi",
            "versioning",
            "pagination",
            "error-handling",
            "idempotency",
        ],
        body="""\
# API Design

An API is a contract. Breaking the contract breaks your users.
Design it right the first time.

## When to use
- Designing a new HTTP API or gRPC service
- Reviewing an existing API for consistency problems
- Choosing between REST, GraphQL, and gRPC

## Choose the right protocol

| Use REST when | Use GraphQL when | Use gRPC when |
|--------------|-----------------|--------------|
| Simple CRUD resources | Clients need flexible queries | Internal microservices |
| Public API | Mobile apps (bandwidth-sensitive) | High-performance streaming |
| Cacheability matters | Multiple resource types per request | Strong typing required |

## REST design rules

### Resource naming
```
GET    /orders              ← list
POST   /orders              ← create
GET    /orders/{id}         ← get one
PUT    /orders/{id}         ← replace
PATCH  /orders/{id}         ← partial update
DELETE /orders/{id}         ← delete
```
- Nouns for resources, verbs for actions: `/orders`, not `/getOrder`
- Plural: `/orders`, not `/order`
- Nested: `/orders/{id}/items` for tight relationships

### Status codes (use them correctly)
| Code | When |
|------|------|
| 200 | Success with body |
| 201 | Created (POST) — include `Location` header |
| 204 | Success, no body (DELETE) |
| 400 | Client error (validation, malformed request) |
| 401 | Not authenticated |
| 403 | Authenticated but not authorised |
| 404 | Resource not found |
| 409 | Conflict (duplicate, state mismatch) |
| 422 | Unprocessable entity (semantic errors) |
| 429 | Rate limited |
| 500 | Server error (never expose internals) |

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true,
    "total": 1234
  }
}
```
Use cursor-based pagination for large collections (not offset).

### Error responses
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "field": "email",
    "request_id": "req_abc123"
  }
}
```
Always include a machine-readable `code` and human-readable `message`.

### Versioning
- URL versioning: `/v1/orders` (simple, explicit)
- Avoid breaking changes by adding fields (never removing)
- Deprecate in v1 → remove in v2 with migration guide

## API documentation
- OpenAPI 3.x spec for REST — generate from code or write first
- Every endpoint: description, all parameters, all response codes
- Example request/response for each endpoint

## Verification checklist
- [ ] Resource names are nouns, plural
- [ ] HTTP methods match semantics (GET is idempotent, POST is not)
- [ ] Error responses have consistent structure with machine-readable codes
- [ ] Pagination implemented for all list endpoints
- [ ] OpenAPI spec generated and validated
- [ ] Breaking changes handled with versioning strategy
""",
    ),
    SkillEntry(
        slug="database-design",
        name="Database Design — schema design, migrations, and query optimisation",
        description=(
            "Principles for relational database schema design: normalisation, indexing, "
            "migrations, and query patterns. Use when designing a new schema, adding tables "
            "or columns, or diagnosing slow queries."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "database",
            "postgresql",
            "mysql",
            "schema",
            "migration",
            "index",
            "normalisation",
            "foreign-key",
            "query",
            "sql",
        ],
        body="""\
# Database Design

Bad schema design is technical debt that compounds. Fix it at the start.

## When to use
- Designing a new database schema
- Adding tables or columns to an existing schema
- Diagnosing slow queries or missing indexes

## Schema design principles

### Normalisation (aim for 3NF for most cases)
- Each column depends on the primary key, not on other non-key columns
- No repeating groups (use a related table instead of `tag1`, `tag2`, `tag3` columns)
- No transitive dependencies

### Primary keys
```sql
-- UUID: portable, safe for distributed systems
id UUID PRIMARY KEY DEFAULT gen_random_uuid()

-- BIGSERIAL: compact, faster for joins, but exposes record count
id BIGSERIAL PRIMARY KEY
```
Use UUIDs for public-facing IDs; use bigserial for internal join tables.

### Naming conventions
```sql
-- Tables: plural, snake_case
CREATE TABLE order_items (...)

-- Columns: snake_case, descriptive
customer_id, created_at, is_active, total_amount_cents

-- Indexes: idx_<table>_<columns>
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

### Timestamps
Every table should have:
```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### Foreign keys
Always define foreign key constraints — they prevent orphaned records:
```sql
customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT
```

## Indexing strategy

```sql
-- Index every foreign key column
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Composite index: match query patterns (leftmost prefix rule)
-- For: WHERE status = 'pending' AND created_at > '...'
CREATE INDEX idx_orders_status_created ON orders(status, created_at);

-- Partial index for common filtered queries
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';
```

## Migrations

```python
# Use a migration tool (Alembic for Python, Flyway for JVM, Liquibase)
# Each migration: one change, reversible

# alembic/versions/001_create_orders.py
def upgrade():
    op.create_table("orders", ...)
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])

def downgrade():
    op.drop_index("idx_orders_customer_id")
    op.drop_table("orders")
```

**Zero-downtime migration rules:**
1. Add columns as nullable; populate; then add NOT NULL constraint
2. Never rename columns — add new + deprecate old
3. Never drop columns without a deprecation period

## Verification checklist
- [ ] Primary keys on all tables
- [ ] Foreign key constraints defined
- [ ] Indexes on all FK columns and common filter columns
- [ ] `created_at`/`updated_at` on all tables
- [ ] Migrations are reversible
- [ ] No direct `ALTER TABLE` in production without migration tool
- [ ] `EXPLAIN ANALYZE` run on queries touching > 10K rows
""",
    ),
    SkillEntry(
        slug="dependency-management",
        name="Dependency Management — keeping dependencies secure and up to date",
        description=(
            "Workflow for auditing, updating, and pinning dependencies. Use when adding a "
            "new dependency, responding to a CVE, setting up automated updates, or preparing "
            "a reproducible build."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "dependencies",
            "pip",
            "npm",
            "cargo",
            "vulnerability",
            "cve",
            "dependabot",
            "pinning",
            "lockfile",
            "supply-chain",
        ],
        body="""\
# Dependency Management

Every dependency is code you did not write and cannot fully control.
Manage it deliberately.

## When to use
- Adding a new dependency to a project
- Responding to a CVE or security advisory
- Setting up automated dependency updates
- Preparing a reproducible build

## Adding a new dependency checklist

Before adding any dependency:
1. **Is it maintained?** — last commit within 12 months, open issues being addressed
2. **Is it popular?** — PyPI/npm weekly downloads > 10K
3. **Is it audited?** — look for known CVEs: `pip-audit`, `npm audit`
4. **Is the licence compatible?** — GPL in a proprietary project is a legal issue
5. **What is the transitive dep count?** — `pipdeptree`, `npm ls`
6. **Can you implement it yourself in < 100 lines?** — if yes, consider not adding the dep

## Python

```bash
# Install and pin
pip install requests==2.31.0
pip freeze > requirements.txt

# Or with pyproject.toml + uv (preferred)
uv add requests

# Audit
pip-audit
pip-audit --fix  # auto-upgrade vulnerable packages

# Update all deps (check test suite after)
pip list --outdated
uv sync --upgrade
```

## Node.js

```bash
# Audit
npm audit
npm audit fix        # auto-fix non-breaking
npm audit fix --force  # may break — review before committing

# Update
npx npm-check-updates  # show available updates
npx npm-check-updates -u && npm install  # apply updates

# Lock file — always commit package-lock.json or yarn.lock
```

## Rust

```bash
cargo audit           # check for CVEs
cargo update          # update to latest compatible versions
cargo outdated        # show available updates
```

## Automated updates with Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Supply chain security

- Pin dependencies to exact versions in `requirements.txt` / `package-lock.json`
- Use trusted registries only (PyPI, npmjs.com, crates.io)
- Verify checksums in CI: `pip install --require-hashes`
- Never `curl | sh` to install dependencies in CI

## Verification checklist
- [ ] No critical/high CVEs in audit output
- [ ] Lock file committed and up to date
- [ ] Dependabot or Renovate configured for automated PRs
- [ ] New dependencies reviewed for maintenance and licence
- [ ] Transitive dependency count reviewed (no bloat)
""",
    ),
    SkillEntry(
        slug="git-workflow",
        name="Git Workflow — branching strategy, commit conventions, and history hygiene",
        description=(
            "Structured Git workflow covering branch naming, conventional commits, rebase "
            "vs merge, and history hygiene. Use when starting a new project, onboarding "
            "a new team member, or when the git history has become messy."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "git",
            "branching",
            "gitflow",
            "conventional-commits",
            "rebase",
            "merge",
            "history",
            "squash",
            "tag",
        ],
        body="""\
# Git Workflow

Good git history is documentation. Bad history is noise.

## When to use
- Starting a new project or team
- Onboarding a new contributor
- Cleaning up a messy git history

## Branch naming

```
main           ← production (protected)
develop        ← integration (protected, gitflow)
feature/xxx    ← new functionality
fix/xxx        ← bug fixes
refactor/xxx   ← code quality (no behaviour change)
release/x.y.z  ← release prep
hotfix/xxx     ← urgent production fixes
```

## Conventional commits

Format: `<type>(<scope>): <description>`

| Type | When |
|------|------|
| `feat` | New user-visible feature |
| `fix` | Bug fix |
| `refactor` | Code change, no behaviour change |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | Build scripts, CI, dependencies |
| `perf` | Performance improvement |
| `ci` | CI configuration changes |

```bash
git commit -m "feat(auth): add OAuth2 login with Google

Adds Google OAuth2 as a login option.
Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars.

Closes #42"
```

## Daily workflow (feature branch)

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
# ... make changes ...
git add -p               # stage interactively (not `git add .`)
git commit -m "feat: ..."
git push origin feature/my-feature
# → open PR against develop
```

## Rebase vs merge

**Use rebase to:**
- Keep feature branch up to date with main: `git rebase develop`
- Clean up local commits before pushing: `git rebase -i HEAD~3`

**Use merge to:**
- Integrate feature branches into main/develop (preserves PR history)

Never rebase pushed commits that others may have pulled.

## Commit hygiene before a PR

```bash
# Squash WIP commits into logical units
git rebase -i HEAD~5

# Amend the last commit message
git commit --amend

# Verify the diff makes sense
git diff origin/develop...HEAD
```

## Tagging releases

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## Verification checklist
- [ ] Branch name follows naming convention
- [ ] Each commit is atomic (one logical change)
- [ ] Commit messages follow conventional commits format
- [ ] WIP commits squashed before PR
- [ ] No binary files or secrets committed
- [ ] Merge conflict resolved correctly (not just "accept all theirs")
""",
    ),
    SkillEntry(
        slug="pr-workflow",
        name="PR Workflow — creating, reviewing, and merging pull requests",
        description=(
            "End-to-end pull request workflow: writing a good description, requesting review, "
            "addressing feedback, and merging. Use when opening a new PR, responding to review "
            "comments, or establishing PR standards for a team."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=["pull-request", "pr", "code-review", "merge", "github", "gitlab", "ci"],
        body="""\
# PR Workflow

A pull request is a unit of review and a piece of project history.
Write them well.

## When to use
- Opening a new pull request
- Responding to review comments
- Establishing PR standards for a team

## Writing a good PR description

```markdown
## What
Brief description of what changed.

## Why
Why is this change necessary? Link to the issue/ticket.

## How
Non-obvious implementation choices or trade-offs.

## Testing
How was this tested? Screenshots for UI changes.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No debug code left in
```

## PR size guidelines
| Lines changed | Action |
|--------------|--------|
| < 400 | Normal PR |
| 400-800 | Add extra context in description |
| > 800 | Split into smaller PRs |

Large PRs get poor reviews. Smaller PRs get merged faster.

## Before requesting review
1. Run CI locally: tests, lint, type check
2. Self-review the diff in the PR interface (not your editor)
3. Remove all debug logging and `TODO: temporary` code
4. Resolve all your own questions/comments

## Responding to review comments

```
Reviewer: "This function is doing too much, could we split it?"

Good response: "Good call. I've extracted the validation logic to
validate_order() in the new commit. Does that address your concern?"

Bad response: "Done." (with no explanation)
```

- Respond to every comment (even if just "Done" after actually fixing it)
- Don't resolve threads unless the reviewer agrees the issue is addressed
- If you disagree, explain why — don't just close the comment

## Merge strategies
| Strategy | When |
|----------|------|
| Squash merge | Most feature PRs (clean main history) |
| Merge commit | Release/hotfix (preserve PR boundary) |
| Rebase merge | When clean linear history is essential |

## After merging
```bash
# Clean up local branches
git branch -d feature/my-feature
git remote prune origin
```

## Verification checklist
- [ ] PR description includes what, why, and testing details
- [ ] PR is < 400 lines (or split and justified)
- [ ] CI passing before requesting review
- [ ] All review comments addressed or explained
- [ ] Branch deleted after merge
""",
    ),
    # ── Brief lang ────────────────────────────────────────────────────────────
    SkillEntry(
        slug="brief-lang",
        name="Brief lang — declarative contract-enforced logic language",
        description=(
            "End-to-end workflow for projects using Brief (v0.14.0): file variants, "
            "compiler commands, contract syntax (txn/rct/let/[pre][post]), "
            "build targets (Rust/C/LLVM/WASM/VHDL/COBOL), and governance rules."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "brief",
            "brief-lang",
            "declarative",
            "contracts",
            "transactions",
            "state-machine",
            "llvm",
            "wasm",
            "fpga",
            "cobol",
            "formal-verification",
            "rust",
        ],
        project_types=["brief-lang"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["brief-compiler", "cargo"],
        body="""\
# Brief lang

**Version anchor: v0.14.0 — commit `6a43c4aebcc5c6c774dbc2908445fb19486e8043` (2026-06-14)**
No release tags exist yet. Both the declared version and the commit hash are kept for
reproducibility. Update this file when Brief ships a tagged release.

Source: https://github.com/Randozart/brief-lang

## What is Brief?

Brief is a declarative, contract-enforced logic language for verifiable state machines.
Programs are a set of *transactions* whose preconditions and postconditions the compiler
proves. Execution is inferred: a reactor loop fires transactions automatically when their
preconditions are met. Brief transpiles to many imperative backends — Rust, C, LLVM IR,
COBOL, SystemVerilog, VHDL, and browser WASM.

## File variants

| Extension | Variant | Targets |
|-----------|---------|--------|
| `.bv` | Brief (normal) | LLVM → binary, COBOL |
| `.sbv` | Strict Brief | Same — hard errors on incomplete contracts |
| `.rbv` | Rendered Brief | Browser: WASM + JS + HTML + CSS + SVG |
| `.ebv` | Embedded Brief | FPGA (VHDL/SystemVerilog), ARM bare-metal |
| `.dbv` | Data Brief | Configuration data (all targets) |
| `.dbvs` | Data Brief Schema | FFI bindings / target specs |
| `.dbvl` | Data Brief Lines | Line-based databases |

Prefer `.sbv` for production code — the proof engine enforces complete contracts.

## Build the compiler (required — no pre-built binaries at v0.14.0)

```bash
git clone https://github.com/Randozart/brief-lang.git
cd brief-lang
git checkout 6a43c4aebcc5c6c774dbc2908445fb19486e8043   # pin to v0.14.0
cargo build --release
# Compiler is now at ./target/release/brief-compiler
export PATH="$PWD/target/release:$PATH"
```

## Compiler commands (v0.14.0)

```bash
# Type-check only (fast — use in CI lint step)
brief-compiler check counter.bv

# Strict mode — proof engine, hard errors (use in CI typecheck step)
brief-compiler check --strict counter.sbv
brief-compiler check --strict counter.bv   # force strict on .bv file

# Compile to backend
brief-compiler rust  counter.bv            # → Rust source
brief-compiler c     counter.bv            # → C source
brief-compiler llvm  counter.bv            # → LLVM IR (.ll)
brief-compiler compile counter.bv --target aarch64.dbvs   # → AArch64 asm
brief-compiler compile counter.bv --target x86_64.dbvs    # → x86-64 asm

# Hardware targets
brief-compiler compile counter.ebv --target vhdl.dbvs       # → VHDL
brief-compiler compile counter.ebv --target systemverilog.dbvs  # → SV

# Web target
brief-compiler compile app.rbv --target wasm.dbvs           # → WASM + JS glue

# FFI bindings from a C header
brief-compiler bind mylib.h                # generates mylib.dbvs

# Metropolitan shared-memory service
brief-compiler metrod connect WeatherApi   # bind to a running service

# LSP server (for editor integration)
brief-compiler lsp

# Run compiler-internal tests (requires Cargo.toml)
cargo test --lib
```

## Language syntax

### Variables
```brief
let counter: Int = 0;
let name: String = "Alice";
```

### Transactions — the core unit
```brief
txn increment() [counter < 100][counter == @counter + 1] {
    &counter = counter + 1;   // &var = mutation
    term;                      // required terminator
};

// @counter = "counter before this transaction"
// [pre][post] = precondition and postcondition contracts
```

### Reactive transactions — fire automatically
```brief
rct txn auto_save() [dirty && !saving][!dirty] {
    save_to_disk();
    &dirty = false;
    term;
};
// Fires whenever dirty==true and saving==false — no polling, no event handlers
```

### Guards (replaces if/else)
```brief
[x > 0] { &result = x * 2; };
[x < 0] { &result = x * -1; };
[x == 0] { escape; };   // escape = rollback this transaction
```

### Entry point
```brief
txn main() [true][true] {
    increment();
    increment();
    term;
};
```

### Contract patterns
```brief
// Withdraw with full pre+post contract
txn withdraw(amount: Int)
    [amount > 0 && balance >= amount]   // precondition
    [balance == @balance - amount]       // postcondition
{
    &balance = balance - amount;
    term;
};

// Partial contract — compiles with warnings (.bv)
txn log_event(msg: String) [true][] {
    write_log(msg);
    term;
};
```

### FFI (Metropolitan interface)
```brief
// Declare an external function via .dbvs binding
use std::io::PrintLine;   // from std/bindings/io.dbvs

txn greet(name: String) [true][true] {
    PrintLine(name);
    term;
};
```

## Project layout (specsmith scaffold)

```
src/        — .bv / .sbv primary source files
lib/        — .bv library modules (imported by src/)
tests/      — contract test .bv files
target/     — build output (gitignored)
```

## CI workflow (GitHub Actions)

```yaml
steps:
  - uses: dtolnay/rust-toolchain@stable
  - name: Build brief-compiler (v0.14.0 @ 6a43c4ae)
    run: |
      git clone https://github.com/Randozart/brief-lang.git brief-lang
      cd brief-lang && git checkout 6a43c4aebcc5c6c774dbc2908445fb19486e8043
      cargo build --release
      echo "$PWD/brief-lang/target/release" >> $GITHUB_PATH

  - name: Lint (brief-compiler check)
    run: brief-compiler check src/

  - name: Typecheck (strict mode)
    run: brief-compiler check --strict src/

  - name: Build to Rust
    run: brief-compiler rust src/main.bv
```

## Governance rules for Brief projects

- Every transaction MUST declare at least a precondition or postcondition — H13.
- `.sbv` (strict mode) is required for all production code paths.
- Compiler output (`target/`) is a **derived artifact** — never hand-edit generated Rust/C.
- FFI boundaries declared via `.dbvs` files are governance artifacts: treat them like API specs.
- `escape;` (rollback) must be documented with a comment explaining the failure condition.
- Contract completeness = proof coverage: treat incomplete contracts as audit warnings.

## Common pitfalls

- `term;` is required at the end of every transaction body — missing it is a parse error.
- `@var` refers to the variable value *before* the transaction; `var` after reassignment is the new value.
- `.bv` files compile with warnings for incomplete contracts; `.sbv` makes them errors.
- The Metropolitan FFI is the only way to interact with foreign code — no inline foreign calls.
- The reactor loop infers execution order; don't assume sequential call order between transactions.
- `brief-compiler lsp` provides editor integration — configure it in your IDE before writing Brief.
""",
    ),
    SkillEntry(
        slug="architecture-decision-records",
        name="Architecture Decision Records — documenting and tracking architectural decisions",
        description=(
            "Create and maintain ADRs to document significant architectural choices, their "
            "context, and rationale. Use when making a significant technology choice, "
            "changing an architectural pattern, or explaining a non-obvious design decision."
        ),
        domain=SkillDomain.SOFTWARE_ENGINEERING,
        tags=[
            "adr",
            "architecture",
            "decision",
            "documentation",
            "madr",
            "rfcs",
            "technical-decision",
        ],
        body="""\
# Architecture Decision Records

ADRs create a searchable record of *why* the system is built the way it is.
Without them, institutional knowledge lives only in people's heads.

## When to use
- Making a significant technology or framework choice
- Changing an architectural pattern
- Documenting a non-obvious trade-off decision
- When someone asks "why did we choose X over Y?"

## ADR format (MADR — Markdown Architectural Decision Records)

```markdown
# ADR-0042: Use PostgreSQL instead of MongoDB for user data

## Status
Accepted

## Context
We need a database for user accounts, preferences, and usage data.
The data has clear relational structure (users → subscriptions → invoices).
Team has stronger SQL expertise than MongoDB.

## Decision
Use PostgreSQL 16.

## Consequences
### Positive
- Strong consistency guarantees
- SQL joins simplify complex queries
- Mature tooling (pgAdmin, psycopg2, SQLAlchemy)

### Negative
- Horizontal write scaling requires Citus (extra complexity)
- Schema migrations require downtime planning

## Alternatives considered
### MongoDB
- Pro: schema flexibility for future unknown fields
- Con: no native joins; team inexperience; ACID only per-document in 4.0+
- Decision: not chosen because relational model fits our data better

### DynamoDB
- Pro: infinite scale, AWS managed
- Con: high cost at our scale; steep learning curve; poor ad-hoc queries
- Decision: not chosen at current scale
```

## ADR storage location
```
docs/decisions/
  0001-use-postgresql.md
  0002-adopt-gitflow.md
  0042-message-queue-rabbitmq.md
```

## Numbering
Use `adr-tools` or manual sequential numbering. Never reuse numbers.

## Lifecycle states
- **Proposed**: under discussion
- **Accepted**: approved and implemented
- **Deprecated**: still in use but not the preferred approach
- **Superseded**: replaced by a later ADR (link to replacement)

## When NOT to write an ADR
- Reversible implementation details (which library within a framework)
- Cosmetic/style choices (tabs vs spaces — this goes in `.editorconfig`)
- Decisions that will obviously change (use ADR when the choice is load-bearing)

## Verification checklist
- [ ] ADR has a number, title, and status
- [ ] Context explains the problem (not just the solution)
- [ ] Alternatives considered with explicit rejection reasoning
- [ ] Consequences section covers both positive and negative
- [ ] ADR committed alongside the implementation PR
""",
    ),
]
