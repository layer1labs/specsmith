# SPDX-License-Identifier: MIT
"""DevOps skills — Docker, Kubernetes, Terraform, CI/CD pipelines."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="github-actions-ci",
        name="GitHub Actions CI — Layer1Labs pattern (zero-trust, parallel, coverage-gated)",
        description=(
            "Standard Layer1Labs GitHub Actions CI pattern: permissions: {} at workflow level, "
            "per-job contents: read grants, parallel jobs (no needs chain), full Python matrix "
            "3.10–3.13, and --cov-fail-under=85 coverage gate."
        ),
        domain=SkillDomain.DEVOPS,
        tags=[
            "ci",
            "github-actions",
            "permissions",
            "pytest",
            "coverage",
            "ruff",
            "mypy",
            "security",
            "python",
            "matrix",
            "zero-trust",
        ],
        platforms=["linux", "windows", "macos"],
        prerequisites=["gh"],
        body=(
            """\
# GitHub Actions CI Skill (Layer1Labs pattern)

Standard CI pattern used across all Layer1Labs / BitConcepts Python projects.
Reference implementation: `chronomemory/.github/workflows/ci.yml`

## Core principles
- `permissions: {}` at workflow level — deny all by default.
- `permissions: contents: read` on each individual job — grant minimum needed.
- All jobs run **in parallel** — no `needs:` dependency chain unless truly required.
- Full Python matrix: **3.10, 3.11, 3.12, 3.13** × ubuntu-latest, windows-latest.
- Coverage gate: `--cov-fail-under=85` when the project can sustain it.
  Omit or lower the threshold for large codebases with integration-heavy code
  (e.g. CLI drivers, HTTP servers) that are structurally hard to unit-test.
- Named jobs (`name:` field) for readable GitHub UI.
- `fail-fast: false` on the test matrix so all combinations are reported.

## Canonical template
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

# Default: deny all. Each job grants only what it needs.
permissions: {}

