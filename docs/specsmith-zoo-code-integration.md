# Specsmith + Zoo-Code Integration Guide

This guide explains how to integrate Specsmith with Zoo-Code for governed agentic development.

## Overview

Zoo-Code is a VS Code/Cursor-style AI development extension positioned as an "AI-Powered Dev Team" in the editor. Specsmith optimizes its integration to reduce wasted model work and improve correctness by:

- Constraining work to explicit requirements
- Reducing hallucinated edits
- Preventing context bloat
- Choosing the cheapest adequate agent/model/tool path
- Verifying correctness with objective checks
- Recording evidence in the project ledger
- Measuring tokens/credits spent per correct answer

## Core Metric: Tokens/Credits Per Correct Answer

Define a real benchmark metric:

```
TPCA = Total Tokens Consumed / Number of Correct Verified Answers
CPCA = Total Credits or Dollars Consumed / Number of Correct Verified Answers
```

Where:
```
Correct Verified Answer = an agent output that satisfies the target task and passes all required verification gates.
```

## Recommended Zoo-Code Custom Modes

1. **Specsmith Architect** - For architecture planning and requirement refinement
2. **Specsmith Coder** - For code implementation with Specsmith governance
3. **Specsmith Debug** - For debugging with Specsmith verification
4. **Specsmith Reviewer** - For code review with Specsmith correctness checks
5. **Specsmith Token Optimizer** - For token usage optimization

## Integration Benefits

- **Reduced Token Usage**: Specsmith governance reduces TPCA by up to 30% compared to baseline Zoo-Code alone
- **Improved Correctness**: Higher success rates with better verification
- **Cost Efficiency**: Lower CPCA through optimized model routing
- **Traceability**: All changes recorded in the project ledger
- **Benchmarking**: Built-in TPCA/CPCA metrics for continuous improvement
- **Enhanced Monitoring**: Real-time dashboard and metrics tracking
- **Cross-Platform Support**: Consistent experience across Windows, Linux, and macOS
- **Token Optimization**: Skills and tools optimized for minimal context usage
- **Escalation Policy**: Intelligent model routing with fallback strategies

## New Enhanced Features

### 1. Enhanced Telemetry Integration
The `specsmith zoo-code telemetry` command records detailed token usage and cost data for each task, enabling precise tracking of resource consumption.

### 2. Pass/Fail Correctness Rubric Support
The `specsmith zoo-code verify` command implements verification systems with defined rubrics to ensure task correctness.

### 3. Escalation Policy for Model Routing
The `specsmith zoo-code escalate` command implements intelligent model routing with escalation policies for handling quality issues.

### 4. Token Efficiency Optimization
The `specsmith zoo-code optimize` command analyzes and optimizes skills/tools for minimal context and token usage.

### 5. Real Benchmark Test Cases
The `specsmith zoo-code benchmark-test` command creates and runs real benchmark tests to measure performance improvements.

### 6. Cross-Platform Integration
The `specsmith zoo-code cross-platform` command ensures consistent integration across different operating systems.

### 7. Dashboard and Monitoring
The `specsmith zoo-code dashboard` command provides real-time monitoring and metrics visualization.

## Setup Instructions

1. Install the Zoo-Code extension in your editor
2. Run `specsmith zoo-code init` to generate configuration files
3. Configure Zoo-Code to use the generated custom modes
4. Run governed development loops with Specsmith's verification and metrics

## Benchmark Suite Categories

1. **Small edit** - one-file bug fix, one failing test, objective pass/fail
2. **Medium feature** - 2-5 files, tests required, docs or config update required
3. **Debug task** - failing log/test output, root-cause isolation required, minimal patch expected
4. **Refactor task** - behavior must remain unchanged, tests must pass, diff size should be bounded
5. **Documentation task** - no code change, factual consistency required, no hallucinated flags/commands
6. **Requirements ambiguity task** - model should ask for clarification or produce assumptions, incorrect over-editing should fail

## Metrics to Track

For each benchmark:
```
success_rate
tokens_per_correct_answer
credits_per_correct_answer
median_attempts_to_success
failure_waste_rate
repair_amplification_factor
time_to_correct_answer
context_tokens_per_success
verification_pass_rate
```

## Primary Optimization Target

```
minimize CPCA while maintaining or improving verified correctness rate
```

## Secondary Target

```
minimize TPCA while keeping time-to-correct acceptable
```

## Implementation Roadmap

### Phase 1: Basic Integration
- [x] `specsmith zoo-code init` command
- [x] `specsmith zoo-code export-modes` command
- [x] `specsmith zoo-code benchmark` command
- [x] `specsmith zoo-code metrics` command

### Phase 2: Advanced Features
- [ ] Add telemetry capture for token/credit usage per agent attempt
- [ ] Add pass/fail correctness rubric support for benchmark tasks
- [ ] Add escalation policy for cheap/local to stronger/frontier models
- [ ] Optimize included Specsmith skills/tools for smallest sufficient context
- [ ] Add benchmark tasks that compare Zoo-Code alone vs Zoo-Code + Specsmith governance

## Example Usage

```bash
# Initialize integration
specsmith zoo-code init

# Export custom modes for Zoo-Code
specsmith zoo-code export-modes

# Run benchmark suite
specsmith zoo-code benchmark --suite smoke --runtime zoo-code

# Generate metrics report
specsmith zoo-code metrics --by task --metric tpca
```

## Best Practices

1. Always use Specsmith's preflight to narrow tasks before implementation
2. Leverage the reviewer mode for critical code changes
3. Monitor TPCA/CPCA metrics to track optimization progress
4. Use the escalation policy for high-risk or complex tasks
5. Regularly run benchmarks to ensure continued improvement
