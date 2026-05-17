# SPDX-License-Identifier: MIT
"""Cloud CLI skills — AWS, Azure, GCP, GitHub CLI."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="aws-cli",
        name="AWS CLI v2 — profiles, SSO, S3, EC2, Lambda, CDK, SAM",
        description=(
            "AWS CLI v2 workflow: named profiles, SSO authentication, S3 operations, "
            "EC2/Lambda management, CDK deployment, and SAM local testing."
        ),
        domain=SkillDomain.CLOUD,
        tags=["aws", "aws-cli", "s3", "ec2", "lambda", "cdk", "sam",
              "iam", "cloudformation", "sso", "cloud"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["aws"],
        body="""\
# AWS CLI v2 Skill

## Installation & auth
```bash
# Install (all platforms)
# Windows: msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
# macOS:   brew install awscli
# Linux:   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
#           -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install

# Configure profile
aws configure --profile myprofile
# → Access Key ID, Secret Key, region, output format

# SSO (recommended for teams)
aws configure sso --profile myprofile
aws sso login --profile myprofile
export AWS_PROFILE=myprofile
```

## S3 operations
```bash
aws s3 ls s3://my-bucket/                          # list objects
aws s3 cp file.txt s3://my-bucket/prefix/          # upload
aws s3 cp s3://my-bucket/file.txt .                # download
aws s3 sync ./local-dir s3://my-bucket/prefix/ \\   # sync (delta only)
    --exclude "*.tmp" --delete
aws s3 presign s3://my-bucket/private.pdf --expires-in 3600  # signed URL
aws s3api put-object-acl --bucket my-bucket --key file.txt --acl private
```

## EC2 management
```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=my-server" \
    --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress}'
aws ec2 start-instances --instance-ids i-0123456789abcdef0
aws ec2 stop-instances --instance-ids i-0123456789abcdef0
aws ec2 describe-security-groups --group-names my-sg
aws ec2 authorize-security-group-ingress --group-id sg-xxx \
    --protocol tcp --port 22 --cidr 203.0.113.0/32
```

## Lambda deployment
```bash
# Package + deploy
zip function.zip lambda_function.py
aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip

# Invoke
aws lambda invoke --function-name my-function \
    --payload '{"key":"value"}' --cli-binary-format raw-in-base64-out response.json
cat response.json

# Logs
aws logs tail /aws/lambda/my-function --follow
```

## CDK (Cloud Development Kit)
```bash
npm install -g aws-cdk
cdk init app --language python
cdk bootstrap                       # one-time per account/region
cdk diff                            # preview changes
cdk deploy                          # deploy stack
cdk destroy                         # remove stack
cdk synth                           # generate CloudFormation template
```

## SAM local testing
```bash
pip install aws-sam-cli
sam init --runtime python3.12
sam local invoke MyFunction --event events/event.json
sam local start-api                  # local API Gateway
sam build && sam deploy --guided     # build + deploy
```

## Common patterns
```bash
# Get caller identity
aws sts get-caller-identity

# Parameter Store
aws ssm get-parameter --name /myapp/db-password --with-decryption \
    --query Parameter.Value --output text
aws ssm put-parameter --name /myapp/key --value "secret" --type SecureString

# Secrets Manager
aws secretsmanager get-secret-value --secret-id myapp/prod/db \
    --query SecretString --output text | jq .

# ECR login
aws ecr get-login-password | docker login --username AWS \
    --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
```

## Common pitfalls
- `--output json` is default; use `--query` (JMESPath) for field selection.
- Credentials precedence: env vars > profiles > instance role.
- Region must be set per-command or via `AWS_DEFAULT_REGION` env.
- MFA: use `aws sts get-session-token --serial-number arn:... --token-code 123456`.
""",
    ),
    SkillEntry(
        slug="azure-cli",
        name="Azure CLI — resource groups, AKS, App Service, Bicep, DevOps",
        description=(
            "Azure CLI workflow: login, resource group management, AKS cluster ops, "
            "App Service deployment, Bicep IaC, and Azure DevOps pipelines."
        ),
        domain=SkillDomain.CLOUD,
        tags=["azure", "az-cli", "aks", "app-service", "bicep",
              "azure-devops", "arm", "keyvault", "cloud", "microsoft"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["az"],
        body="""\
# Azure CLI Skill

## Authentication
```bash
az login                              # browser-based login
az login --use-device-code            # for headless/CI
az login --service-principal -u $APP_ID -p $CLIENT_SECRET --tenant $TENANT_ID

# List subscriptions + set default
az account list --output table
az account set --subscription "My Subscription"
az account show
```

