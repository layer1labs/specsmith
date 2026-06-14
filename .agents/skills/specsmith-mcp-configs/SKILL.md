# Specsmith MCP Server Config Library

A curated, tested repository of MCP server configurations for use in
`.specsmith/mcp.yml`. All entries are sourced from the official
`modelcontextprotocol/servers` GitHub repo, Anthropic, or widely-used
community servers with verified working configurations.

## How to use

Copy any server block below into your `.specsmith/mcp.yml`:

```yaml
# .specsmith/mcp.yml
servers:
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    env: {}
```

Then start the specsmith agent REPL — MCP servers are auto-connected:
```bash
specsmith run
```

To generate a starter config stub:
```bash
specsmith mcp install-warp   # Warp MCP JSON snippet
```

---

## Official MCP Servers (modelcontextprotocol/servers)

All require Node.js 18+ and are run via `npx -y`.

### Filesystem — read/write local files
```yaml
- name: filesystem
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
  env: {}
```
Allows agents to read, write, list, and search files within the specified
directory. Pass multiple directories as additional args.

### GitHub — issues, PRs, code search
```yaml
- name: github
  command: npx
  args: ["-y", "@modelcontextprotocol/server-github"]
  env:
    GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
```
Set `GITHUB_TOKEN` in your environment. Scopes needed: `repo`, `read:org`.

### Brave Search — web search
```yaml
- name: brave-search
  command: npx
  args: ["-y", "@modelcontextprotocol/server-brave-search"]
  env:
    BRAVE_API_KEY: "${BRAVE_API_KEY}"
```
Get a free API key at https://api.search.brave.com

### PostgreSQL — query a Postgres database
```yaml
- name: postgres
  command: npx
  args:
    - "-y"
    - "@modelcontextprotocol/server-postgres"
    - "postgresql://user:password@localhost:5432/dbname"
  env: {}
```
Replace the connection string with your database URL.

### SQLite — query a local SQLite database
```yaml
- name: sqlite
  command: npx
  args: ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/path/to/db.sqlite"]
  env: {}
```

### Fetch — retrieve web pages / REST APIs
```yaml
- name: fetch
  command: npx
  args: ["-y", "@modelcontextprotocol/server-fetch"]
  env: {}
```
Fetches URLs and returns content as text or markdown. Useful for reading
documentation, REST API responses, and public web pages.

### Memory — persistent in-session key-value store
```yaml
- name: memory
  command: npx
  args: ["-y", "@modelcontextprotocol/server-memory"]
  env: {}
```
Stores and retrieves facts within a session. Persisted to a local JSON file.

### Puppeteer — headless browser automation
```yaml
- name: puppeteer
  command: npx
  args: ["-y", "@modelcontextprotocol/server-puppeteer"]
  env: {}
```
Full browser control: navigate, click, screenshot, extract content.
Requires Chromium (installed automatically by puppeteer on first run).

### Sequential Thinking — structured reasoning tool
```yaml
- name: sequential-thinking
  command: npx
  args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  env: {}
```
Provides a `sequential_thinking` tool that helps agents reason step-by-step
through complex problems before acting.

### Slack — post messages and read channels
```yaml
- name: slack
  command: npx
  args: ["-y", "@modelcontextprotocol/server-slack"]
  env:
    SLACK_BOT_TOKEN: "${SLACK_BOT_TOKEN}"
    SLACK_TEAM_ID: "${SLACK_TEAM_ID}"
```
Create a Slack app with `chat:write`, `channels:read`, `channels:history` scopes.

### Google Drive — read and search Drive files
```yaml
- name: google-drive
  command: npx
  args: ["-y", "@modelcontextprotocol/server-googledrive"]
  env:
    GDRIVE_CLIENT_ID: "${GDRIVE_CLIENT_ID}"
    GDRIVE_CLIENT_SECRET: "${GDRIVE_CLIENT_SECRET}"
    GDRIVE_REDIRECT_URI: "http://localhost:3000/oauth2callback"
```

### Everything — test/example server with all tool types
```yaml
- name: everything
  command: npx
  args: ["-y", "@modelcontextprotocol/server-everything"]
  env: {}
```
Reference implementation with prompts, resources, and tools. Useful for
testing MCP client integrations.

---

## Python MCP Servers (uvx / python -m)

