# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Platform engineering skill domain — Kubernetes, observability, GitOps, security."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="helm-chart",
        name="Helm Chart — packaging and deploying Kubernetes applications with Helm",
        description=(
            "Create and maintain Helm charts: chart structure, values, templates, hooks, "
            "and testing. Use when packaging a Kubernetes app as a Helm chart, upgrading "
            "a chart, or debugging a failing Helm release."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "helm",
            "kubernetes",
            "k8s",
            "chart",
            "values",
            "templates",
            "release",
            "upgrade",
            "hooks",
        ],
        project_types=["kubernetes-operator", "microservices"],
        body="""\
# Helm Chart

Helm is the package manager for Kubernetes. Charts package all the K8s
manifests needed to deploy an application.

## When to use
- Packaging a new Kubernetes application for distribution
- Upgrading or migrating an existing chart
- Debugging a failing `helm install` or `helm upgrade`

## Chart structure

```
my-app/
  Chart.yaml           ← metadata (name, version, description)
  values.yaml          ← default configuration values
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    _helpers.tpl       ← named templates (partials)
  charts/              ← sub-charts (dependencies)
  tests/
    test-connection.yaml
```

## Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: My application Helm chart
type: application
version: 1.2.3        # chart version (semver)
appVersion: "2.0.0"   # app version (string)
dependencies:
  - name: postgresql
    version: "13.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
```

## Deployment template

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.port }}
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secret.name }}
                  key: database-url
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

## values.yaml (defaults)

```yaml
replicaCount: 2
image:
  repository: myrepo/my-app
  tag: "latest"
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 8080
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## Common commands

```bash
# Lint before deploying
helm lint ./my-app

# Dry run (renders templates, no deploy)
helm install my-app ./my-app --dry-run --debug

# Install
helm install my-app ./my-app -n my-namespace --create-namespace \
  --set image.tag=v1.2.3

# Upgrade (rollout new version)
helm upgrade my-app ./my-app -n my-namespace \
  --set image.tag=v1.2.4 --atomic --timeout 5m

# Rollback
helm rollback my-app 1 -n my-namespace

# Debug a failed release
helm history my-app -n my-namespace
kubectl describe pod -l app.kubernetes.io/name=my-app -n my-namespace
```

## Verification checklist
- [ ] `helm lint` passes with no errors
- [ ] Resource `requests` and `limits` set for all containers
- [ ] Readiness and liveness probes configured
- [ ] Secrets referenced from K8s Secret (never hardcoded in values)
- [ ] `helm test` passes
- [ ] `helm upgrade --atomic` used in CI to auto-rollback on failure
""",
    ),
    SkillEntry(
        slug="monitoring-observability",
        name="Monitoring & Observability — OpenTelemetry, Prometheus, and Grafana",
        description=(
            "Instrument applications with OpenTelemetry: metrics, traces, and logs. "
            "Set up Prometheus alerting and Grafana dashboards. Use when adding observability "
            "to a new service, diagnosing a production incident, or building SLO dashboards."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "observability",
            "opentelemetry",
            "prometheus",
            "grafana",
            "tracing",
            "metrics",
            "logs",
            "slo",
            "alerting",
            "jaeger",
        ],
        body="""\
# Monitoring & Observability

The three pillars of observability: metrics (what is happening),
traces (where is it happening), logs (why is it happening).

## When to use
- Instrumenting a new service before production deployment
- Diagnosing a production incident
- Building SLO/SLA dashboards

## OpenTelemetry instrumentation (Python)

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("my-service")
meter = metrics.get_meter("my-service")

# Metrics
request_counter = meter.create_counter("http.requests.total")
request_duration = meter.create_histogram("http.request.duration.ms")

# Traces
with tracer.start_as_current_span("process-order") as span:
    span.set_attribute("order.id", order_id)
    span.set_attribute("customer.id", customer_id)
    result = process(order)
    span.set_status(StatusCode.OK)
```

## FastAPI automatic instrumentation

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
```

## Prometheus metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter("http_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["endpoint"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    with REQUEST_LATENCY.labels(request.url.path).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    return response
```

## Alerting rules (Prometheus)

```yaml
# alerts.yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5% for 5 minutes"

      - alert: SlowAPI
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 1s"
```

## SLO definition

```yaml
# slo.yaml
slo:
  - name: "API Availability"
    target: 99.9%
    indicator:
      metric: "http_requests_total"
      good: "status != 5xx"
    window: 30d
  - name: "API Latency"
    target: 95%
    indicator:
      metric: "http_request_duration_seconds"
      good: "< 0.5s"
    window: 30d
```

## Verification checklist
- [ ] All services emit the three pillars: metrics, traces, logs
- [ ] Trace IDs propagated across service boundaries
- [ ] Error rate and latency alerts configured
- [ ] Grafana dashboard deployed alongside the service
- [ ] SLOs defined and error budget tracked
- [ ] On-call runbook links in alert annotations
""",
    ),
    SkillEntry(
        slug="incident-response",
        name="Incident Response — production incident handling and post-mortems",
        description=(
            "Structured incident response: detection, severity classification, mitigation, "
            "communication, and post-mortem. Use when a production incident is declared, "
            "when writing a post-mortem, or when building an on-call runbook."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "incident",
            "on-call",
            "post-mortem",
            "runbook",
            "sev1",
            "mitigation",
            "rollback",
            "communication",
            "blameless",
        ],
        body="""\
# Incident Response

Every minute of downtime costs money and trust. A structured response
minimises both.

## When to use
- A production incident is declared
- Writing a post-mortem after an incident
- Building on-call runbooks for your team

## Severity levels

| Severity | Impact | Response SLA |
|---------|--------|-------------|
| SEV-1 | Service down for all users | Immediate — all hands |
| SEV-2 | Service degraded for many users | 15 minutes |
| SEV-3 | Minor degradation or partial outage | 1 hour |
| SEV-4 | Cosmetic or non-user-facing | Next business day |

## The response lifecycle

### 1. Detect
Alert fires → on-call receives page.
First responder acknowledges within 5 minutes.

### 2. Declare and assemble
```
# Declare in Slack #incidents:
"@incident-responders SEV-2 declared — checkout API 503s
IC: @alice | Comms: @bob | Bridge: [link]"
```

**Incident Commander (IC)** runs the call.
**Comms lead** handles stakeholder updates (every 30min for SEV-1/2).

### 3. Investigate (max 15 min before mitigation)

```bash
# Check deployment history
kubectl rollout history deployment/checkout-api -n prod

# Check recent errors
kubectl logs -l app=checkout-api -n prod --since=10m | grep ERROR

# Check dashboards
# → Grafana: error rate, latency, saturation
# → APM: slow traces, error traces
```

### 4. Mitigate FIRST, fix LATER

```bash
# Rollback if a recent deploy is suspected
kubectl rollout undo deployment/checkout-api -n prod

# Scale up if resource saturation
kubectl scale deployment/checkout-api --replicas=10 -n prod

# Feature flag off if a new feature caused it
```

### 5. Communicate (every 30 min for SEV-1/2)

```
Update 2: [14:35]
- Impact: ~15% of checkout requests failing
- Status: Rolling back to v2.3.1 — ETA 5 minutes
- Next update: 15:05
```

### 6. Resolve and close

```
Resolved [14:42]
- Root cause: OOM in checkout-api v2.3.2
- Fix: rolled back to v2.3.1
- Action items: add memory limit, load test new version
```

## Post-mortem template (blameless)

```markdown
## Incident: [title]
- Date: 2026-06-04
- Duration: 22 minutes
- Severity: SEV-2
- Impact: ~15% of checkout requests failed

## Timeline
- 14:20 — Alert fires: 503 rate > 5%
- 14:25 — IC declared, bridge opened
- 14:35 — Root cause identified (OOM)
- 14:42 — Service restored after rollback

## Root cause
OOM kill in checkout-api v2.3.2 due to memory leak in payment validator.

## What went well
- Alert fired within 2 minutes of impact
- Rollback was fast (< 5 min)

## What went wrong
- No memory limit set — OOM killed the pod instead of throttling
- Load test did not include the payment validator flow

## Action items
| Item | Owner | Due |
|------|-------|-----|
| Add memory limit to checkout-api | @alice | 2026-06-07 |
| Add payment flow to load test suite | @bob | 2026-06-11 |
```

## Verification checklist
- [ ] Alert has runbook link pointing to specific steps
- [ ] Rollback procedure documented and tested (not just theorised)
- [ ] Post-mortem written within 48h
- [ ] Action items assigned to owners with due dates
- [ ] Post-mortem shared with stakeholders and team
""",
    ),
    SkillEntry(
        slug="secret-management",
        name="Secret Management — Vault, SOPS, and Kubernetes secrets",
        description=(
            "Securely manage secrets: Vault integration, SOPS for encrypted GitOps, "
            "Kubernetes External Secrets, and secret rotation. Use when adding secrets "
            "to a service, setting up a secret management strategy, or rotating credentials."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "secrets",
            "vault",
            "sops",
            "external-secrets",
            "kubernetes",
            "rotation",
            "encryption",
            "gitops",
            "credentials",
        ],
        body="""\
# Secret Management

Secrets in git — even encrypted — are secrets at risk.
Treat secret management as a first-class engineering concern.

## When to use
- Adding secrets to a service for the first time
- Setting up a secret management strategy for a team
- Rotating compromised credentials

## Never do these
- `SECRET_KEY=abc123` in a Dockerfile or `.env` committed to git
- Secrets in container environment variables set from plain YAML
- Hardcoded API keys in source code

## Option 1: HashiCorp Vault (production standard)

```python
import hvac

client = hvac.Client(url="http://vault:8200", token=VAULT_TOKEN)

# Read a secret
secret = client.secrets.kv.v2.read_secret_version(
    mount_point="secret",
    path="my-service/database",
)
DB_URL = secret["data"]["data"]["url"]
```

Kubernetes integration:
```yaml
# vault-agent-injector annotations
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "my-service"
        vault.hashicorp.com/agent-inject-secret-database: "secret/data/my-service/database"
```

## Option 2: SOPS (encrypted secrets in git)

```bash
# Encrypt a secrets file with AWS KMS
sops --kms arn:aws:kms:us-east-1:123456789:key/abc123 \
     --encrypt secrets.env > secrets.enc.env

# Decrypt
sops --decrypt secrets.enc.env > secrets.env

# Edit in place
sops secrets.enc.env
```

## Option 3: Kubernetes External Secrets Operator

```yaml
# ExternalSecret pulls from AWS Secrets Manager into a K8s Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-service-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: my-service-secrets
    creationPolicy: Owner
  data:
    - secretKey: database-url
      remoteRef:
        key: /prod/my-service/database
        property: url
```

## Secret rotation

1. Generate new credentials (do NOT revoke old ones yet)
2. Deploy application with new credentials
3. Verify health checks pass
4. Revoke old credentials

```bash
# AWS: rotate RDS password
aws secretsmanager rotate-secret --secret-id /prod/my-service/database

# Vault: enable rotation policy
vault write database/rotate-role/my-service-db
```

## Verification checklist
- [ ] No secrets in source code or committed config files
- [ ] All secrets injected at runtime (not build time)
- [ ] Secret access logged and audited
- [ ] Rotation schedule defined (database passwords: 90 days)
- [ ] Compromised secret rotation procedure documented
- [ ] Least-privilege access — each service accesses only its own secrets
""",
    ),
    SkillEntry(
        slug="gitops",
        name="GitOps — declarative infrastructure with ArgoCD and Flux",
        description=(
            "Implement GitOps: declarative config in git, automated sync with ArgoCD or "
            "Flux, and environment promotion. Use when setting up CD for Kubernetes, "
            "implementing environment promotion, or debugging sync failures."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "gitops",
            "argocd",
            "flux",
            "kubernetes",
            "declarative",
            "sync",
            "promotion",
            "app-of-apps",
            "kustomize",
        ],
        body="""\
# GitOps

In GitOps, the desired state lives in git. The controller ensures the cluster
matches that state. No manual `kubectl apply` in production.

## When to use
- Setting up CD for Kubernetes applications
- Implementing dev → staging → production promotion
- Debugging a sync failure in ArgoCD/Flux

## ArgoCD application

```yaml
# argocd/my-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/k8s-config
    targetRevision: main
    path: apps/my-app/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true      # delete resources removed from git
      selfHeal: true   # revert manual changes to the cluster
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        maxDuration: 3m
```

## Kustomize environment overlays

```
apps/my-app/
  base/
    deployment.yaml
    service.yaml
    kustomization.yaml
  overlays/
    staging/
      kustomization.yaml   ← patches base for staging
      patch-replicas.yaml
    production/
      kustomization.yaml   ← patches base for prod
      patch-replicas.yaml
      patch-resources.yaml
```

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
patches:
  - path: patch-replicas.yaml
images:
  - name: my-app
    newTag: v2.3.1   # override image tag for production
```

## Promotion workflow

```
1. PR merged to main
2. CI builds image, pushes to registry with SHA tag
3. CI opens PR to k8s-config: update image tag in dev overlay
4. ArgoCD syncs dev environment automatically
5. After smoke tests pass, PR to update staging overlay
6. After staging approved, PR to update production overlay
```

## Debugging sync failures

```bash
# Check application status
argocd app get my-app

# Sync manually (bypass auto-sync)
argocd app sync my-app --force

# Check diff between git and cluster
argocd app diff my-app

# View resource status
kubectl get all -n production -l app.kubernetes.io/name=my-app
```

## Verification checklist
- [ ] All cluster resources managed by ArgoCD/Flux (no manual kubectl)
- [ ] `automated.selfHeal: true` to revert drift
- [ ] `automated.prune: true` to clean up deleted resources
- [ ] Separate overlay per environment (dev/staging/prod)
- [ ] Image tag promotion requires PR approval for production
- [ ] ArgoCD notifications configured for sync failures
""",
    ),
    SkillEntry(
        slug="serverless-functions",
        name="Serverless Functions — AWS Lambda, GCP Functions, and Cloudflare Workers",
        description=(
            "Build and deploy serverless functions: handler design, cold starts, "
            "VPC access, monitoring, and cost optimisation. Use when implementing event-driven "
            "processing, API backends, or scheduled jobs without managing servers."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "serverless",
            "lambda",
            "gcp-functions",
            "cloudflare-workers",
            "cold-start",
            "sam",
            "cdk",
            "event-driven",
            "faas",
        ],
        project_types=["serverless"],
        body="""\
# Serverless Functions

Serverless = no server management, pay per invocation.
Use it for event-driven processing, not for sustained high-throughput APIs.

## When to use
- Event-driven processing (S3 uploads, queue consumers, cron jobs)
- Infrequently-called API endpoints
- Edge computing with Cloudflare Workers

## AWS Lambda handler

```python
import json
import logging
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: dict, context: Any) -> dict:
    logger.info("Event: %s", json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))
        result = process(body)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result),
        }
    except ValueError as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    except Exception as e:
        logger.exception("Unhandled error")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}
```

## SAM template

```yaml
# template.yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 256
    Environment:
      Variables:
        DATABASE_URL: !Sub "{{resolve:secretsmanager:${DatabaseSecret}:SecretString:url}}"

Resources:
  ProcessOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: handlers.order.handler
      Runtime: python3.12
      Events:
        ProcessOrderQueue:
          Type: SQS
          Properties:
            Queue: !GetAtt OrderQueue.Arn
            BatchSize: 10
            FunctionResponseTypes:
              - ReportBatchItemFailures  # partial batch success
```

## Cold start mitigation

```python
# Initialise heavy clients outside the handler (reused across invocations)
import boto3
from sqlalchemy import create_engine

_db_engine = None

def get_db():
    global _db_engine
    if _db_engine is None:
        _db_engine = create_engine(os.environ["DATABASE_URL"], pool_size=1)
    return _db_engine

def handler(event, context):
    db = get_db()  # reuses initialised engine
    ...
```

## Cloudflare Workers

```typescript
// src/index.ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/data") {
      const data = await env.KV.get("my-key");
      return Response.json({ data });
    }

    return new Response("Not found", { status: 404 });
  },
};
```

## Cost and performance

| Factor | Optimisation |
|--------|-------------|
| Memory | Set to actual usage + 10% (more memory = faster CPU) |
| Cold starts | Python: 200-500ms, Go: < 50ms, Node: 100-200ms |
| Provisioned concurrency | Only for latency-sensitive, high-traffic endpoints |

## Verification checklist
- [ ] Handler is idempotent (safe to retry)
- [ ] Heavy initialisation outside the handler function
- [ ] Timeout set shorter than upstream timeout (avoid cascading failures)
- [ ] Dead-letter queue configured for async functions
- [ ] Memory tuned with AWS Lambda Power Tuning
- [ ] Structured logs with correlation IDs
""",
    ),
    SkillEntry(
        slug="oauth2-auth",
        name="OAuth2 & Authentication — implementing secure auth with OAuth2/OIDC",
        description=(
            "Implement OAuth2 and OpenID Connect: authorization code flow, token validation, "
            "refresh tokens, and PKCE. Use when adding login to an application, integrating "
            "with an identity provider, or auditing an existing auth implementation."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "oauth2",
            "oidc",
            "jwt",
            "authentication",
            "authorization",
            "pkce",
            "keycloak",
            "auth0",
            "cognito",
            "token",
        ],
        body="""\
# OAuth2 & Authentication

Never implement your own auth crypto. Use a proven library and a trusted IdP.

## When to use
- Adding login to an application
- Integrating with Google, GitHub, Auth0, Keycloak, Cognito, etc.
- Auditing an existing authentication implementation

## OAuth2 flows

| Flow | When |
|------|------|
| Authorization Code + PKCE | Web apps and mobile apps (standard for all new apps) |
| Client Credentials | Machine-to-machine (API to API) |
| Device Flow | Smart TVs, CLI tools |
| Implicit | **Deprecated** — never use in new code |

## Authorization Code + PKCE (web app)

```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(
        request, redirect_uri, code_challenge_method="S256"  # PKCE
    )

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]
    # Create session / JWT
    return create_session(user_info["email"])
```

## JWT validation

```python
from jose import jwt, JWTError
import httpx

async def get_jwks(jwks_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        return (await client.get(jwks_uri)).json()

def verify_jwt(token: str, jwks: dict, audience: str, issuer: str) -> dict:
    header = jwt.get_unverified_header(token)
    key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
    return jwt.decode(
        token,
        key,
        algorithms=[header["alg"]],
        audience=audience,
        issuer=issuer,
    )
```

## Machine-to-machine (client credentials)

```python
import httpx

async def get_m2m_token(client_id: str, client_secret: str, token_url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "api:read api:write",
        })
        return response.json()["access_token"]
```

## Token security rules
- JWTs should have short expiry (15 minutes for access tokens)
- Refresh tokens stored in httpOnly cookies (not localStorage)
- Always validate `aud`, `iss`, `exp`, `nbf` claims
- Never validate tokens with `verify=False`

## Verification checklist
- [ ] PKCE used for all browser-based flows
- [ ] Access tokens validated on every request (not just at login)
- [ ] Refresh tokens stored securely (httpOnly cookie, not localStorage)
- [ ] `audience` and `issuer` validated in JWT
- [ ] Token expiry enforced (not just checked at decode)
- [ ] Auth errors return 401/403 with no internal details
""",
    ),
    SkillEntry(
        slug="api-gateway",
        name="API Gateway — Kong, AWS API Gateway, and rate limiting patterns",
        description=(
            "Configure API gateways: routing, rate limiting, authentication, CORS, "
            "and request transformation. Use when setting up API routing for microservices, "
            "implementing cross-cutting API concerns, or migrating to a service mesh."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "api-gateway",
            "kong",
            "nginx",
            "aws-api-gateway",
            "rate-limiting",
            "routing",
            "cors",
            "auth",
            "load-balancing",
        ],
        body="""\
# API Gateway

The API gateway is the single entry point for all external traffic.
Centralise cross-cutting concerns here (auth, rate limiting, CORS, logging).

## When to use
- Routing traffic to multiple microservices
- Implementing rate limiting, authentication, or CORS centrally
- Adding API versioning without changing backend services

## Kong declarative config (deck)

```yaml
# kong.yaml
_format_version: "3.0"

services:
  - name: orders-service
    url: http://orders-api:8080
    routes:
      - name: orders-route
        paths:
          - /api/v1/orders
        strip_path: false
        methods: [GET, POST, PUT, DELETE]
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
          policy: redis
          redis_host: redis
      - name: jwt
        config:
          secret_is_base64: false
          claims_to_verify: [exp]
      - name: cors
        config:
          origins: ["https://app.example.com"]
          methods: [GET, POST, OPTIONS]
          headers: [Authorization, Content-Type]
          max_age: 86400
```

## Nginx as API gateway

```nginx
# nginx.conf
upstream orders-service {
    least_conn;
    server orders-1:8080;
    server orders-2:8080;
    server orders-3:8080;
}

server {
    listen 443 ssl;

    location /api/v1/orders {
        limit_req zone=api_rate burst=20 nodelay;
        proxy_pass http://orders-service;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

limit_req_zone $binary_remote_addr zone=api_rate:10m rate=10r/s;
```

## AWS API Gateway (HTTP API)

```yaml
# serverless.yml or CDK
Resources:
  HttpApi:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      ProtocolType: HTTP
      CorsConfiguration:
        AllowOrigins:
          - "https://app.example.com"
        AllowMethods: [GET, POST, PUT, DELETE, OPTIONS]
        AllowHeaders: [Authorization, Content-Type]

  ThrottleSettings:
    Type: AWS::ApiGatewayV2::Stage
    Properties:
      DefaultRouteSettings:
        ThrottlingBurstLimit: 100
        ThrottlingRateLimit: 50
```

## Key patterns

### Circuit breaker
```yaml
# Kong circuit breaker plugin
- name: request-termination
  config:
    status_code: 503
    message: "Service temporarily unavailable"
  enabled: true  # toggled programmatically when circuit opens
```

### Request transformation (API versioning without changing backends)
```yaml
- name: request-transformer
  config:
    add:
      headers:
        - "X-API-Version: 2"
    remove:
      headers:
        - "X-Internal-Token"
```

## Verification checklist
- [ ] Rate limiting configured per client IP and/or API key
- [ ] JWT validation at gateway level (before request reaches service)
- [ ] CORS configured with exact origin whitelist (not `*`)
- [ ] Request ID propagated to all upstream services
- [ ] Circuit breaker configured for downstream dependencies
- [ ] Access logs include: IP, method, path, status, latency
""",
    ),
    SkillEntry(
        slug="chaos-engineering",
        name="Chaos Engineering — controlled failure injection with Chaos Monkey / Litmus",
        description=(
            "Practice controlled failure injection to find weaknesses before they become "
            "incidents: pod failures, network latency, CPU stress. Use when preparing for "
            "a high-traffic event, after a post-mortem, or to validate SLOs."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "chaos-engineering",
            "litmus",
            "chaos-monkey",
            "resilience",
            "failure-injection",
            "game-day",
            "slo",
            "steady-state",
        ],
        body="""\
# Chaos Engineering

You don't know if your system is resilient until you break it deliberately.
Chaos engineering finds weaknesses before they find your users.

## When to use
- Preparing for a high-traffic event (Black Friday, product launch)
- After a post-mortem — validate the fix holds under failure
- Quarterly game days to exercise on-call runbooks

## The scientific method for chaos

1. **Define steady state** — what does "healthy" look like?
2. **Hypothesise** — "If pod X fails, the system stays healthy"
3. **Inject failure** — controlled, in a staging or non-critical prod segment
4. **Observe** — did the system stay in steady state?
5. **Learn** — fix what broke; document what held

## LitmusChaos (Kubernetes)

```yaml
# Kill 30% of pods for 2 minutes
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: checkout-chaos
  namespace: staging
spec:
  appinfo:
    appns: staging
    applabel: "app=checkout-api"
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "120"  # seconds
            - name: CHAOS_INTERVAL
              value: "30"
            - name: FORCE
              value: "false"
            - name: PODS_AFFECTED_PERC
              value: "30"
```

```yaml
# Inject 200ms network latency
    - name: pod-network-latency
      spec:
        components:
          env:
            - name: NETWORK_LATENCY
              value: "200"  # ms
            - name: TOTAL_CHAOS_DURATION
              value: "120"
```

## Game day checklist

### Before
- [ ] Notify stakeholders (especially on-call)
- [ ] Document hypothesis and expected outcome
- [ ] Set up monitoring dashboards on second screen
- [ ] Have rollback plan ready

### During
- Watch: error rate, latency, request success rate
- Record: what happened, timestamps, surprises

### After
- [ ] Confirm system returned to steady state
- [ ] Document findings (what broke that shouldn't have)
- [ ] File issues for surprises
- [ ] Update runbook with what you learned

## Steady state hypothesis example

```yaml
steady_state:
  - metric: "error_rate < 1%"
  - metric: "p99_latency < 500ms"
  - metric: "checkout_success_rate > 99%"
```

## Common chaos experiments to start with

| Experiment | What it validates |
|-----------|-------------------|
| Pod kill (random) | Auto-recovery, health checks |
| Network delay (200ms) | Timeouts, retry logic |
| CPU stress (90%) | Graceful degradation |
| Memory stress | OOM handling, eviction |
| DNS failure | Service discovery resilience |

## Verification checklist
- [ ] Steady state defined with measurable metrics
- [ ] Chaos run in staging before production
- [ ] Blast radius limited (staging namespace, canary % of traffic)
- [ ] Monitoring confirmed to detect the injected failure
- [ ] Rollback triggered immediately if steady state violated
- [ ] Findings documented and issues filed
""",
    ),
    SkillEntry(
        slug="service-mesh",
        name="Service Mesh — Istio and Linkerd for microservices communication",
        description=(
            "Configure a service mesh for mTLS, traffic management, and observability "
            "across microservices. Use when implementing zero-trust networking, canary "
            "deployments, or when debugging inter-service connectivity issues."
        ),
        domain=SkillDomain.PLATFORM_ENGINEERING,
        tags=[
            "service-mesh",
            "istio",
            "linkerd",
            "mtls",
            "traffic-management",
            "canary",
            "circuit-breaker",
            "zero-trust",
            "envoy",
        ],
        body="""\
# Service Mesh

A service mesh handles the communication layer between services: mTLS, retries,
circuit breaking, canary deployments — without changing application code.

## When to use
- Implementing zero-trust networking (mTLS between all services)
- Canary deployments without changing application code
- Debugging inter-service connectivity or latency issues

## Istio setup

```bash
# Install Istio
istioctl install --set profile=default -y

# Enable sidecar injection for a namespace
kubectl label namespace production istio-injection=enabled

# Verify
kubectl get pods -n production  # each pod should have 2 containers
```

## mTLS (automatic with Istio)

```yaml
# Enforce strict mTLS across the mesh
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # all traffic must be mTLS
```

## Traffic management

```yaml
# VirtualService: canary deployment (10% to v2)
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: checkout
spec:
  hosts:
    - checkout-service
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: checkout-service
            subset: v2
    - route:
        - destination:
            host: checkout-service
            subset: v1
          weight: 90
        - destination:
            host: checkout-service
            subset: v2
          weight: 10
```

```yaml
# DestinationRule: circuit breaker
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: checkout
spec:
  host: checkout-service
  trafficPolicy:
    connectionPool:
      http:
        http1MaxPendingRequests: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s  # eject unhealthy pods
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

## Linkerd (simpler alternative)

```bash
# Install Linkerd
linkerd install | kubectl apply -f -

# Inject Linkerd proxy into a deployment
kubectl get deploy -n production -o yaml | linkerd inject - | kubectl apply -f -

# View traffic stats
linkerd viz stat deploy -n production
```

## Observability

```bash
# Istio Kiali dashboard
kubectl port-forward svc/kiali 20001:20001 -n istio-system

# Request success rate
istioctl proxy-status
kubectl exec -n production deploy/checkout -- \
  curl localhost:15000/stats | grep upstream_cx_active
```

## Verification checklist
- [ ] mTLS STRICT mode enabled for the production namespace
- [ ] `PeerAuthentication` policy applied to all namespaces
- [ ] Circuit breaker configured for all external dependencies
- [ ] Canary deployment traffic split validated with metrics
- [ ] Service mesh data plane version matches control plane
- [ ] CPU/memory overhead of sidecar proxies accounted for
""",
    ),
]