## Resource groups
```bash
az group create --name myapp-rg --location eastus
az group list --output table
az group delete --name myapp-rg --yes --no-wait
az resource list --resource-group myapp-rg --output table
```

## App Service (Web Apps)
```bash
az appservice plan create --name myapp-plan --resource-group myapp-rg \
    --sku B1 --is-linux
az webapp create --name myapp --resource-group myapp-rg \
    --plan myapp-plan --runtime "PYTHON:3.12"
az webapp deployment source config-zip --resource-group myapp-rg \
    --name myapp --src myapp.zip
az webapp log tail --name myapp --resource-group myapp-rg
az webapp config appsettings set --name myapp --resource-group myapp-rg \
    --settings KEY=VALUE
```

## AKS (Azure Kubernetes Service)
```bash
az aks create --resource-group myapp-rg --name myaks \
    --node-count 2 --enable-addons monitoring --generate-ssh-keys
az aks get-credentials --resource-group myapp-rg --name myaks
kubectl get nodes                    # verify cluster connection
az aks scale --resource-group myapp-rg --name myaks --node-count 4
az aks upgrade --resource-group myapp-rg --name myaks --kubernetes-version 1.29.0
```

## Key Vault
```bash
az keyvault create --name myapp-kv --resource-group myapp-rg --location eastus
az keyvault secret set --vault-name myapp-kv --name db-password --value "secret"
az keyvault secret show --vault-name myapp-kv --name db-password --query value -o tsv
```

## Bicep IaC
```bicep
// main.bicep
param location string = resourceGroup().location
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: 'mystorage${uniqueString(resourceGroup().id)}'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
}
```
```bash
az deployment group create \
    --resource-group myapp-rg \
    --template-file main.bicep \
    --parameters location=eastus
az bicep upgrade             # update Bicep CLI
```

## Container Registry (ACR)
```bash
az acr create --resource-group myapp-rg --name myregistry --sku Basic
az acr login --name myregistry
docker tag myapp:latest myregistry.azurecr.io/myapp:v1
docker push myregistry.azurecr.io/myapp:v1
az acr build --registry myregistry --image myapp:v1 .  # build in cloud
```

## Common pitfalls
- Default subscription matters: always verify with `az account show`.
- Service principal vs managed identity: prefer managed identity in production.
- Bicep vs ARM: Bicep compiles to ARM; prefer Bicep for new IaC.
- Azure CLI ≠ Azure PowerShell: `az` vs `Az.*` cmdlets have different syntax.
""",
    ),
    SkillEntry(
        slug="gcp-cli",
        name="GCP (gcloud CLI) — projects, GKE, Cloud Run, GCS, IAM",
        description=(
            "Google Cloud Platform CLI: gcloud auth, project management, "
            "GKE clusters, Cloud Run serverless, GCS buckets, and IAM."
        ),
        domain=SkillDomain.CLOUD,
        tags=["gcp", "gcloud", "google-cloud", "gke", "cloud-run",
              "gcs", "iam", "bigquery", "cloud", "firebase"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["gcloud"],
        body="""\
# GCP (gcloud CLI) Skill

## Authentication
```bash
gcloud init                           # interactive setup
gcloud auth login                     # browser-based
gcloud auth application-default login # ADC for SDKs
gcloud config set project myproject-id
gcloud config set compute/region us-central1

# Service account
gcloud auth activate-service-account --key-file=sa-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json
```

## GCS (Cloud Storage)
```bash
gsutil ls gs://my-bucket/
gsutil cp file.txt gs://my-bucket/prefix/
gsutil rsync -r ./local gs://my-bucket/
gsutil signurl -d 1h sa-key.json gs://my-bucket/file.txt
gsutil mb -l us-central1 gs://new-bucket
```

## Cloud Run
```bash
gcloud run deploy myservice \
    --image gcr.io/myproject/myapp:v1 \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi --cpu 1
gcloud run services list
gcloud run services update-traffic myservice --to-latest
gcloud run jobs create myjob --image gcr.io/myproject/myjob --region us-central1
gcloud run jobs execute myjob --region us-central1
```

## GKE (Google Kubernetes Engine)
```bash
gcloud container clusters create mycluster \
    --zone us-central1-a --num-nodes 3 --machine-type n2-standard-2
gcloud container clusters get-credentials mycluster --zone us-central1-a
kubectl get nodes
gcloud container clusters resize mycluster --num-nodes 5 --zone us-central1-a
```

