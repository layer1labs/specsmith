# Layered Identity Awareness - Design Document

> **Issue:** [#338](https://github.com/layer1labs/specsmith/issues/338)
> **Parent:** [#336](https://github.com/layer1labs/specsmith/issues/336) - ESDB branch-merge safety
> **Depends on:** [#339](https://github.com/layer1labs/specsmith/issues/339) - Layered configuration
> **Verification:** [#337](https://github.com/layer1labs/specsmith/issues/337) - Testable evidence contract

## 1. Purpose

Give Specsmith stable, explainable awareness of the human user, executing agent, service principal, replica/worktree, and session responsible for every governed action. Auto-detect useful identity signals, persist a global default, allow project-local overrides, and let users inspect or manually change the resolved identity without silently conflating display names with identity.

## 2. Identity Model

### 2.1 Identity Dimensions

Each governed action carries a composite identity record with these fields:

| Field | Type | Description | Example |
|---|---|---|---|
| `actor_id` | `str` | Stable, opaque human or service-principal identity. UUIDv7 or equivalent. | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `actor_display_name` | `str` | Mutable human-readable label. May change without affecting identity. | `Kai (kai@acme.io)` |
| `provider_accounts` | `list[ProviderAccount]` | Linked external identities. | `[{"provider": "github", "username": "kai-dev", "verified": true}]` |
| `agent_id` | `str` | Executing agent/model instance or named automation identity. | `zoo-architect-v2` or `ChronoCortex-LLM` |
| `delegation` | `Delegation or null` | Relationship showing agent acted for a human/service actor. | `{"delegator_id": "a1b2c3d4...", "role": "architect"}` |
| `replica_id` | `str` | Stable machine/worktree writer identity for distributed ESDB. | `worktree-laptop-01` or `esdb-replica-us-east` |
| `session_id` | `str` | One bounded execution session. UUIDv7, generated per run. | `ss-20260717-151736-a1b2c3d4` |
| `identity_confidence` | `float` | Resolution confidence: 0.0 (anonymous) to 1.0 (explicitly configured). | `0.95` |
| `verification_state` | `str` | How identity was resolved. | `auto_detected` |

Verification state values: `explicit`, `env`, `project_policy`, `global_default`, `auto_detected`, `git_identity`, `os_fallback`, `anonymous`.

### 2.2 ProviderAccount Model

```python
@dataclass
class ProviderAccount:
    provider: str          # "github", "gitlab", "bitbucket", "azure_devops", "git"
    username: str          # External platform username
    identity_id: str       # Stable cross-platform identity (optional)
    verified: bool         # Whether the link is cryptographically verified
    display_name: str      # Human-readable label from provider
```

### 2.3 Delegation Model

```python
@dataclass
class Delegation:
    delegator_id: str      # Human or service principal who authorized the action
    delegator_display: str # Display name of delegator
    role: str              # Role the agent is acting under
    scope: list[str]       # Requirement IDs or patterns this delegation covers
    expires_at: str | None # ISO 8601 expiry (optional)
```

### 2.4 Prohibited Identity Sources

The following MUST NOT be used as the canonical `actor_id` by themselves:

- Email addresses (privacy, mutable)
- Git display names (mutable, unverified)
- OS usernames (insecure, mutable)
- Branch names (environment artifact, not identity)
- Provider usernames alone (not cross-platform stable)

## 3. Identity Resolution Order

Each identity field is resolved independently using this precedence. A lower-confidence source MUST NOT silently replace a higher-confidence configured identity.

```
Identity Resolution Precedence
==============================

Level  Priority Source              Confidence  Verification
-----  ------------------------     ----------  -------------
1      CLI/session override         1.0         Explicit flag
       (--who, --agent, --replica)
2      Environment override         0.9         Env var present
       (SPECSMITH_ACTOR_ID, etc.)
3      Project-local identity       0.85        .specsmith/identity.yml
       override
4      Tracked project identity     0.8         Policy in scaffold.yml
       policy or permitted mapping
5      Global Specsmith user        0.75        ~/.config/specsmith/identity.yml
       identity
6      Verified provider auto-detect 0.7        OAuth/token verification
7      Local Git identity           0.5         git config user.*
8      OS account fallback          0.3         os.getuser() / platform
9      Anonymous/generated          0.0         UUIDv7 with warning
```

### 3.1 Resolution Rules

1. **Stop-on-signal**: Resolution stops at the first source that provides a value for the field. Lower levels are consulted only if higher levels return null or empty.
2. **No silent downgrade**: If `actor_id` is already set at confidence >= 0.7, a level 7-9 source cannot replace it.
3. **Warning on fallback**: If resolution falls to level 7 or below, a warning is emitted to the session log.
4. **Anonymous generation**: Level 9 generates a UUIDv7 with a `generated-` prefix and emits a warning.

## 4. Configuration Layers

### 4.1 Global Identity Configuration

**Location:** `~/.config/specsmith/identity.yml` (or `$SPECSMITH_CONFIG_DIR/identity.yml`)

```yaml
user:
  actor_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  display_name: "Kai"
  provider_accounts:
    - provider: github
      username: kai-dev
      verified: true
    - provider: git
      username: kai@laptop
      verified: false

agent:
  default_agent_id: "zoo-architect-v2"
  allowed_agents:
    - "zoo-architect-v2"
    - "zoo-coder-v2"
    - "zoo-reviewer-v2"

replica:
  default_replica_id: "worktree-laptop-01"
```

### 4.2 Project-Local Identity Override

**Location:** `.specsmith/identity.yml` (project root)

```yaml
actor_policy:
  require_explicit_actor: true
  branch_mappings:
    main: "release-service-account"
    develop: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    "feature/*": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  allowed_agents:
    - "zoo-architect-v2"
    - "zoo-coder-v2"

replica_policy:
  worktree_mode: true
  replica_id_template: "worktree-{git_dir_hash}"
```

### 4.3 CLI Override

```bash
# Override actor for a single command
specsmith preflight "Fix REQ-001" --who a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Override agent
specsmith run "Refactor module X" --agent zoo-coder-v2

# Override replica (for distributed ESDB operations)
specsmith esdb push --replica worktree-laptop-01

# Combine overrides
specsmith verify --who a1b2c3d4... --agent zoo-reviewer-v2 --replica worktree-abc123
```

### 4.4 Environment Variables

```bash
export SPECSMITH_ACTOR_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
export SPECSMITH_ACTOR_DISPLAY="Kai (CI)"
export SPECSMITH_AGENT_ID="ci-runner-v2"
export SPECSMITH_REPLICA_ID="esdb-replica-us-east"
export SPECSMITH_IDENTITY_MODE=explicit
```

## 5. Auto-Detection Providers

### 5.1 Provider Priority

Auto-detection runs in order. The first provider that returns a **verified** identity wins. Unverified results are used as fallback.

```
Auto-Detection Chain:
  1. Git config (user.name, user.email) -> confidence 0.5
  2. GitHub CLI (gh auth status) -> confidence 0.7 (if token valid)
  3. GitLab CLI (glab auth status) -> confidence 0.7
  4. Azure DevOps (az account show) -> confidence 0.7
  5. Bitbucket (app password check) -> confidence 0.6
  6. OS username (os.getuser()) -> confidence 0.3
```

### 5.2 Verification Methods

| Provider | Verification Method | Max Confidence |
|---|---|---|
| Git config | Local file read | 0.5 |
| GitHub | OAuth token introspection | 0.7 |
| GitLab | Personal access token validation | 0.7 |
| Azure DevOps | `az account show` API call | 0.7 |
| Bitbucket | App password ping | 0.6 |
| OS username | Local lookup | 0.3 |

### 5.3 IdentityResolver Implementation

```python
class IdentityResolver:
    """Resolves layered identity from all available sources."""

    def resolve(self, project_dir: Path, cli_overrides: CLIOverrides) -> ResolvedIdentity:
        # 1. Check CLI overrides first
        if cli_overrides.actor_id:
            return self._build_identity(
                actor_id=cli_overrides.actor_id,
                confidence=1.0, verification_state="explicit",
            )

        # 2. Check environment
        env_actor = os.environ.get("SPECSMITH_ACTOR_ID")
        if env_actor:
            return self._build_identity(
                actor_id=env_actor,
                display_name=os.environ.get("SPECSMITH_ACTOR_DISPLAY", ""),
                confidence=0.9, verification_state="env",
            )

        # 3. Check project-local identity
        project_identity = self._load_project_identity(project_dir)
        if project_identity and self._is_branch_match(project_identity, project_dir):
            return self._build_identity(
                actor_id=project_identity.actor_id,
                confidence=0.85, verification_state="project_policy",
            )

        # 4. Check global identity
        global_identity = self._load_global_identity()
        if global_identity:
            return self._build_identity(
                actor_id=global_identity.actor_id,
                display_name=global_identity.display_name,
                provider_accounts=global_identity.provider_accounts,
                confidence=0.75, verification_state="global_default",
            )

        # 5. Auto-detect from providers
        for provider in self._providers:
            result = provider.detect()
            if result:
                confidence = result.verified * 0.7 + (1 - result.verified) * 0.3
                return self._build_identity(
                    actor_id=result.identity_id or self._generate_anonymous_id(),
                    display_name=result.display_name,
                    provider_accounts=[result.to_provider_account()],
                    confidence=confidence, verification_state="auto_detected",
                )

        # 6. Fallback: anonymous with warning
        warnings.warn("Identity resolved to anonymous/generated identity")
        return self._build_identity(
            actor_id=self._generate_anonymous_id(),
            confidence=0.0, verification_state="anonymous",
        )
```

## 6. Governance Integration

### 6.1 Identity in Preflight

Every preflight call includes the resolved identity in its decision payload:

```python
def run_preflight(utterance: str, project_dir: Path, **kwargs) -> dict:
    identity = identity_resolver.resolve(project_dir, cli_overrides=kwargs)
    return {
        "decision": "accepted",
        "work_item_id": "...",
        "identity": {
            "actor_id": identity.actor_id,
            "actor_display_name": identity.actor_display_name,
            "agent_id": identity.agent_id,
            "replica_id": identity.replica_id,
            "session_id": identity.session_id,
            "confidence": identity.confidence,
            "verification_state": identity.verification_state,
            "delegation": identity.delegation,
        },
    }
```

### 6.2 Identity in Ledger Events

Every ledger event records the identity of the actor who triggered it:

```json
{
  "event_id": "evt-20260717-151736-001",
  "event_type": "preflight_decision",
  "timestamp": "2026-07-17T15:17:36Z",
  "identity": {
    "actor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "agent_id": "zoo-architect-v2",
    "replica_id": "worktree-laptop-01",
    "session_id": "ss-20260717-151736-a1b2c3d4"
  },
  "data": {
    "utterance": "Fix REQ-001 authentication flow",
    "decision": "accepted",
    "work_item_id": "WI-20260717-001"
  }
}
```

### 6.3 Identity-Aware Governance Decisions

Identity affects governance decisions in these ways:

| Decision | Identity Factor | Effect |
|---|---|---|
| Preflight acceptance | `actor_id` in permitted list | Lowers confidence threshold |
| Release gating | `actor_id` has release role | Allows release operations |
| Branch protection | `replica_id` matches worktree | Allows direct push |
| Audit trail | `agent_id` + `delegation` | Records who authorized automation |
| Conflict resolution | `actor_id` + `replica_id` | Determines write priority in ESDB |

### 6.4 Role-Based Access in Governance

```yaml
roles:
  developer:
    allowed_commands: ["read_file", "write_file", "apply_diff", "run_shell"]
    blocked_commands: ["release", "migrate-project", "esdb-repair"]
    max_confidence_target: 0.85

  architect:
    allowed_commands: ["read_file", "write_file", "apply_diff", "run_shell", "run_slash_command"]
    blocked_commands: ["release", "esdb-repair"]
    max_confidence_target: 0.9

  release_manager:
    allowed_commands: ["*"]
    blocked_commands: []
    max_confidence_target: 0.95
    requires_delegation: true

  service_account:
    allowed_commands: ["read_file", "run_shell", "run_tests", "apply_diff"]
    blocked_commands: ["release", "migrate-project", "specsmith-kill-session"]
    max_confidence_target: 0.8
    requires_explicit_actor: true
```

## 7. Session Context Integration

The `SessionContext` in [`session_init.py`](src/specsmith/session_init.py:29) is extended with identity fields:

```python
@dataclass
class SessionContext:
    # ... existing fields ...

    # Identity fields (new)
    resolved_identity: ResolvedIdentity | None = None
    identity_warning: str | None = None  # Warning if confidence < 0.5

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        if self.resolved_identity:
            d["identity"] = self.resolved_identity.to_dict()
        if self.identity_warning:
            d["identity_warning"] = self.identity_warning
        return d
```

## 8. Examples

### 8.1 Developer Working Locally

Scenario: Developer Kai works on feature branch with global identity configured.

Resolution path:
1. CLI override: not provided
2. Environment: not set
3. Project-local: no branch mapping for feature/*
4. Global identity: FOUND - actor_id = a1b2c3d4...
5. Result: confidence 0.75, verification_state = global_default

### 8.2 CI Pipeline

Scenario: CI runner executes tests on main branch.

Resolution path:
1. CLI override: not provided
2. Environment: SPECSMITH_ACTOR_ID=ci-runner found
3. Result: confidence 0.9, verification_state = env

### 8.3 Release on Main Branch

Scenario: Release manager pushes to main with project-local policy.

Resolution path:
1. CLI override: not provided
2. Environment: not set
3. Project-local: branch mapping for main -> release-service-account
4. Result: confidence 0.85, verification_state = project_policy

### 8.4 Anonymous Fallback

Scenario: New developer with no global identity, no providers configured.

Resolution path:
1. CLI override: not provided
2. Environment: not set
3. Project-local: no identity.yml
4. Global identity: not configured
5. Auto-detect: git config found user.name = "newdev"
6. Result: confidence 0.5, verification_state = git_identity, WARNING emitted

### 8.5 Service Principal with Delegation

Scenario: CI agent runs tests on behalf of developer Kai.

Resolution:
- actor_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890 (Kai)
- agent_id: ci-runner-v2
- delegation: {delegator_id: a1b2c3d4..., role: developer, scope: [REQ-001, REQ-002]}
- confidence: 0.9 (from env), verification_state: env

## 9. CLI Commands for Identity Management

### 9.1 Identity Status

```bash
# Show currently resolved identity
specsmith identity status

# Show with debug info (resolution path)
specsmith identity status --verbose
```

Output:
```
Resolved Identity:
  actor_id:      a1b2c3d4-e5f6-7890-abcd-ef1234567890
  display_name:  Kai
  agent_id:      zoo-architect-v2
  replica_id:    worktree-laptop-01
  session_id:    ss-20260717-151736-a1b2c3d4
  confidence:    0.75
  verification:  global_default

Resolution path:
  [SKIP] Level 1: No CLI override
  [SKIP] Level 2: No environment variables
  [SKIP] Level 3: No project-local identity
  [FOUND] Level 5: Global identity from ~/.config/specsmith/identity.yml
```

### 9.2 Identity Set

```bash
# Set global identity
specsmith identity set --actor-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 --display "Kai"

# Set project-local identity
specsmith identity set --actor-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 --project-local

# Link provider account
specsmith identity set --provider github --username kai-dev --verified
```

### 9.3 Identity List

```bash
# List all configured global identities
specsmith identity list

# List project-local identity overrides
specsmith identity list --project-local
```

## 10. File Locations Summary

| Configuration | Location | Scope |
|---|---|---|
| Global identity | `~/.config/specsmith/identity.yml` | All projects |
| Project identity | `.specsmith/identity.yml` | Single project |
| Scaffold policy | `scaffold.yml` or `docs/SPECSMITH.yml` | Single project |
| Session state | `.specsmith/session.json` | Single session |
| Ledger events | `.specsmith/ledger.jsonl` | All actions |

## 11. Key Decisions

### 11.1 Why UUIDv7 for actor_id

- Time-ordered for efficient indexing in ESDB
- Contains timestamp for audit trail
- Random component prevents enumeration
- Standardized, not vendor-specific

### 11.2 Why Display Names Are Separate

- Display names are mutable (people change names)
- Identity must be stable across name changes
- Prevents identity fragmentation in audit trails
- Allows multiple display names per actor_id

### 11.3 Why No Email as Identity

- Privacy concerns (GDPR, data minimization)
- Emails change (account migration, role changes)
- Not cryptographically verifiable by default
- Can be stored in provider_accounts if needed

### 11.4 Why Confidence Scores

- Explainable governance decisions
- Users can see why identity was resolved a certain way
- Lower-confidence identities can trigger additional verification
- Audit trail shows resolution quality over time

## 12. Implementation Notes

### 12.1 New Modules Required

| Module | Purpose |
|---|---|
| `src/specsmith/identity/resolver.py` | Core IdentityResolver class |
| `src/specsmith/identity/models.py` | ProviderAccount, Delegation, ResolvedIdentity dataclasses |
| `src/specsmith/identity/providers.py` | Auto-detection providers (git, github, gitlab, etc.) |
| `src/specsmith/identity/store.py` | Global and project-local identity storage |
| `src/specsmith/commands/identity.py` | CLI commands for identity management |

### 12.2 Modified Modules

| Module | Changes |
|---|---|
| `src/specsmith/session_init.py` | Add identity fields to SessionContext |
| `src/specsmith/governance_logic.py` | Include identity in preflight/verify responses |
| `src/specsmith/cli.py` | Add --who, --agent, --replica CLI flags |
| `src/specsmith/_config_schema.py` | Add identity-related config fields |
| `src/specsmith/ledger.py` | Include identity in ledger events |

### 12.3 Backward Compatibility

- Existing projects without identity configuration fall through to auto-detection
- No breaking changes to existing CLI commands (new flags are optional)
- Ledger events without identity fields are still valid (identity is additive)
- Global identity file is optional; projects work without it

## 13. Acceptance Criteria

- [ ] Identity resolver resolves all 9 precedence levels correctly
- [ ] CLI flags --who, --agent, --replica override all other sources
- [ ] Environment variables override global and project-local config
- [ ] Project-local branch mappings work correctly
- [ ] Auto-detection providers verify identities before returning
- [ ] Ledger events include identity information
- [ ] Preflight decisions include resolved identity
- [ ] Session context includes identity fields
- [ ] Identity status command shows resolution path
- [ ] Warnings emitted for low-confidence identities
- [ ] Anonymous identity generation with prefix works
- [ ] No silent downgrades from high to low confidence
- [ ] Provider accounts can be linked and verified
- [ ] Delegation records are properly stored and checked