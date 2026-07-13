---
name: vllm-integration
description: Skill for integrating with VLLM for large language model serving with specsmith governance
---

# VLLM Platform Integration

This skill enables specsmith projects to integrate with VLLM for large language model serving while maintaining governance compliance.

## Requirements Covered

- REQ-110: VLLM Platform Integration
- Allows specsmith projects to integrate with VLLM for large language model serving with human approval

## Integration Capabilities

### Platform Features
- VLLM model serving and deployment
- GPU and CPU resource management
- Model optimization and quantization
- API endpoint configuration for VLLM services
- Performance monitoring and tuning

### Governance Requirements
- Human approval required for all VLLM integrations
- Configuration management with governance controls
- Security best practices enforcement
- Resource monitoring and logging

## Usage Examples

```bash
# Initialize VLLM integration
specsmith skill install vllm-integration

# Configure VLLM platform settings
specsmith vllm configure --platform vllm --model-path /path/to/model --gpu-count 2

# Deploy model via VLLM
specsmith vllm deploy --model my-model --port 8000
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
vllm:
  platform: vllm
  model_path: /path/to/models
  gpu_count: 2
  port: 8000
  quantization: "none"
```

## Security Considerations

- All VLLM integrations require human approval
- Model access controls must be configured
- Network security must be enforced
- Resource usage monitoring is required

## Compliance Requirements

- Follow security best practices for AI platform integrations
- Maintain audit logs of all VLLM interactions
- Ensure proper resource management and monitoring
