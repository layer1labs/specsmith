---
name: ollama-integration
description: Skill for integrating with Ollama for local AI model serving with specsmith governance
---

# Ollama Platform Integration

This skill enables specsmith projects to integrate with Ollama for local AI model serving while maintaining governance compliance.

## Requirements Covered

- REQ-112: Ollama Platform Integration
- Allows specsmith projects to integrate with Ollama for local AI model serving with human approval

## Integration Capabilities

### Platform Features
- Ollama model management and deployment
- Local model serving
- GPU and CPU resource utilization
- API endpoint configuration for Ollama services
- Model pulling and caching

### Governance Requirements
- Human approval required for all Ollama integrations
- Configuration management with governance controls
- Security best practices enforcement
- Resource monitoring and logging

## Usage Examples

```bash
# Initialize Ollama integration
specsmith skill install ollama-integration

# Configure Ollama platform settings
specsmith ollama configure --platform ollama --model-path /path/to/models --gpu-enabled true

# Pull and run model via Ollama
specsmith ollama run --model llama3 --port 11434
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
ollama:
  platform: ollama
  model_path: /path/to/models
  gpu_enabled: true
  port: 11434
  model_name: "llama3"
```

## Security Considerations

- All Ollama integrations require human approval
- Local model access controls must be configured
- Network security must be enforced
- Resource usage monitoring is required

## Compliance Requirements

- Follow security best practices for AI platform integrations
- Maintain audit logs of all Ollama interactions
- Ensure proper resource management and monitoring
