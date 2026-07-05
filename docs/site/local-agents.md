# Local agent defaults

This guide gives recommended first-run defaults for installing Specsmith with local or self-hosted coding agents.

The goal is not to make a small model behave like a frontier model. The goal is to put a smaller model inside a governed workflow where it only performs bounded, testable work:

1. inspect the project state;
2. run preflight before edits;
3. use the smallest useful local model for the role;
4. produce patches, not vague prose;
5. verify with tests, linters, builds, or simulator output;
6. save the governance ledger only after evidence exists.

For most fresh installs, use this rule:

- **Use Ollama** when you want the simplest local setup.
- **Use LM Studio** when you want a GUI model manager with an OpenAI-compatible local server.
- **Use a Python server** when you already run vLLM, llama.cpp, or another OpenAI-compatible endpoint in a virtual environment or on a remote GPU box.
- **Use no local model** on CPU-only machines unless the task is small and latency does not matter.

---

## Fresh install baseline

Install the CLI with `pipx` and keep it isolated from project dependencies:

```bash
pipx install specsmith
specsmith --version
```

In each governed project, start with the normal session anchor:

```bash
specsmith audit --project-dir .
specsmith sync --project-dir .
specsmith checkpoint --project-dir .
```

Then inspect the local model recommendation:

```bash
specsmith local-model recommend
```

This prints a role-oriented lineup with `fits`, `tight`, or `spills` status. Prefer the printed recommendation over guessing from model size alone.

If you want Specsmith to pull the best built-in Ollama fallback for the detected hardware, run:

```bash
specsmith local-model setup
```

---

## Default model policy

Specsmith's built-in local defaults intentionally bias toward stable, widely available Ollama tags:

| Role | Default family | Why |
|---|---|---|
| Coding | `qwen2.5-coder` | best default for patching, bug fixing, small refactors, tests, and code explanation |
| General | `qwen2.5` | planning, notes, requirements cleanup, and non-code project work |
| Reasoning / harder pass | `deepseek-r1` or `deepseek-coder-v2` | slower second opinion for debugging, review, and failure analysis |

Use newer/larger models as explicit overrides, not as the first-run default. For example, `qwen3-coder:30b` is a strong agentic coding option on large local machines, but it should be an intentional 24 GB+ / high-memory choice rather than the baseline for every install.

---

## Hardware defaults

Use the CLI's recommendation as the source of truth, but these are the practical defaults to expect.

| Machine class | Recommended default | Fast model | Harder pass | Notes |
|---|---|---|---|---|
| CPU-only or < 7 GB VRAM | none | optional `qwen2.5-coder:1.5b` or `3b` | remote/cloud reviewer | Do not default to local coding. Use governance + cloud or a remote endpoint. |
| 8 GB VRAM / 8-12 GB Apple unified | `qwen2.5-coder:7b` | `qwen2.5-coder:7b` | `deepseek-r1:7b` or remote reviewer | Good for bounded edits and tests. Keep context tight. |
| 10-16 GB VRAM / 16-24 GB Apple unified | `qwen2.5-coder:14b` | `qwen2.5-coder:7b` | `deepseek-r1:14b` or `deepseek-coder-v2:16b` if it fits | Best default for modern desktops and stronger laptops. |
| 20-24 GB VRAM / 32 GB+ Apple unified | `qwen2.5-coder:32b` | `qwen2.5-coder:14b` or `7b` | `deepseek-coder-v2:16b` | Good local-only development tier. |
| 24 GB+ VRAM with long-context needs | `qwen2.5-coder:32b`; optional `qwen3-coder:30b` | `qwen2.5-coder:14b` | separate reviewer model | Use for repository-scale reads only when the endpoint stays responsive. |
| Remote multi-GPU / high-memory server | endpoint-specific | endpoint-specific | endpoint-specific | Register as BYOE and route heavy roles to it. |

For 7B and 14B models, governed usage matters more than raw context size. Prefer short, relevant context plus tests over dumping the entire repository into the model.

---

## Preset selection

Specsmith stores agent profiles in `~/.specsmith/agents.json`. Start with one of the built-in presets:

```bash
specsmith agents preset list
```

Recommended defaults:

```bash
# Best default when cloud/frontier models are allowed.
specsmith agents preset apply default

# Fully local, Ollama-first setup.
specsmith agents preset apply local-only

# Lower-cost cloud setup with local fallback.
specsmith agents preset apply cost-conscious

# No local fallback; useful for CPU-only machines that should not run local LLMs.
specsmith agents preset apply frontier-only
```

