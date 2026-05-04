# Bring-Your-Own-Endpoint (BYOE)

Specsmith ships first-class support for self-hosted OpenAI-v1-compatible
LLM servers (vLLM, llama.cpp `server`, LM Studio, TGI,
text-generation-webui, …). Every endpoint you register can be selected
per session via `--endpoint <id>` on `specsmith run`, `chat`, and
`serve` (PR-2).

## Quick start

Register a vLLM running on your LAN:

```sh
specsmith endpoints add \
  --id home-vllm \
  --name "Home vLLM" \
  --base-url http://10.0.0.4:8000/v1 \
  --default-model Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8 \
  --auth none \
  --set-default

specsmith endpoints test home-vllm
```

Once the test reports `ok`, run an agent against it:

```sh
specsmith run --endpoint home-vllm "summarise the last commit"
```

## Storage layout

All endpoints live in `~/.specsmith/endpoints.json` (override with
`SPECSMITH_HOME`). The on-disk schema is versioned:

```json
{
  "schema_version": 1,
  "default_endpoint_id": "home-vllm",
  "endpoints": [
    {
      "id": "home-vllm",
      "name": "Home vLLM",
      "base_url": "http://10.0.0.4:8000/v1",
      "auth": {"kind": "bearer-keyring",
               "keyring_service": "specsmith",
               "keyring_user": "endpoint:home-vllm"},
      "default_model": "Qwen/Qwen2.5-Coder-32B",
      "verify_tls": true,
      "tags": ["local", "coder"],
      "created_at": "2026-05-01T11:30:17Z"
    }
  ]
}
```

The file is written `chmod 600` on POSIX. Token bytes for the inline
strategy are the only secret material that ever lands in this file —
the keyring and env-var strategies leave it secret-free.

## Auth strategies

| Kind             | Where the token lives                              | When to use |
|------------------|----------------------------------------------------|-------------|
| `none`           | nowhere — request is unauthenticated                | trusted LAN, open vLLM dev box |
| `bearer-inline`  | `endpoints.json` (plaintext, `chmod 600`)           | quick scratch setups where keyring is unavailable |
| `bearer-env`     | the env var name you specify (`--token-env FOO`)    | CI / containers / 12-factor deploys |
| `bearer-keyring` | OS keyring, indexed by `(service, user)` (default)  | desktop / laptop installs (default) |

The `list --json` output redacts inline tokens to `"***"`. The CLI
never logs token bytes to terminal output.

## Health checks

```sh
specsmith endpoints test home-vllm --json
specsmith endpoints models home-vllm --json
```

`test` calls `<base_url>/models` with the resolved bearer token, prints
the latency in milliseconds, and reports up to 5 model ids. `models`
returns the full list.

If the endpoint does not expose `/v1/models`, `test` will still return a
clear error message — set `default_model` manually and rely on the
session-level model dropdown instead.

## CLI reference

| Command | Notes |
|---------|-------|
| `specsmith endpoints add` | Register a new endpoint. `--auth bearer-keyring` (default) prompts for the secret without echo. |
| `specsmith endpoints list [--json]` | Tabular by default, JSON for IDE consumers. Tokens are redacted. |
| `specsmith endpoints remove <id> [--purge-keyring]` | Remove the entry; pass `--purge-keyring` to also delete the saved token. |
| `specsmith endpoints default <id>` | Promote an existing endpoint to the default. |
| `specsmith endpoints test [<id>] [--timeout 5]` | Probe `/v1/models`. Exits 1 on failure. |
| `specsmith endpoints models [<id>]` | List every model the endpoint advertises. |

## Security notes

* The store path is `chmod 600` on POSIX where supported.
* `verify_tls: false` is opt-in (`--no-verify-tls`); otherwise the CLI
  verifies the certificate chain. Disabling it for an https endpoint is
  documented per-endpoint in the on-disk JSON so a drift audit can spot
  insecure configurations.
* `auth.kind == bearer-inline` is functional but not recommended.
  Prefer `bearer-keyring` when the OS keyring is available; otherwise
  use `bearer-env` and inject the secret through your shell or
  container environment.

## Roadmap

* **PR-2 (this milestone):** wires `--endpoint <id>` into `run`,
  `chat`, and `serve`, plus a new `_run_openai_compat` provider driver.
* **PR-3:** Endpoints tab and a per-session dropdown in the
  `specsmith-vscode` extension.
* **PR-4:** 0.8.0 release notes + tag.
