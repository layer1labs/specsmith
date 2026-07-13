# SKILL.md
# Local AI Governed Profile

## Requirements Covered

### Governance Requirements
- REQ-012: Least-Privilege Agent Permissions
- REQ-217: Agent Permissions Check
- REQ-220: Policy Guardrails
- REQ-244: Context Window Sizing
- REQ-245: Live Context Fill Indicator
- REQ-246: Auto Context Compression
- REQ-247: Hard Context Ceiling

## Core Principle
The local-ai-governed profile is designed for agents operating with local AI models and tools. It ensures compliance with Specsmith governance while managing the unique constraints and capabilities of local AI environments.

## Profile Characteristics

### Required Skills
- preflight-gate
- governed-agent-loop
- requirement-author
- testcase-author
- traceability-auditor
- context-pack-compiler
- token-budget-auditor
- skill-composer
- webui-integration
- vllm-integration
- lmstudio-integration
- ollama-integration
- openterminal-integration

### Environment-Specific Features
- Local AI model integration capabilities
- Context window optimization for local AI constraints
- Compliance with local AI environment policies
- Integration with various local AI platforms

## Implementation Details

### Local AI-Specific Execution
1. Leverage local AI model capabilities for code generation and analysis
2. Optimize context windows to fit local AI constraints
3. Apply Specsmith governance rules within local AI environments
4. Maintain traceability between local AI actions and Specsmith requirements

### Context Management
- Optimize context for local AI model limitations
- Apply local AI-specific compression techniques
- Ensure context fits within local AI constraints while maintaining traceability
- Track local AI usage and performance metrics

## Configuration

### Default Behavior
By default, the local-ai-governed profile:
- Integrates with various local AI platforms (WebUI, VLLM, LMStudio, Ollama, OpenTerminal)
- Optimizes context for local AI model constraints
- Maintains full Specsmith governance compliance
- Tracks local AI usage metrics

### Override Options
- Allow local AI-specific skill overrides
- Support local AI environment customization
- Enable local AI-specific context optimization

## Security Considerations
- All local AI actions must pass preflight validation
- Local AI skill compositions must be traceable
- Local AI environment compliance must be maintained
- Local AI usage must be tracked and audited

## Compliance Requirements
- Every local AI action must be traceable to a valid work item or requirement
- Local AI integration must comply with local environment policies
- All skill compositions must follow Specsmith governance
- Local AI usage must be reported and audited
