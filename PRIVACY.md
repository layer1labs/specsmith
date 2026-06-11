# specsmith — Privacy Policy

**Last updated: April 2026**

## Summary

specsmith is a local CLI tool. It collects no telemetry, sends no analytics, and stores no data on Layer1Labs servers. The only external network calls it makes are those you explicitly configure.

---

## What data leaves your machine

### LLM providers (only when you run `specsmith run`)

When you start an agent session, specsmith sends your project's governance files (AGENTS.md, LEDGER.md snippets) and your chat messages to the LLM provider you have configured:

| Provider | Data destination | Privacy policy |
|---|---|---|
| Anthropic (Claude) | api.anthropic.com | https://www.anthropic.com/privacy |
| OpenAI (GPT) | api.openai.com | https://openai.com/policies/privacy-policy |
| Google (Gemini) | generativelanguage.googleapis.com | https://policies.google.com/privacy |
| Mistral | api.mistral.ai | https://mistral.ai/privacy |
| Ollama | localhost (no network call) | n/a — runs locally |

You control which provider is used. Layer1Labs has no visibility into what is sent to these providers — all requests go directly from your machine to their API.

### GitHub issues (`specsmith` doesn't file issues automatically)

The specsmith CLI itself never creates GitHub issues. Kairos has an optional, consent-gated bug reporter — see the [Kairos PRIVACY.md](https://github.com/layer1labs/kairos/blob/main/PRIVACY.md).

### Patent search (`specsmith patent`)

The `specsmith patent` command sends search queries to the USPTO Open Data Portal (developer.uspto.gov). No personally identifiable information is included unless you put it in the query.

---

## What stays on your machine

All of the following are stored locally only, never uploaded:

- `scaffold.yml` — project configuration
- `AGENTS.md`, `LEDGER.md`, governance files
- `.specsmith/credits.json` — token/cost usage history
- `.specsmith/trace.jsonl` — cryptographic trace vault
- `.specsmith/retrieval-index.json` — opt-in local search index
- API keys — stored in your OS keyring via `specsmith auth set` (never written to files)

---

## No telemetry

specsmith does **not**:

- Send crash reports or usage analytics to Layer1Labs
- Track which commands you run or how often
- Phone home to check for updates automatically (the `specsmith update` command checks PyPI only when you run it)
- Collect your name, email, or any personally identifiable information

---

## Self-update

`specsmith update` and `specsmith self-update` query `pypi.org/pypi/specsmith/json` to check the latest published version. This is a standard HTTPS GET request; PyPI may log your IP address per their own privacy policy (https://www.python.org/privacy/).

---

## Contact

For privacy questions: open an issue at https://github.com/layer1labs/specsmith or email privacy@layer1labs.dev