Check what was installed:

```bash
specsmith agents list
specsmith agents route show
```

The important routes are:

| Activity | Preferred role |
|---|---|
| `chat`, `/code`, `/fix`, `/refactor` | coder |
| `/plan`, `/architect` | architect |
| `/review`, `/why`, `/audit` | reviewer |
| `/test` | tester |
| `/commit`, `/pr` | editor |

---

## Option A: Ollama install

Ollama is the simplest local path because Specsmith can talk to it directly.

Install Ollama, then pull the model tier that matches your machine.

### 8 GB VRAM

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b
```

### 12-16 GB VRAM

```bash
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5:14b
ollama pull deepseek-r1:14b
ollama pull qwen2.5-coder:7b
```

### 24 GB+ VRAM

```bash
ollama pull qwen2.5-coder:32b
ollama pull qwen2.5:32b
ollama pull deepseek-coder-v2:16b
ollama pull qwen2.5-coder:14b
```

Optional long-context / agentic coding model for high-memory machines:

```bash
ollama pull qwen3-coder:30b
```

Apply the local-only profile set:

```bash
specsmith agents preset apply local-only
specsmith agents list
```

Run a governed local session:

```bash
specsmith run --agent local-coder
```

Before any edit, force the preflight gate:

```bash
specsmith preflight "implement the smallest patch for <work item>" --json
```

If the decision is `accepted`, proceed with the work item id. If it is `needs_clarification`, do not edit yet.

---

## Option B: LM Studio install

Use LM Studio when you want a GUI to download/load models while still exposing an OpenAI-compatible endpoint to Specsmith.

1. Install LM Studio.
2. Download a model matching the hardware defaults above.
3. Load the model.
4. Start the local server.
5. Confirm the server is reachable at the OpenAI-compatible base URL, usually:

```text
http://localhost:1234/v1
```

Register LM Studio as a Specsmith BYOE endpoint:

```bash
specsmith endpoints add \
  --id lmstudio-local \
  --name "LM Studio Local" \
  --base-url http://localhost:1234/v1 \
  --default-model "<model-id-shown-by-lm-studio>" \
  --auth none \
  --set-default

specsmith endpoints test lmstudio-local
specsmith endpoints models lmstudio-local
```

Bind a coder profile to that endpoint:

```bash
specsmith agents add \
  --id lmstudio-coder \
  --role coder \
  --provider openai-compat \
  --endpoint lmstudio-local \
  --capability code \
  --capability diff-apply \
  --fallback ollama/qwen2.5-coder:7b

specsmith agents route set /code lmstudio-coder
specsmith agents route set /fix lmstudio-coder
specsmith agents route set /refactor lmstudio-coder
```

Run against the endpoint:

```bash
specsmith run --endpoint lmstudio-local
```

Use LM Studio for inference and Specsmith for governance. Do not rely on the chat UI alone for governed repository edits, because the governance ledger, preflight decisions, checkpoints, and save flow live in the Specsmith session.

---

## Option C: straight Python environment

Use this path when the local model server is part of a Python environment, container, LAN box, or remote GPU workstation.

Keep the Specsmith CLI in `pipx`, and keep the model server in its own environment:

```bash
pipx install specsmith
python -m venv .venv-local-llm
source .venv-local-llm/bin/activate
python -m pip install --upgrade pip
```

### Python server with vLLM

For NVIDIA GPU servers, vLLM is usually the best Python-native serving path:

```bash
pip install vllm
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
  --host 127.0.0.1 \
  --port 8000
```

For a larger GPU:

```bash
vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --host 127.0.0.1 \
  --port 8000
```

Register it with Specsmith:

```bash
specsmith endpoints add \
  --id python-vllm \
  --name "Python vLLM" \
  --base-url http://127.0.0.1:8000/v1 \
  --default-model Qwen/Qwen2.5-Coder-7B-Instruct \
  --auth none \
  --set-default

specsmith endpoints test python-vllm
```

### Python server with llama-cpp-python

For CPU, Apple Silicon, or GGUF-based setups:

```bash
pip install "llama-cpp-python[server]"
python -m llama_cpp.server \
  --model /path/to/qwen2.5-coder-7b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8000 \
  --n_ctx 8192