### Git — git operations
```yaml
- name: git
  command: uvx
  args: ["mcp-server-git", "--repository", "/path/to/repo"]
  env: {}
```
Or without uvx:
```yaml
- name: git
  command: python
  args: ["-m", "mcp_server_git", "--repository", "/path/to/repo"]
  env: {}
```
Install: `pip install mcp-server-git`

### Time — current time and timezone conversions
```yaml
- name: time
  command: uvx
  args: ["mcp-server-time", "--local-timezone", "America/New_York"]
  env: {}
```
Install: `pip install mcp-server-time`

---

## specsmith Governance MCP Server

The specsmith governance server ships built-in — no install required.

### specsmith governance
```yaml
- name: specsmith-governance
  command: specsmith
  args: ["mcp", "serve", "--project-dir", "."]
  env: {}
```
Exposes: `governance_audit`, `governance_checkpoint`, `governance_preflight`,
`governance_phase`, `governance_req_list`, `governance_trace_seal`.

Get the Warp-ready JSON snippet:
```bash
specsmith mcp install-warp
```

---

## Community / Third-party Servers

These are widely used with verified working configs. Require their own install.

### Exa — semantic web search
```yaml
- name: exa
  command: npx
  args: ["-y", "exa-mcp-server"]
  env:
    EXA_API_KEY: "${EXA_API_KEY}"
```
Get an API key at https://exa.ai — has a generous free tier.

### Tavily — AI-optimized web search
```yaml
- name: tavily
  command: npx
  args: ["-y", "tavily-mcp"]
  env:
    TAVILY_API_KEY: "${TAVILY_API_KEY}"
```
Get an API key at https://tavily.com

### Linear — issue tracking
```yaml
- name: linear
  command: npx
  args: ["-y", "@linear/mcp-server"]
  env:
    LINEAR_API_KEY: "${LINEAR_API_KEY}"
```

### Sentry — error monitoring
```yaml
- name: sentry
  command: uvx
  args: ["mcp-server-sentry"]
  env:
    SENTRY_AUTH_TOKEN: "${SENTRY_AUTH_TOKEN}"
    SENTRY_ORG_SLUG: "${SENTRY_ORG}"
```

### Playwright — browser automation (alternative to Puppeteer)
```yaml
- name: playwright
  command: npx
  args: ["-y", "@playwright/mcp"]
  env: {}
```
Requires `npx playwright install chromium` on first use.

### Redis — cache and key-value operations
```yaml
- name: redis
  command: npx
  args: ["-y", "mcp-server-redis"]
  env:
    REDIS_URL: "redis://localhost:6379"
```

### Notion — read and write Notion pages
```yaml
- name: notion
  command: npx
  args: ["-y", "@suesukim/mcp-server-notion"]
  env:
    NOTION_API_TOKEN: "${NOTION_TOKEN}"
```
Create an integration at https://www.notion.so/my-integrations

---

## Multi-server starter template

A ready-to-use `.specsmith/mcp.yml` for a typical full-stack development setup:

```yaml
# .specsmith/mcp.yml — full-stack dev starter
servers:
  - name: specsmith-governance
    command: specsmith
    args: ["mcp", "serve", "--project-dir", "."]
    env: {}

  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
    env: {}

  - name: github
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"

  - name: fetch
    command: npx
    args: ["-y", "@modelcontextprotocol/server-fetch"]
    env: {}

  - name: memory
    command: npx
    args: ["-y", "@modelcontextprotocol/server-memory"]
    env: {}

  - name: sequential-thinking
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    env: {}

  - name: brave-search
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
```

## Database development template

```yaml
servers:
  - name: specsmith-governance
    command: specsmith
    args: ["mcp", "serve", "--project-dir", "."]
    env: {}

  - name: postgres
    command: npx
    args: ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
    env: {}

  - name: sqlite
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./dev.db"]
    env: {}

  - name: redis
    command: npx
    args: ["-y", "mcp-server-redis"]
    env:
      REDIS_URL: "redis://localhost:6379"

  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
    env: {}
```

---

## Troubleshooting

**Server fails to start:**
```bash
specsmith esdb status   # check project health
npx -y @modelcontextprotocol/server-<name> --help   # test manually
```

**Authentication errors:** Confirm env vars are exported in your shell:
```bash
echo $GITHUB_TOKEN   # should print your token
```

**Windows path issues with filesystem server:** Use forward slashes or
double-backslash in args:
```yaml
args: ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/user/projects"]
```

**Missing feature or broken config?** Follow the `specsmith-error-reporting`
skill to check if it's a known issue before filing a new ticket.
