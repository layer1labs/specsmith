# Context Budget Management

This document defines how context windows are managed within the specsmith governance framework.

## Context Window Policies

### GPU-Aware Context Sizing
- Context windows are sized based on available GPU memory
- When no GPU is detected, fallback to CPU-safe defaults
- VRAM-aware model recommendations are provided

### Context Budget Allocation
- Each session maintains a context budget
- Context usage is tracked and reported
- Context compression is applied when necessary
- Hard context ceiling prevents 100% full contexts

## Context Management Rules

1. **Context Awareness**: All agents must be aware of their context window limitations
2. **Budget Tracking**: Context usage is tracked throughout the session
3. **Compression**: Automatic context compression when approaching limits
4. **Fallback**: Safe fallback strategies when context is exceeded

## Context Window Management

### Live Context Fill Indicator
- Real-time indicator of context usage
- Warning when approaching limits
- Automatic compression when necessary

### Auto Context Compression
- Intelligent compression of context when needed
- Preservation of critical information
- Maintains effectiveness while reducing size

### Hard Context Ceiling
- Never allow context to reach 100% full
- Maintain buffer for new information
- Prevent overflow conditions
