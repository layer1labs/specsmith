# VS Code Integration for Specsmith

This document describes the integration of Specsmith with Visual Studio Code, enabling developers to work with specsmith-governed projects directly from their IDE.

## Overview

The Specsmith VS Code extension provides:
- Project initialization and configuration
- Real-time compliance checking
- Governance file navigation
- Integration with specsmith CLI commands
- Code analysis and quality reporting

## Installation

### Prerequisites
- Visual Studio Code (1.80 or later)
- Python 3.8 or later
- Specsmith installed via pipx

### Installation Steps
1. Install the Specsmith VS Code extension from the marketplace
2. Ensure specsmith is installed: `pipx install specsmith`
3. Open a specsmith-governed project in VS Code

## Features

### 1. Project Initialization
- Initialize new specsmith projects directly from VS Code
- Configure project type and governance settings

### 2. Compliance Monitoring
- Real-time compliance status display
- Highlight compliance gaps in the editor
- Quick access to compliance reports

### 3. Governance File Navigation
- Browse governance files (REQUIREMENTS.md, TESTS.md, etc.)
- Quick access to work items and requirements
- Visual representation of governance structure

### 4. CLI Integration
- Run specsmith commands directly from the command palette
- Access to audit, verify, and clean commands
- Integration with specsmith's agent system

### 5. Code Analysis
- Integration with specsmith's code quality analysis
- Cyclomatic complexity reporting
- A-range complexity compliance checking

## Extension Structure

The extension consists of:
- `package.json` - Extension metadata and configuration
- `src/extension.ts` - Main extension entry point
- `src/commands.ts` - Command implementations
- `src/compliance.ts` - Compliance checking integration
- `src/analysis.ts` - Code analysis integration

## Configuration

The extension can be configured through VS Code settings:
```json
{
    "specsmith.complianceCheckOnSave": true,
    "specsmith.codeAnalysisEnabled": true,
    "specsmith.projectRoot": "."
}
```

## Usage

### Command Palette
- `Specsmith: Initialize Project` - Create a new specsmith project
- `Specsmith: Run Audit` - Execute specsmith audit
- `Specsmith: Check Compliance` - Run compliance check
- `Specsmith: Analyze Code Quality` - Run code quality analysis
- `Specsmith: View Compliance Report` - Open compliance report in browser

### Status Bar
- Compliance status indicator
- Last audit timestamp
- Compliance gap count

## Development

To contribute to the extension:
1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Submit a pull request

## Support

For support, please file an issue on the [Specsmith GitHub repository](https://github.com/layer1labs/specsmith/issues).