```

Then register it:

```bash
specsmith endpoints add \
  --id python-llamacpp \
  --name "Python llama.cpp" \
  --base-url http://127.0.0.1:8000/v1 \
  --default-model local-qwen-coder \
  --auth none \
  --set-default

specsmith endpoints test python-llamacpp
```

Bind routes to the Python endpoint:

```bash
specsmith agents add \
  --id python-local-coder \
  --role coder \
  --provider openai-compat \
  --endpoint python-vllm \
  --capability code \
  --capability diff-apply

specsmith agents route set /code python-local-coder
specsmith agents route set /fix python-local-coder
specsmith agents route set /refactor python-local-coder
```

Use a different endpoint id if you registered `python-llamacpp` instead of `python-vllm`.

---

## No-GPU defaults

Do not make a CPU-only model the default coding agent for serious work. It usually creates a bad user experience: slow responses, smaller context, weaker repair loops, and high frustration.

Recommended no-GPU setup:

```bash
specsmith agents preset apply cost-conscious
```

Then either:

- route coding/review work to a cloud provider;
- register a remote BYOE endpoint running on a GPU workstation;
- use CPU-only local models only for tiny classifier/editor tasks.

If you still need a local CPU model, treat it as experimental:

```bash
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5:3b
```

Use it for short, bounded tasks only:

- summarize a file;
- classify a work item;
- draft a test name;
- explain a small compiler error;
- propose a patch that a stronger reviewer will check.

---

## Governance profile for small models

Small models work best when Specsmith narrows the task before the model sees it.

Use this operating loop:

```bash
specsmith audit --project-dir .
specsmith sync --project-dir .
specsmith checkpoint --project-dir .

specsmith preflight "<specific change>" --json
specsmith run --agent <agent-id>

# run project-specific checks here
pytest
ruff check .
mypy src

specsmith checkpoint --project-dir .
specsmith save
specsmith kill-session
```

For small local models, enforce these rules:

| Rule | Why |
|---|---|
| One work item per session | prevents scope drift |
| One patch objective per preflight | keeps 7B/14B models inside their competence window |
| Relevant files only | avoids context dilution |
| Tests before save | makes the ledger evidence-based |
| Different reviewer when possible | catches shared model-family blind spots |
| No auto-commits from agent tools | keeps Specsmith as the audit boundary |

---

## Recommended first-run recipes

### Modern desktop with 12 GB VRAM

```bash
pipx install specsmith
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5:14b
ollama pull deepseek-r1:14b
specsmith agents preset apply local-only
specsmith local-model recommend
specsmith run --agent local-coder
```

### 8 GB laptop GPU

```bash
pipx install specsmith
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b
specsmith agents preset apply local-only
specsmith run --agent local-coder
```

### CPU-only laptop with remote GPU endpoint

```bash
pipx install specsmith
specsmith agents preset apply cost-conscious
specsmith endpoints add \
  --id remote-gpu \
  --name "Remote GPU" \
  --base-url http://<host>:8000/v1 \
  --default-model Qwen/Qwen2.5-Coder-14B-Instruct \
  --auth bearer-keyring \
  --set-default
specsmith endpoints test remote-gpu
specsmith run --endpoint remote-gpu
```

### LM Studio workstation

```bash
pipx install specsmith
specsmith endpoints add \
  --id lmstudio-local \
  --base-url http://localhost:1234/v1 \
  --default-model "<model-id-shown-by-lm-studio>" \
  --auth none \
  --set-default
specsmith endpoints test lmstudio-local
specsmith run --endpoint lmstudio-local
```

---

## Smoke test checklist

A new local agent install is healthy when all of these pass:

```bash
specsmith local-model recommend
specsmith agents list
specsmith agents route show
specsmith endpoints list
specsmith checkpoint --project-dir .
```

For endpoint-backed agents:

```bash
specsmith endpoints test <endpoint-id>
specsmith endpoints models <endpoint-id>
```

For Ollama-backed agents:

```bash
ollama list
ollama run qwen2.5-coder:7b "Return only: ok"
```

Then test a governed no-op task:

```bash
specsmith preflight "inspect repository and propose no code changes" --json
specsmith run "inspect repository and propose no code changes"
```

If the model cannot obey a no-op governance task, do not trust it with code edits yet.

---

## Related docs

- [Multi-Agent Profiles](agents.md)
- [Bring-Your-Own-Endpoint](endpoints.md)
- [Agent Integrations](agent-integrations.md)
- [Standalone CLI](standalone-cli.md)
- [Warp Integration](warp-integration.md)
