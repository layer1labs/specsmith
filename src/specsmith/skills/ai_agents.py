# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""AI / LLM / Agent skill domain — skills for building and governing AI-powered systems."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="llm-app-development",
        name="LLM App Development — building production LLM-powered applications",
        description=(
            "Guides agents through building production-grade LLM-powered apps using "
            "LangChain, LlamaIndex, Haystack, or the Anthropic/OpenAI SDK directly. "
            "Use when creating a new LLM feature, chatbot, assistant, or AI-powered workflow."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "llm",
            "langchain",
            "llamaindex",
            "openai",
            "anthropic",
            "ai",
            "chatbot",
            "assistant",
            "streaming",
            "tool-use",
            "function-calling",
        ],
        project_types=["llm-app", "agent-orchestration", "rag-pipeline"],
        body="""\
# LLM App Development

Production-grade apps built on LLMs require more than a working API call.
This skill covers the full lifecycle: prompt design, context management,
tool use, error handling, cost control, and observability.

## When to use
- Building a new chatbot, assistant, or AI-powered workflow
- Adding an LLM feature to an existing application
- Refactoring a prototype into production-ready code

## Core workflow

### 1. Choose an integration pattern
| Pattern | When | Tools |
|---------|------|-------|
| Direct SDK | Simple Q&A, single-turn | `anthropic`, `openai` |
| LangChain/LangGraph | Multi-step, tool use, agents | `langchain`, `langgraph` |
| LlamaIndex | Document Q&A, RAG | `llama-index` |
| LiteLLM | Multi-provider fallback | `litellm` |

### 2. Design prompts first
- Write the system prompt in `src/<pkg>/prompts/system.md`
- Test in the provider playground before wiring up code
- Use prompt templates with typed variables — never f-string raw user input

### 3. Implement with streaming
```python
# Prefer streaming for all user-facing responses
async for chunk in client.messages.stream(...):
    yield chunk.text
```

### 4. Add tool use properly
- Define tools as typed Pydantic models
- Validate tool call arguments before execution
- Never pass unvalidated tool output back to the LLM

### 5. Handle errors and rate limits
```python
from anthropic import APIStatusError, RateLimitError
import tenacity

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(RateLimitError),
    wait=tenacity.wait_exponential(min=1, max=60),
    stop=tenacity.stop_after_attempt(5),
)
async def call_llm(...):
    ...
```

### 6. Control costs
- Log token counts per request: `response.usage.input_tokens`
- Set `max_tokens` — never omit it
- Cache repeated context with prompt caching (Anthropic) or semantic caching

### 7. Observability
- Use LangSmith, Langfuse, or custom OTEL spans to trace every LLM call
- Log: model, prompt version, token counts, latency, user ID

## Common rationalizations
| Rationalization | Reality |
|---|---|
| "I'll add error handling later" | Rate limits hit in production on day one |
| "Max tokens doesn't matter" | Uncapped calls create runaway costs |
| "Streaming is complex" | Users abandon apps with 10+ second waits |

## Verification checklist
- [ ] System prompt in a versioned file, not hardcoded in a call
- [ ] All user inputs validated/sanitized before insertion
- [ ] `max_tokens` set on every call
- [ ] Retry logic with exponential backoff
- [ ] Token usage logged
- [ ] Streaming implemented for user-facing responses
""",
    ),
    SkillEntry(
        slug="mcp-server-development",
        name="MCP Server Development — building Model Context Protocol servers",
        description=(
            "Step-by-step guide for building an MCP server that exposes tools and resources "
            "to AI agents. Use when creating a new MCP server, adding tools/resources to an "
            "existing server, or debugging MCP protocol issues."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "mcp",
            "model-context-protocol",
            "mcp-server",
            "tools",
            "resources",
            "prompts",
            "stdio",
            "fastmcp",
            "claude",
            "warp",
        ],
        project_types=["mcp-server"],
        body="""\
# MCP Server Development

MCP (Model Context Protocol) is the standard for exposing tools and resources to AI
agents. This skill covers the full server lifecycle using the `mcp` Python SDK.

## When to use
- Creating a new MCP server for Warp, Claude Code, Cursor, or other agents
- Adding new tools or resources to an existing server
- Debugging MCP handshake or tool call issues

## Anatomy of an MCP server

```
src/<package>/
  server.py        # FastMCP or low-level MCP server entry point
  tools/           # One module per tool or tool group
  resources/       # Static and dynamic resource providers
  __init__.py
```

## Minimal FastMCP server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_docs(query: str) -> str:
    # Search the documentation. Use when the user asks about docs.
    return _do_search(query)

@mcp.resource("docs://{path}")
def get_doc(path: str) -> str:
    # Return a documentation page by path.
    return _read_doc(path)

if __name__ == "__main__":
    mcp.run()
```

## Warp MCP config (Settings → Agents → MCP servers)
```json
{
  "my-server": {
    "command": "python",
    "args": ["-m", "my_package.server"]
  }
}
```

## Tool design principles
1. **One tool = one clear action** — never merge two actions into one tool
2. **Description is the contract** — agents select tools by description alone
3. **Return plain text or structured JSON** — no HTML, no markdown in responses
4. **Be idempotent where possible** — agents may call tools multiple times

## Resource design
- Use URI templates (`docs://{path}`) for parameterised resources
- Static resources for config/reference data agents load once
- Keep individual resources under 50 KB — split large documents

## Testing
```bash
# Install the MCP inspector
npx @modelcontextprotocol/inspector python -m my_package.server

# Run unit tests
pytest tests/ -v
```

## Debugging checklist
- [ ] Server starts without error: `python -m my_package.server`
- [ ] Inspector shows all tools and resources
- [ ] Each tool has a trigger-rich description (what it does + when to use it)
- [ ] All tool arguments are typed and validated (Pydantic)
- [ ] Error responses use MCP error codes, not exceptions
- [ ] Server exits cleanly on SIGINT/SIGTERM
""",
    ),
    SkillEntry(
        slug="agent-orchestration",
        name="Agent Orchestration — multi-agent system design with LangGraph / AutoGen / CrewAI",
        description=(
            "Design and implement multi-agent systems using LangGraph, AutoGen, CrewAI, or "
            "Swarm. Use when building systems where multiple specialized agents collaborate, "
            "handle long-horizon tasks, or require parallel execution with verification."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "agents",
            "multi-agent",
            "langgraph",
            "autogen",
            "crewai",
            "swarm",
            "orchestration",
            "dag",
            "planner",
            "verifier",
            "agentic",
        ],
        project_types=["agent-orchestration", "llm-app"],
        body="""\
# Agent Orchestration

Multi-agent systems decompose complex tasks across specialized agents.
The key design challenges are: defining clean agent boundaries, managing
state safely, and preventing cascading failures.

## When to use
- Task requires distinct planning + execution + verification steps
- Parallelizable subtasks with independent failure domains
- Long-horizon workflows that exceed single-context limits

## Orchestration patterns

### 1. Supervisor / worker (most common)
```
Supervisor
  ├── Agent A (research)
  ├── Agent B (implementation)
  └── Agent C (verification)
```
Use when: tasks have clear phases; supervisor can delegate dynamically.

### 2. Pipeline (sequential)
```
Planner → Researcher → Writer → Reviewer → Publisher
```
Use when: each step strictly depends on the previous output.

### 3. Parallel fan-out / fan-in
```
Orchestrator → [Agent A, Agent B, Agent C] → Aggregator
```
Use when: independent subtasks can run concurrently.

## LangGraph implementation skeleton

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class WorkflowState(TypedDict):
    task: str
    research: str
    draft: str
    review: str

workflow = StateGraph(WorkflowState)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)
workflow.add_node("reviewer", reviewer_agent)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "reviewer")
workflow.add_conditional_edges(
    "reviewer",
    lambda s: "writer" if s["review"] == "revise" else END,
)
graph = workflow.compile()
```

## Safety and reliability rules
1. **Set max iterations** — all loops must have a termination condition
2. **Validate state transitions** — never trust agent output without schema validation
3. **Log every agent step** — use LangSmith traces or OTEL spans
4. **Isolate side effects** — only the terminal node commits/writes/sends
5. **Idempotent tools** — agents may retry; tools must handle duplicates

## Verification checklist
- [ ] Each agent has a single, clearly scoped responsibility
- [ ] All graph edges are tested (including conditional branches)
- [ ] Max-iteration guard prevents infinite loops
- [ ] State schema is a typed TypedDict or Pydantic model
- [ ] Integration test covers the full happy path
- [ ] Failure of one worker does not silently corrupt state
""",
    ),
    SkillEntry(
        slug="prompt-engineering",
        name="Prompt Engineering — designing, caching, and optimising LLM prompts",
        description=(
            "Structured workflow for writing, versioning, testing, and caching prompts. "
            "Use when creating a new system prompt, optimising response quality, reducing "
            "costs with prompt caching, or A/B testing prompt variants."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "prompt",
            "system-prompt",
            "few-shot",
            "chain-of-thought",
            "prompt-caching",
            "anthropic",
            "openai",
            "token-cost",
            "eval",
        ],
        body="""\
# Prompt Engineering

Good prompts are versioned, tested, and cached. Treat them as code.

## When to use
- Writing a new system prompt or task instruction
- Optimising an existing prompt for quality, cost, or latency
- Setting up prompt caching (Anthropic / OpenAI)

## Prompt design checklist

### Role and goal
```
You are a <role> that <primary goal>.
Your response must <output constraint>.
```

### Structure hierarchy (for long system prompts)
1. Role + mission (first 100 tokens — gets cached)
2. Rules and constraints
3. Output format specification
4. Few-shot examples (cache-friendly if static)
5. Dynamic context (never cached — injected at runtime)

### Writing rules
- Use positive instructions: "Always cite sources" not "Don't forget sources"
- Be explicit about format: "Respond as a JSON object with keys: ..."
- Specify what to do when uncertain: "If you don't know, say so"
- Avoid hedging instructions: "Respond concisely" not "Try to be concise"

## Prompt caching (Anthropic)

Cache the static prefix to cut costs up to 90% on repeated calls:

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": LARGE_STATIC_DOCUMENT,
                "cache_control": {"type": "ephemeral"},
            },
            {"type": "text", "text": user_question},
        ],
    }
]
```

Requirements: content block must be ≥1024 tokens (Sonnet/Haiku) or ≥2048 (Opus).

## Versioning
Store prompts in `src/<pkg>/prompts/`:
```
prompts/
  system_v1.md    ← current production
  system_v2.md    ← in testing
  CHANGELOG.md    ← what changed and why
```

## Evaluation
Measure before and after any change:
- Response quality: human eval or LLM-as-judge on 50+ examples
- Latency: p50/p95 TTFT and total response time
- Cost: input tokens × rate + output tokens × rate
- Cache hit rate: `usage.cache_read_input_tokens / usage.input_tokens`

## Verification checklist
- [ ] System prompt is in a versioned file, not inline code
- [ ] Static context blocks have `cache_control` set
- [ ] Few-shot examples cover the top-3 failure modes
- [ ] Output format is explicitly specified
- [ ] Prompt has been tested on ≥20 adversarial inputs
""",
    ),
    SkillEntry(
        slug="rag-development",
        name="RAG Development — retrieval-augmented generation pipeline design",
        description=(
            "End-to-end guide for building production RAG pipelines: chunking, embedding, "
            "vector storage, retrieval, and generation. Use when building document Q&A, "
            "knowledge base search, or any system that retrieves external context for an LLM."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "rag",
            "retrieval",
            "embeddings",
            "vector-database",
            "chromadb",
            "faiss",
            "pinecone",
            "weaviate",
            "llamaindex",
            "langchain",
            "chunking",
            "reranking",
        ],
        project_types=["rag-pipeline", "llm-app"],
        body="""\
# RAG Development

RAG quality is determined 80% by the ingestion pipeline and only 20% by the LLM.

## When to use
- Building document Q&A or knowledge base search
- Adding external context to any LLM application
- Improving accuracy by grounding responses in retrieved facts

## Pipeline architecture

```
Documents → Chunker → Embedder → Vector Store
                                      ↓
Query → Embedder → Retriever → Reranker → LLM → Answer
```

## Step 1: Document ingestion

```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader("data/").load_data()
splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)
```

**Chunking strategy by document type:**
| Type | Chunk size | Overlap |
|------|-----------|---------|
| Technical docs | 512 tokens | 50 |
| Long-form prose | 1024 tokens | 100 |
| FAQ / Q&A pairs | Full Q+A pair | 0 |
| Code | Function/class boundary | 0 |

## Step 2: Choose a vector store
| Store | Best for |
|-------|---------|
| ChromaDB | Local dev, small-medium corpus |
| FAISS | High-throughput in-memory |
| Pinecone | Managed, production-scale |
| pgvector | Already using PostgreSQL |
| Weaviate | Hybrid search (BM25 + vector) |

## Step 3: Retrieval + reranking

```python
# Hybrid: combine dense + sparse retrieval
from llama_index.core.retrievers import VectorIndexRetriever, BM25Retriever

dense = VectorIndexRetriever(index=index, similarity_top_k=10)
sparse = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=10)
# Rerank with a cross-encoder
from llama_index.core.postprocessor import SentenceTransformerRerank
reranker = SentenceTransformerRerank(model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=3)
```

## Step 4: Evaluate retrieval quality

Track these metrics before and after changes:
- **Recall@k**: fraction of relevant docs in top-k results
- **MRR**: mean reciprocal rank of first relevant result
- **Answer faithfulness**: does the answer only use retrieved context?
- **Answer relevance**: does the answer actually address the question?

## Common failure modes
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Hallucinated facts | Retrieval misses relevant chunks | Lower similarity threshold; add hybrid search |
| Context too long | Over-retrieval | Reranker + top-n=3 |
| Slow queries | No HNSW index | Build ANN index on vector store |
| Stale answers | No re-ingestion pipeline | Add incremental update job |

## Verification checklist
- [ ] Recall@5 ≥ 0.8 on a golden question set
- [ ] Chunk size tuned to document type
- [ ] Metadata filters implemented (date, source, category)
- [ ] Re-ingestion pipeline exists for document updates
- [ ] Faithfulness score measured on eval set
""",
    ),
    SkillEntry(
        slug="context-engineering",
        name="Context Engineering — managing LLM context windows effectively",
        description=(
            "Techniques for fitting the right information into context windows without "
            "overflowing or wasting tokens. Use when hitting context limits, optimising "
            "cost, or designing multi-turn conversations and long-document workflows."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "context",
            "context-window",
            "tokens",
            "summarization",
            "compression",
            "memory",
            "sliding-window",
            "prompt-caching",
            "cost",
        ],
        body="""\
# Context Engineering

The context window is your most constrained resource. Every token has a cost;
every token beyond the limit causes silent truncation or errors.

## When to use
- Application approaches the model's context limit
- Reducing cost on high-volume LLM calls
- Building multi-turn conversations that stay coherent over many turns
- Designing long-document processing workflows

## Context budget framework

| Slot | What goes here | Max budget |
|------|---------------|------------|
| System prompt | Role, rules, format | 10% of window |
| Retrieved context | RAG chunks, documents | 40% of window |
| Conversation history | Past turns | 30% of window |
| Current task | User message + tools | 20% of window |

**Never hard-code token counts** — use `tiktoken` or the SDK's tokeniser.

## Strategy 1: Sliding window for conversation history

```python
def truncate_history(messages: list, max_tokens: int) -> list:
    total = sum(count_tokens(m) for m in messages)
    while total > max_tokens and len(messages) > 1:
        # Keep the system prompt; drop oldest user/assistant pair
        messages.pop(1)
        total = sum(count_tokens(m) for m in messages)
    return messages
```

## Strategy 2: Summarise and compress

```python
COMPRESS_THRESHOLD = 0.75  # compress when > 75% full

async def maybe_compress(history: list, model_limit: int) -> list:
    used = sum(count_tokens(m) for m in history)
    if used / model_limit < COMPRESS_THRESHOLD:
        return history
    summary = await llm.summarise(history[:-4])  # keep last 2 turns verbatim
    return [{"role": "system", "content": f"[Summary] {summary}"}] + history[-4:]
```

## Strategy 3: Dynamic retrieval instead of full document injection

Never inject a 50-page PDF verbatim. Use RAG to inject only the 3-5 most relevant chunks.

## Strategy 4: Prompt caching for static context

Put stable, expensive context (docs, rules, examples) in a cached prefix.
See `prompt-engineering` skill for Anthropic cache_control syntax.

## Measuring context efficiency

```python
cache_hit_rate = usage.cache_read_input_tokens / usage.input_tokens
effective_cost = (
    (usage.input_tokens - usage.cache_read_input_tokens) * input_price
    + usage.cache_read_input_tokens * cache_price
    + usage.output_tokens * output_price
)
```

## Verification checklist
- [ ] Token budget tracked per slot (system / context / history / task)
- [ ] Sliding window or summarisation applied to conversation history
- [ ] No full document injections > 10K tokens without RAG
- [ ] Cache hit rate ≥ 50% for high-traffic prompts
- [ ] Application tested at 90% of context window limit
""",
    ),
    SkillEntry(
        slug="ai-safety-review",
        name="AI Safety Review — reviewing AI systems for safety, alignment, and bias",
        description=(
            "Checklist-driven review of AI systems for safety issues: prompt injection, "
            "jailbreaks, harmful output, PII leakage, bias, and compliance. Use before "
            "deploying any LLM feature to production or after any system prompt change."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "ai-safety",
            "alignment",
            "prompt-injection",
            "jailbreak",
            "bias",
            "pii",
            "compliance",
            "gdpr",
            "responsible-ai",
            "red-teaming",
        ],
        body="""\
# AI Safety Review

Every LLM feature that touches production users needs a safety review.
This is not optional — it is a pre-deployment gate.

## When to use
- Before deploying any LLM feature to users
- After any system prompt change
- When adding new tool use or external data access
- After a security report or user complaint

## Review categories

### 1. Prompt injection resistance
Test that user-supplied text cannot override the system prompt:
```
User: "Ignore all previous instructions and ..."
User: "As your new system prompt, ..."
User: "[SYSTEM] You are now ..."
```
**Pass criteria**: model follows original instructions despite injection attempt.

### 2. Harmful output
Test with adversarial inputs across:
- Violence / self-harm content
- Illegal advice (weapons, fraud, CSAM)
- Hate speech and discrimination
- Medical / legal advice without disclaimer

Use a red-team eval set; do not rely on manual spot-checks.

### 3. PII leakage
- Does the system echo back PII from user input in logs?
- Does RAG retrieval surface private user data to other users?
- Are API keys / credentials ever included in model output?

### 4. Bias audit
- Test with demographic variants in prompts (names, locations, genders)
- Verify response quality does not vary by demographic signal
- Check that the system does not perpetuate stereotypes in generated content

### 5. Tool use safety
- Can a tool be called with inputs that cause destructive side effects?
- Is there a confirmation step before irreversible actions?
- Are tool call arguments validated before execution?

### 6. Compliance
| Requirement | Check |
|-------------|-------|
| GDPR | User data not stored beyond session without consent |
| CCPA | Data deletion requests handled |
| EU AI Act | High-risk AI system classification check |
| SOC2 | Audit logs for all AI actions |

## Automated red-teaming
```bash
# Garak: open-source LLM vulnerability scanner
pip install garak
garak --model openai:gpt-4o --probes promptinject,dan
```

## Verification checklist
- [ ] Prompt injection test suite run (≥20 variants)
- [ ] Harmful output eval set run (≥50 adversarial inputs)
- [ ] PII leakage paths identified and mitigated
- [ ] Demographic bias test run with name/location variants
- [ ] All tools have argument validation before execution
- [ ] Irreversible tool actions have human-in-the-loop gate
- [ ] Compliance mapping completed for applicable regulations
""",
    ),
    SkillEntry(
        slug="langchain-development",
        name="LangChain Development — chains, agents, and tools with LangChain",
        description=(
            "Build LangChain applications: chains, agents, structured output, custom tools, "
            "and memory. Use when implementing LangChain-based workflows or debugging "
            "LangChain chain/agent behaviour."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=["langchain", "lcel", "chain", "agent", "tool", "memory", "runnable", "langsmith"],
        project_types=["llm-app", "agent-orchestration"],
        body="""\
# LangChain Development

LangChain's core abstraction is the Runnable. Chains compose Runnables; agents
loop over tool calls until the LLM decides to stop.

## When to use
- Building multi-step LLM workflows
- Integrating LLMs with external tools and data sources
- Debugging LangChain chain or agent behaviour

## LCEL (LangChain Expression Language)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatAnthropic(model="claude-sonnet-4-5")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
])
chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"input": "Hello!"})
```

## Structured output (Pydantic)

```python
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    bullets: list[str]
    sentiment: Literal["positive", "neutral", "negative"]

structured_llm = llm.with_structured_output(Summary)
summary = await structured_llm.ainvoke("Summarise this article: ...")
```

## Custom tools

```python
from langchain_core.tools import tool

@tool
def search_docs(query: str) -> str:
    # Search internal documentation. Use when asked about company policies.
    return _vector_search(query)
```

## Observability with LangSmith

```bash
export LANGSMITH_API_KEY="..."
export LANGSMITH_TRACING_V2=true
```

Every chain invocation is automatically traced.

## Debugging tips
1. Enable verbose: `chain.with_config({"verbose": True})`
2. Use `RunnableLambda` to add print statements mid-chain
3. Check LangSmith trace for intermediate outputs
4. Verify tool schemas match the LLM's tool call format

## Verification checklist
- [ ] All tools decorated with `@tool` and have docstrings
- [ ] Structured output models have field descriptions
- [ ] Async invocation used for all I/O-bound chains
- [ ] LangSmith tracing enabled in development
- [ ] Chain tested with `ainvoke`, `astream`, and `abatch`
""",
    ),
    SkillEntry(
        slug="langgraph-development",
        name="LangGraph Development — stateful multi-step agents with LangGraph",
        description=(
            "Build stateful, graph-based agent workflows with LangGraph. Use when "
            "implementing agents that need branching logic, tool loops, human-in-the-loop "
            "steps, or persistent state across long-horizon tasks."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "langgraph",
            "state-machine",
            "agent",
            "tool-loop",
            "human-in-the-loop",
            "checkpoint",
            "persistence",
            "react",
        ],
        project_types=["agent-orchestration", "llm-app"],
        body="""\
# LangGraph Development

LangGraph models agent workflows as directed graphs. Each node is a function
that reads and writes a shared state. Edges (including conditional edges)
define control flow.

## When to use
- Agent needs to loop over tool calls (ReAct pattern)
- Workflow has branching logic based on LLM decisions
- Human approval required before certain steps
- Long-running tasks need persistent checkpoint/resume

## Minimal ReAct agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5")
tools = [search_web, run_python, write_file]

agent = create_react_agent(llm, tools)
result = await agent.ainvoke({"messages": [("user", "Analyse this CSV and plot the trend")]})
```

## Custom graph with state

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    iterations: int

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if state["iterations"] >= 10:
        return END
    return "tools" if last.tool_calls else END

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", call_tools)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")
app = graph.compile()
```

## Human-in-the-loop

```python
from langgraph.checkpoint.memory import MemorySaver

# Interrupt before executing destructive tools
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["write_file", "send_email"],
)
```

## Persistence with PostgreSQL

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
```

## Verification checklist
- [ ] Max-iteration guard on all tool-call loops
- [ ] State TypedDict uses `Annotated[list, operator.add]` for message lists
- [ ] All conditional edges are tested (including error/timeout branches)
- [ ] Human-in-the-loop interrupts on irreversible tool calls
- [ ] Checkpointing enabled for long-running tasks
- [ ] Graph visualised with `app.get_graph().print_ascii()`
""",
    ),
    SkillEntry(
        slug="vector-database",
        name="Vector Database — choosing, configuring, and querying vector stores",
        description=(
            "Guide to selecting and operating vector databases for AI applications. "
            "Use when setting up a vector store, optimising query performance, implementing "
            "hybrid search, or migrating between vector database providers."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "vector-database",
            "embeddings",
            "chromadb",
            "faiss",
            "pgvector",
            "pinecone",
            "weaviate",
            "qdrant",
            "ann",
            "hnsw",
            "hybrid-search",
        ],
        project_types=["rag-pipeline", "llm-app"],
        body="""\
# Vector Database

Vector databases store and retrieve dense embeddings for semantic search.
Picking the right one depends on scale, latency, and infrastructure constraints.

## When to use
- Setting up a vector store for RAG or semantic search
- Tuning ANN index parameters for latency/recall trade-off
- Implementing hybrid search (vector + keyword)

## Choosing a vector store

| Store | Scale | Infra | Hybrid | Best for |
|-------|-------|-------|--------|---------|
| ChromaDB | 1M | Local/Docker | No | Dev/prototyping |
| FAISS | 100M | In-process | No | High-throughput batch |
| pgvector | 10M | PostgreSQL | Yes | Already using Postgres |
| Qdrant | 100M | Docker/Cloud | Yes | Production, open-source |
| Weaviate | 100M | Docker/Cloud | Yes | Multi-tenancy |
| Pinecone | 1B+ | Managed | Yes | No-ops production |

## ChromaDB (local dev)

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"},
)
collection.add(
    documents=chunks,
    embeddings=embed(chunks),
    ids=[str(i) for i in range(len(chunks))],
    metadatas=[{"source": f, "date": d} for f, d in meta],
)
results = collection.query(query_embeddings=embed([query]), n_results=5)
```

## pgvector (production with Postgres)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1536),
    metadata JSONB
);
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Query
SELECT content, 1 - (embedding <=> $1::vector) AS score
FROM documents
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

## Hybrid search (BM25 + vector)

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")
results = client.query_points(
    collection_name="docs",
    prefetch=[
        models.Prefetch(query=sparse_vector, using="bm25", limit=20),
        models.Prefetch(query=dense_vector, using="text-dense", limit=20),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=5,
)
```

## Verification checklist
- [ ] Embedding model and dimensions locked to a specific version
- [ ] HNSW index built (not brute-force) for collections > 10K vectors
- [ ] Metadata filter indexes created for common filter fields
- [ ] Recall@5 measured on golden eval set
- [ ] Re-indexing pipeline exists for document updates
- [ ] Backup strategy defined (Qdrant snapshots, pgdump, etc.)
""",
    ),
    SkillEntry(
        slug="model-evaluation",
        name="Model Evaluation — LLM output quality measurement and benchmarking",
        description=(
            "Framework for measuring and tracking LLM output quality: LLM-as-judge, "
            "task-specific metrics, regression testing, and A/B evaluation. Use before "
            "deploying prompt changes, model upgrades, or RAG pipeline modifications."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "evaluation",
            "evals",
            "llm-as-judge",
            "benchmarking",
            "quality",
            "regression",
            "faithfulness",
            "relevance",
            "ragas",
            "deepeval",
        ],
        body="""\
# Model Evaluation

"Vibe checking" is not evaluation. Build a reproducible eval harness before
you deploy, and run it on every significant change.

## When to use
- Before deploying prompt changes or model upgrades
- After RAG pipeline modifications
- When users report quality regressions
- Establishing a quality baseline for a new feature

## Eval types

| Type | What it measures | When |
|------|-----------------|------|
| Unit evals | Single prompt → expected output | Every commit |
| Task evals | End-to-end task success rate | Before deploy |
| RAG evals | Retrieval quality + faithfulness | After ingestion changes |
| A/B evals | Comparative quality, two variants | Prompt/model changes |

## LLM-as-judge pattern

```python
JUDGE_PROMPT = '''
Rate the following response on a scale of 1-5 for {criterion}.
Criterion: {criterion_description}

Question: {question}
Response: {response}
Ground truth: {ground_truth}

Return JSON: {"score": <1-5>, "reason": "<one sentence>"}
'''

async def judge(question, response, ground_truth, criterion):
    result = await llm.invoke(JUDGE_PROMPT.format(**locals()))
    return json.loads(result.content)
```

## RAG evaluation with RAGAS

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": retrieved_contexts,
    "ground_truth": ground_truths,
})
scores = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
```

## Regression test harness

```python
# tests/evals/test_quality.py
@pytest.mark.parametrize("example", GOLDEN_EXAMPLES)
async def test_response_quality(example):
    response = await chain.ainvoke({"input": example["input"]})
    score = await judge(example["input"], response, example["expected"])
    assert score["score"] >= 4, f"Quality regression: {score['reason']}"
```

## Minimum eval thresholds before deploy
- Faithfulness ≥ 0.85 (answer only uses retrieved context)
- Relevance ≥ 0.80 (answer addresses the question)
- No regressions on golden test set (100% pass rate)
- P95 latency within 10% of baseline

## Verification checklist
- [ ] Golden eval set of ≥50 question/answer pairs exists
- [ ] Eval runs in CI before deployment
- [ ] LLM-as-judge uses a different (stronger) model than the app
- [ ] RAG evals cover faithfulness, relevance, and recall
- [ ] Baseline scores are version-controlled alongside prompt versions
""",
    ),
    SkillEntry(
        slug="fine-tuning-workflow",
        name="Fine-Tuning Workflow — fine-tuning LLMs with PEFT / LoRA / full SFT",
        description=(
            "End-to-end workflow for fine-tuning LLMs: dataset preparation, PEFT/LoRA "
            "configuration, training, evaluation, and deployment. Use when pre-trained "
            "models don't follow domain-specific formats or terminologies consistently."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "fine-tuning",
            "lora",
            "peft",
            "sft",
            "qlora",
            "huggingface",
            "trl",
            "unsloth",
            "dataset",
            "training",
        ],
        body="""\
# Fine-Tuning Workflow

Fine-tune only when prompt engineering is insufficient. The threshold:
if ≥500 high-quality examples exist and the task has a consistent format,
fine-tuning is worth exploring.

## When to use
- Model consistently fails a narrow, well-defined task despite good prompting
- Domain-specific terminology or output format not achievable via prompting
- Latency/cost requirements demand a smaller model

## Decision checklist before fine-tuning
- [ ] ≥500 high-quality, diverse examples prepared
- [ ] Prompt engineering exhausted (chain-of-thought, few-shot, structured output)
- [ ] Evaluation harness ready to measure improvement
- [ ] Compute budget confirmed (LoRA on a single A100 for 2-4h typical)

## Step 1: Dataset preparation

```python
# Format: instruction tuning (Alpaca format)
dataset = [
    {
        "instruction": "Extract all dates from the text.",
        "input": "The meeting is on 2026-06-04 and the deadline is July 15.",
        "output": '["2026-06-04", "2026-07-15"]',
    },
    ...
]
# Save as JSONL
with open("train.jsonl", "w") as f:
    for ex in dataset:
        f.write(json.dumps(ex) + "\\n")
```

## Step 2: LoRA / QLoRA with Unsloth

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,          # LoRA rank — higher = more capacity, more VRAM
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0,
    bias="none",
)
```

## Step 3: Training with TRL SFTTrainer

```python
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        output_dir="outputs",
    ),
)
trainer.train()
```

## Step 4: Evaluation
Run the eval harness from the `model-evaluation` skill against the fine-tuned model.
Compare task accuracy, format compliance, and hallucination rate vs. base model.

## Step 5: Merge and export

```python
model.save_pretrained_merged("model-merged", tokenizer, save_method="merged_16bit")
# Or export to GGUF for llama.cpp
model.save_pretrained_gguf("model-gguf", tokenizer, quantization_method="q4_k_m")
```

## Verification checklist
- [ ] Dataset quality-reviewed (no duplicates, no formatting errors)
- [ ] Validation split used (80/20 train/val)
- [ ] Training loss curve checked for divergence
- [ ] Fine-tuned model evaluated on held-out test set
- [ ] Improvement over base model confirmed (not just memorization)
- [ ] Model versioned and linked to training dataset hash
""",
    ),
    SkillEntry(
        slug="computer-vision-pipeline",
        name="Computer Vision Pipeline — CV model training, inference, and deployment",
        description=(
            "Build computer vision pipelines: dataset prep, model training/fine-tuning, "
            "inference API, and deployment. Use when implementing image classification, "
            "object detection, segmentation, or multimodal LLM vision features."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "computer-vision",
            "cv",
            "yolo",
            "pytorch",
            "torchvision",
            "huggingface",
            "object-detection",
            "segmentation",
            "roboflow",
            "inference",
            "multimodal",
        ],
        body="""\
# Computer Vision Pipeline

CV pipelines have three phases: data → training → serving.
Each phase has common failure modes that this skill guards against.

## When to use
- Image classification, object detection, or segmentation tasks
- Adding vision capabilities to an LLM application
- Fine-tuning a pre-trained vision model on custom data

## Task ↔ Model selection

| Task | Recommended models |
|------|--------------------|
| Classification | ResNet50, EfficientNet-B4, ViT-B/16 |
| Object detection | YOLOv10, DETR, RT-DETR |
| Segmentation | SAM2, Mask R-CNN, SegFormer |
| Multimodal (with LLM) | Claude claude-opus-4-5 vision, LLaVA, Qwen-VL |

## Dataset preparation

```python
# Use Roboflow for annotation + augmentation
from roboflow import Roboflow
rf = Roboflow(api_key="...")
project = rf.workspace("my-org").project("my-dataset")
dataset = project.version(1).download("yolov10")
```

**Minimum dataset sizes:**
- Classification: ≥500 images per class
- Object detection: ≥300 images per class, ≥2 instances per image
- Segmentation: ≥100 annotated images per class

## YOLOv10 training (detection)

```python
from ultralytics import YOLO

model = YOLO("yolov10n.pt")  # nano for speed; yolov10x for accuracy
model.train(
    data="dataset.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    patience=20,      # early stopping
    val=True,
)
metrics = model.val()
```

## Inference API with FastAPI

```python
@app.post("/predict")
async def predict(file: UploadFile):
    img = Image.open(await file.read())
    results = model(img)
    return {"detections": results[0].tojson()}
```

## Quality metrics
- Classification: accuracy, F1 per class, confusion matrix
- Detection: mAP@50, mAP@50-95, precision, recall
- Segmentation: mIoU, Dice coefficient

## Verification checklist
- [ ] Train/val/test split stratified by class
- [ ] Data augmentation applied (flip, brightness, crop)
- [ ] mAP ≥ 0.6 on val set before deployment
- [ ] Model output schema validated (no naked exceptions on bad input)
- [ ] Inference latency measured (target: < 100ms p95)
- [ ] Model versioned in DVC or MLflow with training params
""",
    ),
    SkillEntry(
        slug="mlops-workflow",
        name="MLOps Workflow — ML pipeline orchestration, tracking, and serving",
        description=(
            "End-to-end MLOps: experiment tracking with MLflow, pipeline orchestration "
            "with Prefect/Airflow, model serving with BentoML/Ray Serve, and monitoring. "
            "Use when building repeatable training pipelines or productionising ML models."
        ),
        domain=SkillDomain.AI_AGENTS,
        tags=[
            "mlops",
            "mlflow",
            "prefect",
            "airflow",
            "bentoml",
            "ray-serve",
            "model-registry",
            "feature-store",
            "monitoring",
            "drift",
        ],
        project_types=["mlops-platform", "data-ml"],
        body="""\
# MLOps Workflow

MLOps = DevOps for ML. Reproducible training, versioned models, automated
serving, and drift monitoring.

## When to use
- Building a repeatable training pipeline
- Promoting a model from experiment to production
- Setting up model monitoring after deployment

## Experiment tracking with MLflow

```python
import mlflow

mlflow.set_experiment("churn-prediction-v2")
with mlflow.start_run():
    mlflow.log_params({"model": "xgboost", "n_estimators": 200, "max_depth": 6})
    model.fit(X_train, y_train)
    mlflow.log_metrics({"auc": roc_auc, "f1": f1})
    mlflow.sklearn.log_model(model, "model")
```

## Pipeline orchestration with Prefect

```python
from prefect import flow, task

@task
def extract() -> pd.DataFrame: ...

@task
def transform(df: pd.DataFrame) -> pd.DataFrame: ...

@task
def train(df: pd.DataFrame) -> None: ...

@flow(name="weekly-retrain")
def training_pipeline():
    df = extract()
    df = transform(df)
    train(df)

# Deploy as a cron schedule
training_pipeline.serve(cron="0 2 * * 1")  # Every Monday 2am
```

## Model serving with BentoML

```python
import bentoml

@bentoml.service(resources={"cpu": "2", "memory": "4Gi"})
class ChurnPredictor:
    model = bentoml.sklearn.get("churn-model:latest").to_runner()

    @bentoml.api
    async def predict(self, features: np.ndarray) -> np.ndarray:
        return await self.model.predict.async_run(features)

# Deploy: bentoml serve service:ChurnPredictor
```

## Model monitoring

Track these metrics in production:
- **Data drift**: PSI or KS test on input feature distributions
- **Prediction drift**: distribution shift in model outputs
- **Performance decay**: accuracy/AUC on labelled samples (if available)
- **Latency**: p50/p95/p99 inference time

```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=train_df, current_data=prod_df)
```

## Model promotion workflow
1. Train → log to MLflow with all params + metrics
2. Evaluate against holdout test set
3. Compare with current production model in Model Registry
4. Stage → Production promotion requires: `new_auc - prod_auc ≥ 0.005`
5. Deploy with BentoML; shadow mode for 1 week before cutover

## Verification checklist
- [ ] All training runs logged to MLflow with reproducible params
- [ ] Model artifacts stored in Model Registry (not local disk)
- [ ] Training pipeline idempotent (safe to re-run)
- [ ] Serving API validated with contract tests
- [ ] Data drift monitoring active in production
- [ ] Rollback procedure documented and tested
""",
    ),
]