jobs:
  lint:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install ruff
      - name: ruff format --check
        run: ruff format --check src/ tests/
      - name: ruff check
        run: ruff check src/ tests/

  typecheck:
    name: Type check (mypy)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev]"
      - run: mypy src/<package>/

  test:
    name: Test (Python ${{ matrix.python-version }} / ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    permissions:
      contents: read
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -e ".[dev]"
      - run: pytest --cov=<package> --cov-report=term-missing --cov-fail-under=85
      # Note: omit --cov-fail-under when coverage is below 85% structurally
      # (large CLIs/servers with hard-to-unit-test paths).

  security:
    name: Security audit (pip-audit)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install pip-audit
      - run: pip install -e .
      - run: pip-audit
```

## What NOT to do
- Do NOT set `permissions: contents: read` at workflow level — use `permissions: {}` + per-job grants.
- Do NOT use `needs: [lint, typecheck]` to gate the test job — run all in parallel.
- Do NOT omit Python 3.11 from the matrix.
- Do NOT skip `--cov-fail-under` when unit coverage can sustain 85%.
  For large codebases with structural coverage limits, omit it rather than
  carrying a perpetually-failing gate.
- Do NOT use `cancel-in-progress: true` (concurrency block) unless there is a
  specific reason — chronomemory pattern omits it.
- Do NOT use `macos-latest` in the matrix unless macOS-specific behavior must be
  tested — it is ~10× slower and uses more CI minutes.

## Rust projects (additional jobs)
```yaml
  rust-lint:
    name: Rust lint (clippy + fmt)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - run: cargo fmt --check --all
      - run: cargo clippy --workspace -- -D warnings

  rust-test:
    name: Rust tests
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --workspace

  security:
    name: Security audit (cargo-audit)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo install cargo-audit --locked
      - run: cargo audit
```
"""
        ),
    ),
    SkillEntry(
        slug="docker-workflow",
        name="Docker — multi-stage builds, Compose, registries, security",
        description=(
            "Docker workflow best practices: multi-stage Dockerfiles, "
            "Compose for local dev, image security scanning, and registry push."
        ),
        domain=SkillDomain.DEVOPS,
        tags=[
            "docker",
            "containers",
            "dockerfile",
            "compose",
            "registry",
            "security",
            "devops",
            "ci",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=["docker"],
        body="""\
# Docker Workflow Skill

## Multi-stage Dockerfile (Python example)
```dockerfile
# Stage 1: build + test
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir build && pip install --no-cache-dir .
COPY src/ src/
RUN python -m pytest tests/ -q

# Stage 2: minimal runtime image
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages/ \
    /usr/local/lib/python3.12/site-packages/
COPY --from=builder /app/src/ src/
USER nobody   # never run as root
ENTRYPOINT ["python", "-m", "myapp"]
```

## Docker Compose (local development)
```yaml
# compose.yaml (Compose V2 format)
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./src:/app/src   # live reload in dev

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```
```bash
docker compose up -d               # start all services
docker compose logs -f api         # follow service logs
docker compose exec api bash       # shell into service
docker compose down -v             # stop + remove volumes
docker compose build --no-cache    # force rebuild
```

## Image security
```bash
# Scan for vulnerabilities
docker scout cves myapp:latest     # Docker Scout
trivy image myapp:latest           # Trivy (open source)
grype myapp:latest                 # Grype by Anchore

# Reduce attack surface
# - Use distroless or alpine base images
# - Multi-stage to exclude build tools
# - USER nobody or USER 1001
# - Read-only filesystem: --read-only (add tmpfs for /tmp)

# Sign images (cosign)
cosign sign --key cosign.key myregistry.io/myapp:v1
cosign verify --key cosign.pub myregistry.io/myapp:v1
```

## Registry operations
```bash
docker build -t myregistry.io/myapp:v1 .
docker push myregistry.io/myapp:v1
docker pull myregistry.io/myapp:v1
docker tag myapp:latest myregistry.io/myapp:latest
docker manifest inspect myregistry.io/myapp:v1   # check multi-arch

# Multi-arch build (buildx)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
    -t myregistry.io/myapp:v1 --push .
```

## Common pitfalls
- `.dockerignore`: exclude `node_modules/`, `.git/`, `*.pyc`, `.env` — reduces build context.
- Layer caching: copy `package.json` / `requirements.txt` before source code.
- `CMD` vs `ENTRYPOINT`: use ENTRYPOINT for the main process, CMD for defaults.
- Secrets in build: never use `RUN echo $SECRET` — use Docker secrets or build args with care.
""",
    ),
    SkillEntry(
        slug="kubernetes",
        name="Kubernetes — kubectl, Helm, namespaces, Ingress, GitOps",
        description=(
            "Kubernetes operations: kubectl commands, Helm chart management, "
            "namespace isolation, Ingress routing, and GitOps with ArgoCD/Flux."
        ),
        domain=SkillDomain.DEVOPS,
        tags=[
            "kubernetes",
            "kubectl",
            "helm",
            "ingress",
            "gitops",
            "argocd",
            "flux",
            "k8s",
            "devops",
            "containers",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=["kubectl", "helm"],
        body="""\
# Kubernetes Skill

## kubectl essentials
```bash
# Context / cluster management
kubectl config get-contexts
kubectl config use-context my-cluster
kubectl config set-context --current --namespace myapp

# Resources
kubectl get pods -n myapp -o wide
kubectl get all -n myapp
kubectl describe pod myapp-7d4b9c-xxx -n myapp
kubectl logs myapp-7d4b9c-xxx -f --tail=100   # follow logs
kubectl exec -it myapp-7d4b9c-xxx -- bash     # shell into pod
kubectl port-forward svc/myapp 8080:80         # local port forward
kubectl top pods -n myapp                      # resource usage

# Apply manifests
kubectl apply -f k8s/                          # apply directory
kubectl delete -f k8s/deployment.yaml
kubectl rollout status deployment/myapp -n myapp
kubectl rollout undo deployment/myapp -n myapp # rollback
kubectl scale deployment myapp --replicas=3

# Debugging
kubectl events --for pod/myapp-xxx -n myapp
kubectl run debug --image=busybox -it --rm -- sh  # ephemeral debug pod
```

## Deployment manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: myapp
spec:
  replicas: 2
  selector:
    matchLabels: {app: myapp}
  template:
    metadata:
      labels: {app: myapp}
    spec:
      containers:
      - name: myapp
        image: myregistry.io/myapp:v1
        ports: [{containerPort: 8000}]
        resources:
          requests: {cpu: 100m, memory: 128Mi}
          limits:   {cpu: 500m, memory: 256Mi}
        readinessProbe:
          httpGet: {path: /health, port: 8000}
        livenessProbe:
          httpGet: {path: /health, port: 8000}
          initialDelaySeconds: 10
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef: {name: myapp-secrets, key: database-url}
```

## Helm chart management
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo bitnami/postgresql
helm install my-postgres bitnami/postgresql \
    --namespace db --create-namespace \
    --set auth.postgresPassword=secret \
    --values my-values.yaml
helm upgrade my-postgres bitnami/postgresql --values my-values.yaml
helm list -A
helm rollback my-postgres 1
helm uninstall my-postgres -n db
```

## Ingress with nginx-ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts: [myapp.example.com]
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service: {name: myapp-api, port: {number: 8000}}
```

## Common pitfalls
- ImagePullBackOff: check registry credentials (`kubectl create secret docker-registry`).
- OOMKilled: increase memory limit or fix memory leak.
- CrashLoopBackOff: check logs with `kubectl logs --previous`.
- Pending pods: check `kubectl describe pod` for scheduling failures (resource requests too high).
""",
    ),
    SkillEntry(
        slug="terraform",
        name="Terraform — init/plan/apply, state, modules, workspaces",
        description=(
            "Terraform IaC workflow: provider setup, state management, "
            "module composition, workspace environments, and CI/CD integration."
        ),
        domain=SkillDomain.DEVOPS,
        tags=[
            "terraform",
            "iac",
            "infrastructure",
            "devops",
            "aws",
            "azure",
            "gcp",
            "modules",
            "workspaces",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=["terraform"],
        body="""\
# Terraform Skill

## Core workflow
```bash
terraform init               # download providers + modules
terraform validate           # syntax + schema check
terraform plan               # preview changes (never modifies infra)
terraform plan -out=tfplan   # save plan for CI/CD
terraform apply              # apply changes (prompts confirmation)
terraform apply tfplan       # apply saved plan (no prompt)
terraform apply -auto-approve  # CI/CD: skip prompt (use carefully)
terraform destroy            # destroy all resources
terraform show               # show current state
terraform output             # show output values
```

## Provider configuration
```hcl
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "myapp-tfstate"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}
provider "aws" {
  region = var.aws_region
  default_tags { tags = { Project = "myapp", ManagedBy = "terraform" } }
}
```

## Module pattern
```
modules/
  vpc/       main.tf, variables.tf, outputs.tf
  rds/       main.tf, variables.tf, outputs.tf
envs/
  prod/      main.tf, terraform.tfvars
  staging/   main.tf, terraform.tfvars
```
```hcl
# envs/prod/main.tf
module "vpc" {
  source     = "../../modules/vpc"
  cidr_block = "10.0.0.0/16"
  az_count   = 3
}
module "db" {
  source     = "../../modules/rds"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}
```

## Workspaces (environment management)
```bash
terraform workspace new staging
terraform workspace new prod
terraform workspace list
terraform workspace select prod
terraform plan -var-file=prod.tfvars   # workspace-specific vars
# Current workspace in HCL:
locals { env = terraform.workspace }
```

## State management
```bash
terraform state list                         # list resources in state
terraform state show aws_instance.web        # details of one resource
terraform state mv aws_instance.old_name aws_instance.new_name  # rename
terraform state rm aws_instance.web          # remove from state (not destroy)
terraform import aws_instance.web i-0123abc  # import existing resource
```

## CI/CD pattern (GitHub Actions)
```yaml
- name: Terraform Plan
  run: |
    terraform init
    terraform plan -out=tfplan -var-file=${{ env.ENV }}.tfvars
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

- name: Terraform Apply (on merge to main)
  if: github.ref == 'refs/heads/main'
  run: terraform apply -auto-approve tfplan
```

## Common pitfalls
- Always run `terraform plan` before `apply` — review the diff carefully.
- State locking: use DynamoDB (AWS) or GCS bucket with versioning for remote state.
- Sensitive values: use `sensitive = true` on outputs; never commit `.tfvars` with secrets.
- Provider upgrades: run `terraform init -upgrade` after version constraint changes.
""",
    ),
    SkillEntry(
        slug="ci-cd-github-actions",
        name="GitHub Actions CI/CD — workflows, matrix, secrets, caching",
        description=(
            "GitHub Actions workflow patterns: matrix builds, environment secrets, "
            "caching, composite actions, reusable workflows, and deployment gates."
        ),
        domain=SkillDomain.DEVOPS,
        tags=[
            "github-actions",
            "ci-cd",
            "yaml",
            "workflow",
            "matrix",
            "secrets",
            "caching",
            "deployment",
            "automation",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=["gh"],
        body="""\
# GitHub Actions CI/CD Skill

## Workflow skeleton
```yaml
name: CI
on:
  push: {branches: [main, develop]}
  pull_request: {branches: [main]}
  workflow_dispatch:           # manual trigger

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true    # cancel stale PR runs

permissions:
  contents: read
  packages: write             # for GHCR pushes
```

## Matrix build (multi-OS, multi-version)
```yaml
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ["3.11", "3.12"]
        exclude:
          - os: windows-latest
            python: "3.11"
    runs-on: ${{ matrix.os }}
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: {python-version: "${{ matrix.python }}"}
    - run: pip install -e ".[dev]" && pytest
```

## Dependency caching
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
    restore-keys: ${{ runner.os }}-pip-

# Node
- uses: actions/setup-node@v4
  with: {node-version: "20", cache: "npm"}  # built-in cache

# Cargo
- uses: Swatinem/rust-cache@v2
```

## Secrets and environment protection
```yaml
jobs:
  deploy:
    environment: production          # requires manual approval if configured
    steps:
    - env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
      run: ./deploy.sh

# OIDC (no long-lived keys)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456:role/github-actions-role
    aws-region: us-east-1
```

## Reusable workflow
```yaml
# .github/workflows/reusable-test.yml
on:
  workflow_call:
    inputs:
      python-version: {type: string, default: "3.12"}
    secrets:
      CODECOV_TOKEN: {required: true}
jobs:
  test:
    runs-on: ubuntu-latest
    steps: [...]
```
```yaml
# Calling workflow
jobs:
  call-test:
    uses: ./.github/workflows/reusable-test.yml
    with: {python-version: "3.12"}
    secrets: inherit
```

## Deployment gates
```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps: [...]

  deploy-production:
    needs: [deploy-staging]       # sequential
    environment:
      name: production
      url: https://myapp.com      # shown in deployment tab
    steps: [...]
```

## Common pitfalls
- `${{ secrets.FOO }}` prints as `***` — never log it.
- `needs:` creates sequential jobs; remove it for parallel execution.
- Windows path separators: use `path-separator: /` in checkout.
- Artifact upload/download: use actions/upload-artifact@v4 (v3 deprecated 2025).
""",
    ),
]