## Container Registry / Artifact Registry
```bash
gcloud artifacts repositories create myrepo \
    --repository-format docker --location us-central1
gcloud auth configure-docker us-central1-docker.pkg.dev
docker tag myapp us-central1-docker.pkg.dev/myproject/myrepo/myapp:v1
docker push us-central1-docker.pkg.dev/myproject/myrepo/myapp:v1
gcloud builds submit --tag gcr.io/myproject/myapp .   # Cloud Build
```

## IAM
```bash
gcloud projects add-iam-policy-binding myproject-id \
    --member="serviceAccount:sa@myproject.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
gcloud iam service-accounts create mysa --display-name "My Service Account"
gcloud iam service-accounts keys create sa-key.json \
    --iam-account mysa@myproject.iam.gserviceaccount.com
```

## Common pitfalls
- Application Default Credentials: use `gcloud auth application-default login` for local dev.
- Billing: enable billing on new projects before using most services.
- Project vs Organization: resource hierarchy matters for IAM inheritance.
- Quota limits: check `gcloud services quotas` before large deployments.
""",
    ),
    SkillEntry(
        slug="gh-cli",
        name="GitHub CLI (gh) — PRs, issues, Actions, releases, Copilot",
        description=(
            "GitHub CLI: create/review PRs, manage issues, trigger Actions, "
            "create releases, manage codespaces, and use Copilot from terminal."
        ),
        domain=SkillDomain.CLOUD,
        tags=["github", "gh", "pull-request", "issues", "github-actions",
              "releases", "codespaces", "copilot", "git", "ci"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["gh", "git"],
        body="""\
# GitHub CLI (gh) Skill

## Authentication
```bash
gh auth login                         # browser-based
gh auth login --with-token < token.txt
gh auth status
gh auth token                         # print current token
```

## Pull Requests
```bash
gh pr create --title "feat: add feature" --body "Description" --base main
gh pr create --fill                   # use commit message for title/body
gh pr list --state open
gh pr view 42                         # view PR #42
gh pr checkout 42                     # check out PR branch
gh pr review 42 --approve -b "LGTM"
gh pr review 42 --request-changes -b "Please fix X"
gh pr merge 42 --squash --delete-branch
gh pr diff 42                         # show diff
```

## Issues
```bash
gh issue create --title "Bug: crash on X" --label bug --assignee @me
gh issue list --label "help wanted" --state open
gh issue close 15 --comment "Fixed in #42"
gh issue view 15
gh issue develop 15 --checkout       # create branch linked to issue
```

## GitHub Actions
```bash
gh workflow list                      # list workflows
gh workflow run deploy.yml            # trigger workflow
gh workflow run deploy.yml --field env=production
gh run list --workflow deploy.yml     # list runs
gh run watch 12345                    # follow live run
gh run view 12345 --log-failed        # show failed step logs
gh run rerun 12345 --failed-only      # re-run failed jobs
```

## Releases
```bash
gh release create v1.2.0 \
    --title "v1.2.0" \
    --notes "Bug fixes and performance improvements" \
    dist/myapp-linux-amd64 dist/myapp-windows.exe
gh release list
gh release download v1.2.0            # download assets
gh release delete v1.2.0             # delete release
```

## Repository management
```bash
gh repo create myorg/newrepo --public --clone
gh repo clone myorg/newrepo
gh repo fork upstream/repo --clone
gh repo sync                          # sync fork from upstream
gh repo view --web                    # open in browser
gh browse                             # open current dir in GitHub
```

## Copilot in terminal
```bash
gh copilot suggest "delete all stopped docker containers"   # get command suggestion
gh copilot explain "git rebase -i HEAD~3"                   # explain command
gh extension install github/gh-copilot                      # if not pre-installed
```

## Common patterns
```bash
# Automate PR comment
gh pr comment 42 --body "$(cat review_notes.md)"

# Get PR checks status
gh pr checks 42

# Search issues
gh issue list --search "label:bug assignee:@me"

# View Actions secrets (names only — values are masked)
gh secret list
gh secret set MY_SECRET --body "value"  # set secret
```

## Common pitfalls
- Token scope: `gh auth login` requests only needed scopes — add more with
  `gh auth refresh -s write:packages`.
- Org SSO: run `gh auth refresh` after enabling SSO on an organization.
- `gh pr create` from detached HEAD fails — ensure you're on a named branch.
""",
    ),
]
