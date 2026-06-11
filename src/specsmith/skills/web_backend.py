# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Web / backend skill domain — frontend engineering, web perf, accessibility, databases."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="frontend-ui-engineering",
        name="Frontend UI Engineering — component architecture and state management",
        description=(
            "Patterns for building maintainable frontend UIs: component design, state "
            "management, rendering optimisation, and testing. Use when designing a new "
            "component system, refactoring a complex UI, or investigating rendering performance."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "frontend",
            "react",
            "vue",
            "components",
            "state",
            "zustand",
            "redux",
            "rendering",
            "storybook",
        ],
        body="""\
# Frontend UI Engineering

Well-designed UIs are composed of small, testable, reusable components.
State lives as close to where it is used as possible.

## When to use
- Designing a new component library or design system
- Refactoring a complex, entangled UI
- Investigating rendering performance issues

## Component design principles

### 1. Single responsibility
Each component does one thing:
```tsx
// Bad: one component for everything
<UserCard user={user} onEdit={edit} onDelete={del} showStats={true} />

// Good: composed from smaller pieces
<UserCard user={user}>
  <UserStats />
  <UserActions onEdit={edit} onDelete={del} />
</UserCard>
```

### 2. Co-locate state with consumers
```tsx
// Bad: lifting state too high
function App() {
  const [searchQuery, setSearchQuery] = useState("");
  return <SearchBar query={searchQuery} onChange={setSearchQuery} />;
}

// Good: keep state in the smallest component that needs it
function SearchBar() {
  const [query, setQuery] = useState("");
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

### 3. Derive don't duplicate
```tsx
// Bad: keeping derived state in state
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]);

// Good: derive on render
const [items, setItems] = useState([]);
const filteredItems = items.filter(item => item.active);
```

## State management decision
| State type | Where |
|-----------|-------|
| UI state (open/closed, active tab) | Local `useState` |
| Form state | `useForm` (react-hook-form) |
| Server state | TanStack Query / SWR |
| Shared app state | Zustand / Jotai |
| Global complex state | Redux Toolkit (large teams only) |

## Performance optimisation
```tsx
// Prevent unnecessary re-renders
const ExpensiveList = memo(({ items }: { items: Item[] }) => (
  <ul>{items.map(item => <ListItem key={item.id} {...item} />)}</ul>
));

// Lazy load heavy components
const Chart = lazy(() => import("./Chart"));
```

## Testing components
```tsx
// Test behaviour, not implementation
it("shows error when form is submitted empty", async () => {
  render(<LoginForm />);
  await userEvent.click(screen.getByRole("button", { name: /submit/i }));
  expect(screen.getByText(/email is required/i)).toBeInTheDocument();
});
```

## Verification checklist
- [ ] Components have a single responsibility
- [ ] No prop drilling deeper than 3 levels (use context or state manager)
- [ ] Server state managed with TanStack Query or SWR
- [ ] Expensive components wrapped in `memo`
- [ ] Storybook stories for all shared UI components
- [ ] Component tests cover user interactions, not implementation
""",
    ),
    SkillEntry(
        slug="web-performance",
        name="Web Performance — Core Web Vitals and bundle optimisation",
        description=(
            "Improve page load speed, Core Web Vitals, and bundle size. Use when LCP > 2.5s, "
            "CLS > 0.1, INP > 200ms, bundle size has grown significantly, or when preparing "
            "for a production launch."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "performance",
            "core-web-vitals",
            "lcp",
            "cls",
            "inp",
            "bundle",
            "lighthouse",
            "lazy-loading",
            "caching",
            "cdn",
        ],
        body="""\
# Web Performance

Every 100ms of latency costs ~1% conversion. Performance is a feature.

## When to use
- LCP > 2.5s, CLS > 0.1, or INP > 200ms
- Bundle size has grown without explanation
- Preparing for a production launch
- After adding a large new dependency

## Step 1: Measure with real tools

```bash
# Lighthouse (automated)
npx lighthouse https://yoursite.com --output json

# WebPageTest (real devices, global CDN nodes)
# → webpagetest.org

# Chrome DevTools
# → Network tab: disable cache, throttle to "Slow 4G"
# → Performance tab: record page load
```

## Step 2: Fix LCP (Largest Contentful Paint — target < 2.5s)

LCP is almost always an image or hero text.

```html
<!-- Preload the LCP image -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">

<!-- Use responsive images -->
<img src="hero.webp" srcset="hero-480.webp 480w, hero-960.webp 960w"
     sizes="(max-width: 600px) 480px, 960px" loading="eager">
```

## Step 3: Fix CLS (Cumulative Layout Shift — target < 0.1)

CLS is caused by content jumping when images/fonts/ads load.

```css
/* Reserve space for images */
img { aspect-ratio: 16 / 9; width: 100%; }

/* Avoid font-display: auto */
@font-face {
  font-display: optional; /* prevents invisible text flash */
}
```

## Step 4: Reduce bundle size

```bash
# Analyse bundle
npx vite-bundle-visualizer  # Vite
npx webpack-bundle-analyzer  # Webpack
npx @next/bundle-analyzer    # Next.js
```

Common fixes:
```tsx
// Lazy-load heavy routes
const AdminPanel = lazy(() => import("./AdminPanel"));

// Tree-shake lodash
import debounce from "lodash/debounce";  // not import _ from "lodash"

// Replace moment.js with date-fns (saves ~67KB gzip)
import { format } from "date-fns";
```

## Step 5: Optimise images

```bash
# Convert to WebP/AVIF
npx sharp-cli --input "*.png" --output "dist/" --format webp

# Next.js: use <Image> component (automatic optimisation)
import Image from "next/image";
```

## Caching and CDN

```nginx
# Cache static assets 1 year
location ~* \\.(js|css|webp|woff2)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}
# HTML: revalidate
location ~* \\.html$ {
    add_header Cache-Control "public, max-age=0, must-revalidate";
}
```

## Verification checklist
- [ ] Lighthouse score ≥ 90 on mobile
- [ ] LCP < 2.5s on Slow 4G
- [ ] CLS < 0.1
- [ ] INP < 200ms
- [ ] Bundle < 200KB gzip for initial load
- [ ] All images served as WebP/AVIF with explicit dimensions
""",
    ),
    SkillEntry(
        slug="accessibility",
        name="Accessibility — WCAG 2.1 AA implementation for web applications",
        description=(
            "WCAG 2.1 AA compliance checklist and implementation guide. Use when building "
            "new UI components, preparing for an accessibility audit, or after receiving "
            "accessibility bug reports."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "accessibility",
            "a11y",
            "wcag",
            "aria",
            "keyboard",
            "screen-reader",
            "colour-contrast",
            "axe",
            "focus",
        ],
        body="""\
# Accessibility (a11y)

Accessibility is not optional for public-facing products.
WCAG 2.1 AA is the legal minimum in most jurisdictions.

## When to use
- Building new UI components (always, from the start)
- Preparing for an accessibility audit
- After receiving accessibility bug reports

## The four WCAG principles (POUR)
1. **Perceivable** — information can be seen or heard
2. **Operable** — all functionality works with keyboard
3. **Understandable** — content is readable and predictable
4. **Robust** — works with assistive technologies

## Checklist by category

### Keyboard navigation
```tsx
// All interactive elements must be keyboard-focusable
// Never use <div onClick> for buttons — use <button>
<button onClick={handleAction}>Submit</button>  // ✓
<div onClick={handleAction}>Submit</div>        // ✗ not keyboard-accessible

// Custom components need tabIndex and keyboard handlers
<div
  role="button"
  tabIndex={0}
  onClick={handleAction}
  onKeyDown={e => e.key === "Enter" && handleAction()}
>
  Submit
</div>
```

### Semantic HTML
```html
<!-- Use the right element for the job -->
<nav>...</nav>         <!-- navigation landmark -->
<main>...</main>       <!-- main content -->
<h1>Page Title</h1>   <!-- heading hierarchy (h1 → h2 → h3) -->
<button>Submit</button>  <!-- not <a> or <div> -->
<label for="email">Email</label><input id="email" />
```

### ARIA — only when HTML is not enough
```tsx
// Modal dialog
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Confirm Delete</h2>
</div>

// Loading state
<div aria-live="polite" aria-label="Loading...">
  {isLoading && <Spinner />}
</div>

// Icon buttons need labels
<button aria-label="Close dialog">
  <CloseIcon aria-hidden="true" />
</button>
```

### Colour contrast
- Normal text: minimum 4.5:1 ratio
- Large text (18pt+): minimum 3:1 ratio

```bash
# Check contrast programmatically
npx axe-cli https://yoursite.com
```

### Focus management
```tsx
// Trap focus in modals
import { FocusTrap } from "@radix-ui/react-focus-trap";

// Return focus when modal closes
const triggerRef = useRef(null);
useEffect(() => {
  if (!isOpen) triggerRef.current?.focus();
}, [isOpen]);
```

## Testing tools

```bash
# Automated: axe-core (catches ~30-40% of issues)
npm install --save-dev axe-core @axe-core/react

# Manual: screen reader testing
# macOS: Cmd+F5 (VoiceOver)
# Windows: Windows+Enter (Narrator)
# NVDA: free, Windows (recommended)
```

## Verification checklist
- [ ] Keyboard navigation tested on all interactive flows
- [ ] All images have alt text (empty alt="" for decorative images)
- [ ] Heading hierarchy is correct (h1→h2→h3, no skipping)
- [ ] Colour contrast ≥ 4.5:1 for all text
- [ ] Form inputs have associated labels
- [ ] Modal focus trap and focus return implemented
- [ ] `axe-core` automated tests run in CI
- [ ] Screen reader test completed (VoiceOver or NVDA)
""",
    ),
    SkillEntry(
        slug="testing-e2e",
        name="End-to-End Testing — Playwright workflow for web apps",
        description=(
            "Playwright-based end-to-end test workflow: test structure, page objects, "
            "CI integration, and visual regression. Use when setting up E2E tests for a "
            "web app, debugging flaky tests, or adding tests for a critical user journey."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "e2e",
            "playwright",
            "cypress",
            "testing",
            "browser-testing",
            "visual-regression",
            "flaky-tests",
            "page-object",
        ],
        body="""\
# End-to-End Testing

E2E tests are the safety net for critical user journeys.
Write them for the top 5 flows that, if broken, would cause immediate user impact.

## When to use
- Setting up E2E tests for a web app
- Adding coverage for a new critical user journey (login, checkout, signup)
- Investigating flaky E2E tests

## Test structure — what to test

| Priority | Examples |
|----------|---------|
| 🔴 Critical | Login, signup, checkout, payment, data loss |
| 🟡 High | Main CRUD operations, search, filters |
| 🟢 Normal | Edge cases, error messages, accessibility flows |

Do NOT write E2E tests for every UI state — use component tests instead.

## Playwright setup

```bash
npm init playwright@latest
```

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
  },
});
```

## Page Object Model (for maintainability)

```typescript
// e2e/pages/LoginPage.ts
export class LoginPage {
  constructor(private readonly page: Page) {}

  async login(email: string, password: string) {
    await this.page.goto("/login");
    await this.page.getByLabel("Email").fill(email);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: /sign in/i }).click();
    await this.page.waitForURL("/dashboard");
  }
}

// e2e/auth.spec.ts
test("user can log in", async ({ page }) => {
  const login = new LoginPage(page);
  await login.login("user@test.com", "password");
  await expect(page.getByText("Welcome back")).toBeVisible();
});
```

## Selectors — use accessible locators

```typescript
// Best: user-facing attributes
await page.getByRole("button", { name: "Submit" });
await page.getByLabel("Email address");
await page.getByText("Confirm your order");

// Acceptable: test IDs for dynamic content
await page.getByTestId("checkout-total");

// Avoid: CSS selectors that break on refactor
await page.locator(".btn-primary.submit");  // fragile
```

## Fixing flaky tests

Flakiness is almost always a timing issue:
```typescript
// Bad: fixed wait
await page.waitForTimeout(2000);

// Good: wait for condition
await expect(page.getByRole("status")).toContainText("Saved");
await page.waitForURL("/dashboard");
await page.waitForLoadState("networkidle");
```

## CI integration

```yaml
# .github/workflows/e2e.yml
- uses: microsoft/playwright-github-action@v1
- run: npx playwright install --with-deps
- run: npx playwright test
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```

## Verification checklist
- [ ] Tests cover the top-5 critical user journeys
- [ ] Page Object Model used for multi-step flows
- [ ] Only accessible locators used (role, label, text)
- [ ] No `waitForTimeout` — use condition-based waits
- [ ] Tests run in CI with artifact upload on failure
- [ ] Flaky tests resolved before merging
""",
    ),
    SkillEntry(
        slug="nextjs-development",
        name="Next.js Development — App Router, Server Components, and data fetching",
        description=(
            "Production patterns for Next.js 15: App Router structure, Server vs Client "
            "Components, Server Actions, data fetching, and caching. Use when building a "
            "new Next.js feature, migrating from Pages Router, or debugging hydration errors."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "nextjs",
            "react",
            "app-router",
            "server-components",
            "server-actions",
            "rsc",
            "hydration",
            "caching",
            "typescript",
        ],
        project_types=["nextjs-app"],
        body="""\
# Next.js Development

The App Router moved rendering decisions into the component tree.
The default is Server Components — opt into Client Components explicitly.

## When to use
- Building a new Next.js App Router feature
- Migrating from Pages Router
- Debugging hydration errors or unexpected client-side behaviour

## Server vs Client Components

```tsx
// Default: Server Component (no "use client")
// ✓ Access databases, files, secrets
// ✓ Faster, zero JS sent to client
// ✗ No useState, useEffect, event handlers
async function ProductList() {
  const products = await db.query("SELECT * FROM products");  // ✓ direct DB
  return <ul>{products.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}

// Client Component — add "use client" at top of file
// ✓ Interactivity, useState, event handlers
// ✗ No direct DB/file access
"use client";
function AddToCartButton({ productId }: { productId: string }) {
  const [added, setAdded] = useState(false);
  return <button onClick={() => setAdded(true)}>Add to Cart</button>;
}
```

**Rule**: push `"use client"` as far down the tree as possible.

## App Router file structure

```
app/
  layout.tsx           ← root layout (persistent)
  page.tsx             ← home page /
  (marketing)/         ← route group (no URL segment)
    about/page.tsx     ← /about
  dashboard/
    layout.tsx         ← nested layout for /dashboard/*
    page.tsx           ← /dashboard
    loading.tsx        ← Suspense boundary
    error.tsx          ← error boundary
  api/
    products/route.ts  ← API route (GET, POST handlers)
```

## Data fetching

```tsx
// Server Component: async/await directly
async function Page({ params }: { params: { id: string } }) {
  const data = await fetch(`https://api.example.com/items/${params.id}`, {
    next: { revalidate: 60 },  // ISR: revalidate every 60 seconds
  });
  return <ItemDetail item={await data.json()} />;
}

// Cache options
fetch(url);                          // cached forever (static)
fetch(url, { cache: "no-store" });   // always fresh (dynamic)
fetch(url, { next: { revalidate: 60 } });  // ISR
```

## Server Actions

```tsx
"use server";

export async function createOrder(formData: FormData) {
  const email = formData.get("email") as string;
  // Validate + save to DB
  await db.orders.create({ email });
  revalidatePath("/orders");
  redirect("/orders");
}

// In a form:
<form action={createOrder}>
  <input name="email" type="email" required />
  <button type="submit">Order</button>
</form>
```

## Common pitfalls
| Problem | Cause | Fix |
|---------|-------|-----|
| Hydration mismatch | Different server/client render | Check for `window`, `Date.now()`, random values in RSC |
| Infinite re-renders | Object/array in deps array | `useMemo` or move outside component |
| Stale data after mutation | Forgot to `revalidatePath` | Add `revalidatePath("/affected-route")` after mutation |

## Verification checklist
- [ ] `"use client"` only where interactivity is needed
- [ ] No secrets or DB access in Client Components
- [ ] Loading and error boundaries defined for all routes
- [ ] `revalidatePath` called after all Server Actions that mutate data
- [ ] TypeScript strict mode enabled
""",
    ),
    SkillEntry(
        slug="database-postgresql",
        name="PostgreSQL — production setup, queries, and maintenance",
        description=(
            "PostgreSQL production guide: connection pooling, query optimisation, "
            "vacuuming, replication, and backup. Use when setting up PostgreSQL for "
            "production, diagnosing slow queries, or planning a maintenance window."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "postgresql",
            "postgres",
            "sql",
            "pgbouncer",
            "vacuum",
            "replication",
            "backup",
            "pgvector",
            "jsonb",
        ],
        body="""\
# PostgreSQL Production

PostgreSQL is a battleship. Use it well.

## When to use
- Setting up PostgreSQL for a production application
- Diagnosing slow queries or lock contention
- Planning a maintenance window or migration

## Connection pooling (PgBouncer)

Direct connections from 100+ app servers overwhelm PostgreSQL.
Always use PgBouncer in transaction mode:

```ini
# pgbouncer.ini
[databases]
myapp = host=postgres port=5432 dbname=myapp

[pgbouncer]
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

Application connects to `:6432`, PgBouncer multiplexes to PostgreSQL.

## Essential configuration

```sql
-- postgresql.conf (key settings)
shared_buffers = 25% of RAM         -- cache
effective_cache_size = 75% of RAM   -- planner hint
work_mem = 16MB                     -- per-sort, per-hash
max_connections = 100               -- keep low; use pgbouncer
log_min_duration_statement = 500    -- log queries > 500ms
```

## Query patterns

### JSONB for semi-structured data
```sql
ALTER TABLE events ADD COLUMN metadata JSONB;
CREATE INDEX idx_events_metadata ON events USING GIN(metadata);

-- Query JSON field
SELECT * FROM events WHERE metadata->>'event_type' = 'purchase';
SELECT * FROM events WHERE metadata @> '{"user_id": 123}';
```

### Efficient bulk inserts
```python
# Use COPY or executemany with psycopg
with conn.cursor() as cur:
    psycopg.copy(
        "COPY items (name, price) FROM STDIN",
        [(row["name"], row["price"]) for row in data]
    )
```

### Window functions instead of subqueries
```sql
-- Running total per customer
SELECT customer_id, amount,
  SUM(amount) OVER (PARTITION BY customer_id ORDER BY created_at) AS running_total
FROM orders;
```

## Maintenance

```sql
-- Table bloat from dead rows — run after heavy updates/deletes
VACUUM ANALYZE orders;

-- Aggressive reclaim space (requires table lock — use carefully)
VACUUM FULL orders;

-- Check table and index bloat
SELECT relname, n_dead_tup, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;
```

## Backup

```bash
# Logical backup (restore to any version)
pg_dump -Fc myapp > myapp_$(date +%F).dump
pg_restore -d myapp_restore myapp_$(date +%F).dump

# Continuous archiving with pgBackRest (production)
pgbackrest --stanza=main backup
```

## Monitoring queries to watch

```sql
-- Active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Longest running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' ORDER BY duration DESC LIMIT 10;

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;
```

## Verification checklist
- [ ] PgBouncer in transaction mode (pool_size ≤ max_connections / 4)
- [ ] `log_min_duration_statement = 500` enabled
- [ ] Automated daily backup with retention policy
- [ ] Autovacuum settings reviewed for high-churn tables
- [ ] Read replica in place for heavy reporting queries
- [ ] Failover tested (promote replica + update connection string)
""",
    ),
    SkillEntry(
        slug="caching-redis",
        name="Caching with Redis — patterns, pitfalls, and eviction strategies",
        description=(
            "Redis caching patterns: cache-aside, write-through, TTL strategy, cache "
            "stampede prevention, and eviction. Use when adding caching to reduce DB load, "
            "improve latency, or store session/rate-limit state."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "redis",
            "caching",
            "cache-aside",
            "ttl",
            "session",
            "rate-limiting",
            "pub-sub",
            "lua",
            "eviction",
        ],
        body="""\
# Caching with Redis

Cache only what you have proven is slow. Measure before caching.

## When to use
- Database queries taking > 100ms that are called frequently
- Session storage for stateless API servers
- Rate limiting and distributed counters
- Real-time pub/sub between services

## Connection setup (Python)

```python
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379",
    max_connections=20,
    decode_responses=True,
)
client = redis.Redis(connection_pool=pool)
```

## Cache-aside pattern (most common)

```python
async def get_product(product_id: str) -> dict:
    cache_key = f"product:{product_id}"

    # 1. Check cache
    cached = await client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Cache miss: fetch from DB
    product = await db.get_product(product_id)

    # 3. Populate cache with TTL
    await client.setex(cache_key, 3600, json.dumps(product))
    return product
```

## Cache invalidation

```python
# Invalidate on write
async def update_product(product_id: str, data: dict):
    await db.update_product(product_id, data)
    await client.delete(f"product:{product_id}")  # ← invalidate

# Invalidate by pattern (careful — expensive on large Redis instances)
keys = await client.keys("product:*")
if keys:
    await client.delete(*keys)
```

## Preventing cache stampede

```python
from redis.lock import Lock

async def get_with_lock(key: str, ttl: int, fetch_fn):
    cached = await client.get(key)
    if cached:
        return json.loads(cached)

    async with Lock(client, f"lock:{key}", timeout=5):
        # Re-check after acquiring lock
        cached = await client.get(key)
        if cached:
            return json.loads(cached)

        value = await fetch_fn()
        await client.setex(key, ttl, json.dumps(value))
        return value
```

## Rate limiting

```lua
-- Atomic rate limit check (Lua script — runs atomically)
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then redis.call('EXPIRE', key, window) end
if current > limit then return 0 end
return 1
```

## TTL strategy

| Data type | TTL |
|----------|-----|
| User sessions | 24 hours |
| API responses | 5-60 minutes |
| Rate limit counters | 1 minute |
| Computed aggregates | 1 hour |
| Immutable (product IDs) | 24 hours |

## Eviction policy (set in redis.conf)

```
# For caches: evict least-recently-used items when full
maxmemory-policy allkeys-lru

# For session storage: only evict keys with TTL set
maxmemory-policy volatile-lru
```

## Verification checklist
- [ ] TTL set on every cache key (no eternal keys)
- [ ] Cache stampede prevention for high-traffic keys
- [ ] Cache invalidation on all write paths
- [ ] `maxmemory` and eviction policy configured
- [ ] Redis persistence configured for session data (if needed)
- [ ] Cache hit ratio monitored: `redis-cli info stats | grep keyspace`
""",
    ),
    SkillEntry(
        slug="rest-api-development",
        name="REST API Development — building production-grade REST APIs",
        description=(
            "Build production REST APIs with FastAPI or Express: authentication, "
            "validation, error handling, rate limiting, and OpenAPI docs. Use when "
            "implementing a new API or adding endpoints to an existing service."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "rest",
            "fastapi",
            "express",
            "api",
            "authentication",
            "jwt",
            "rate-limiting",
            "openapi",
            "validation",
        ],
        body="""\
# REST API Development

A production API handles bad inputs gracefully, fails fast on bad requests,
and never exposes internal details in error responses.

## When to use
- Implementing a new REST API service
- Adding endpoints to an existing API
- Reviewing an API for production readiness

## FastAPI skeleton

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

app = FastAPI(title="My API", version="1.0.0")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")

class CreateOrderRequest(BaseModel):
    customer_email: EmailStr
    items: list[str]
    total_cents: int

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    body: CreateOrderRequest,
    token: str = Depends(oauth2),
    db: AsyncSession = Depends(get_db),
):
    user = verify_token(token)  # raises 401 if invalid
    order = await order_service.create(db, user.id, body)
    return order
```

## Authentication

```python
from jose import jwt, JWTError

def verify_token(token: str) -> UserPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return UserPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## Consistent error responses

```python
from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail.upper().replace(" ", "_"),
                "message": exc.detail,
                "request_id": request.state.request_id,
            }
        },
    )
```

## Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/orders")
@limiter.limit("10/minute")
async def create_order(request: Request, ...):
    ...
```

## OpenAPI documentation

FastAPI generates OpenAPI automatically. Enhance it:
```python
@app.post(
    "/orders",
    summary="Create a new order",
    response_description="The created order",
    responses={
        409: {"description": "Order already exists"},
        422: {"description": "Validation error"},
    },
)
```

## Verification checklist
- [ ] All inputs validated with Pydantic models
- [ ] Authentication required on all non-public endpoints
- [ ] Error responses use consistent structure
- [ ] Rate limiting applied to auth and mutation endpoints
- [ ] Sensitive data never in error messages or logs
- [ ] OpenAPI spec exported and validated
- [ ] Health check endpoint at `/health`
""",
    ),
    SkillEntry(
        slug="graphql-development",
        name="GraphQL Development — schema design, resolvers, and performance",
        description=(
            "Build production GraphQL APIs: schema-first design, resolver patterns, "
            "DataLoader for N+1, subscriptions, and persisted queries. Use when "
            "implementing a GraphQL API or diagnosing GraphQL N+1 and performance issues."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "graphql",
            "apollo",
            "strawberry",
            "resolver",
            "dataloader",
            "n+1",
            "subscription",
            "schema",
            "fragments",
        ],
        body="""\
# GraphQL Development

GraphQL's power is in its type system and composability.
Its danger is N+1 queries at every resolver.

## When to use
- Building APIs where clients need flexible data fetching
- Mobile apps with bandwidth constraints
- Implementing a GraphQL API from scratch
- Diagnosing N+1 or performance issues

## Schema design

```graphql
type Query {
  order(id: ID!): Order
  orders(
    status: OrderStatus
    first: Int = 20
    after: String
  ): OrderConnection!
}

type Order {
  id: ID!
  customer: Customer!       # → risk of N+1
  items: [OrderItem!]!      # → risk of N+1
  totalCents: Int!
  status: OrderStatus!
  createdAt: DateTime!
}

type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
}
```

## Python with Strawberry

```python
import strawberry
from strawberry.dataloader import DataLoader

@strawberry.type
class Query:
    @strawberry.field
    async def order(self, id: strawberry.ID, info: strawberry.Info) -> Order | None:
        return await info.context["order_loader"].load(id)
```

## DataLoader — solving the N+1 problem

```python
# Without DataLoader: 1 query per order.customer (N+1)
# With DataLoader: 1 batch query for all customers

async def load_customers(customer_ids: list[str]) -> list[Customer]:
    customers = await db.fetch_many(
        "SELECT * FROM customers WHERE id = ANY($1)", customer_ids
    )
    by_id = {c.id: c for c in customers}
    return [by_id.get(id) for id in customer_ids]

customer_loader = DataLoader(load_fn=load_customers)

@strawberry.type
class Order:
    customer_id: str

    @strawberry.field
    async def customer(self, info: strawberry.Info) -> Customer:
        return await info.context["customer_loader"].load(self.customer_id)
```

## Depth and complexity limits (protect against DoS)

```python
from strawberry.extensions import MaxQueryDepth, QueryDepthLimiter

schema = strawberry.Schema(
    query=Query,
    extensions=[
        MaxQueryDepth(max_depth=10),
    ],
)
```

## Persisted queries (production)

Persisted queries prevent malicious clients from sending arbitrary queries:
```typescript
// Apollo Client: automatic persisted queries
const client = new ApolloClient({
  link: createPersistedQueryLink({ useGETForHashedQueries: true }),
});
```

## Verification checklist
- [ ] DataLoader used for every resolver that fetches related entities
- [ ] Max query depth set (10 is a good default)
- [ ] Pagination implemented with Relay-style cursors
- [ ] Mutations return the modified type (for cache updates)
- [ ] Authentication checked in middleware, not per-resolver
- [ ] N+1 confirmed absent with query logging
""",
    ),
    SkillEntry(
        slug="message-queue",
        name="Message Queues — async task processing with Redis/RabbitMQ/Celery",
        description=(
            "Async task queue patterns: task design, error handling, retries, dead-letter "
            "queues, and monitoring. Use when offloading slow operations from request paths, "
            "implementing event-driven workflows, or processing background jobs."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "message-queue",
            "celery",
            "redis",
            "rabbitmq",
            "kafka",
            "async",
            "background-jobs",
            "retry",
            "dead-letter",
            "worker",
        ],
        body="""\
# Message Queues

Move anything that takes > 500ms out of the request path.

## When to use
- Sending emails, generating PDFs, processing images
- Event-driven workflows (order → inventory → shipping)
- Rate-limited external API calls
- Any task that can be processed asynchronously

## Celery with Redis (Python)

```python
from celery import Celery

app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,          # ack only after task completes
    worker_prefetch_multiplier=1, # one task at a time per worker
)

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(TransientError,),
)
def send_order_email(self, order_id: str) -> None:
    try:
        order = Order.get(order_id)
        email_service.send(order.customer_email, "order_confirmation", order)
    except TransientError as exc:
        raise self.retry(exc=exc)
```

## Task design rules
1. **Idempotent** — safe to retry without side effects
2. **Small scope** — one responsibility per task
3. **Accept IDs, not objects** — objects serialise poorly and go stale
4. **Set timeouts** — never let a task run forever

```python
# Pass ID, not the full object
send_order_email.delay(order.id)   # ✓
send_order_email.delay(order)      # ✗ serialises entire object
```

## Dead-letter queue

```python
app.conf.task_routes = {
    "tasks.send_order_email": {
        "queue": "email",
        "dead_letter_queue": "email.dead",
    }
}
```

Monitor dead-letter queues — they contain tasks that exhausted all retries.

## Running workers

```bash
# Development
celery -A tasks worker --loglevel=info

# Production (with autoscale)
celery -A tasks worker --autoscale=10,2 --loglevel=warning

# Scheduled tasks (cron-like)
celery -A tasks beat --loglevel=info
```

## Monitoring with Flower

```bash
pip install flower
celery -A tasks flower --port=5555
```

## Verification checklist
- [ ] All tasks are idempotent
- [ ] Task arguments are primitive types or IDs (not objects)
- [ ] `max_retries` and `default_retry_delay` set on every task
- [ ] Dead-letter queue monitored with alerts
- [ ] Task timeouts configured (`soft_time_limit`, `time_limit`)
- [ ] Worker count sized to queue depth (not to CPU count)
""",
    ),
    SkillEntry(
        slug="websocket-realtime",
        name="WebSocket & Real-Time — building real-time features with WebSockets",
        description=(
            "Implement real-time features using WebSockets: connection management, "
            "rooms/channels, reconnection, and scaling with Redis pub/sub. Use when "
            "building chat, live dashboards, collaborative editing, or notifications."
        ),
        domain=SkillDomain.WEB_BACKEND,
        tags=[
            "websocket",
            "realtime",
            "socket.io",
            "fastapi-websocket",
            "pub-sub",
            "redis",
            "sse",
            "live",
            "collaboration",
        ],
        body="""\
# WebSocket & Real-Time

Use WebSockets for true bidirectional, low-latency communication.
Use Server-Sent Events (SSE) for server-to-client streams.

## When to use
- Chat, live notifications, collaborative editing
- Live dashboards with < 1s update latency
- Game state synchronisation
- Order/delivery tracking

## FastAPI WebSocket

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # room_id → connections

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

    def disconnect(self, ws: WebSocket, room: str):
        self.active.get(room, []).remove(ws)

    async def broadcast(self, room: str, message: dict):
        for ws in self.active.get(room, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass  # client disconnected mid-send

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: str):
    await manager.connect(ws, room_id)
    try:
        while True:
            data = await ws.receive_json()
            await manager.broadcast(room_id, {"from": ws.client.host, **data})
    except WebSocketDisconnect:
        manager.disconnect(ws, room_id)
```

## Scaling across multiple servers (Redis pub/sub)

```python
import redis.asyncio as aioredis

redis = aioredis.from_url("redis://localhost")

async def subscribe_to_room(room_id: str, ws: WebSocket):
    async with redis.pubsub() as pubsub:
        await pubsub.subscribe(f"room:{room_id}")
        async for message in pubsub.listen():
            if message["type"] == "message":
                await ws.send_text(message["data"])

async def publish_to_room(room_id: str, data: dict):
    await redis.publish(f"room:{room_id}", json.dumps(data))
```

## Client reconnection (JavaScript)

```typescript
class ReconnectingWebSocket {
  private ws: WebSocket | null = null;
  private retryDelay = 1000;

  connect(url: string) {
    this.ws = new WebSocket(url);

    this.ws.onclose = () => {
      setTimeout(() => {
        this.retryDelay = Math.min(this.retryDelay * 2, 30000);  // exponential backoff
        this.connect(url);
      }, this.retryDelay);
    };

    this.ws.onopen = () => { this.retryDelay = 1000; };  // reset on success
  }
}
```

## Server-Sent Events (simpler for server-to-client only)

```python
from fastapi.responses import StreamingResponse

@app.get("/notifications/stream")
async def notifications(token: str = Depends(verify_token)):
    async def event_generator():
        async for event in notification_service.subscribe(token.user_id):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## Verification checklist
- [ ] Authentication checked on WebSocket upgrade (not just HTTP)
- [ ] Heartbeat/ping-pong implemented (detect silent disconnects)
- [ ] Redis pub/sub used for multi-server deployments
- [ ] Client reconnection with exponential backoff
- [ ] Rate limiting applied to message sends
- [ ] Max message size enforced
""",
    ),
]
