# Specsmith VS Code Extension

This extension provides integration between Visual Studio Code and Specsmith, enabling developers to work with specsmith-governed projects directly from their IDE.

## Features

- **Project Initialization**: Create new specsmith projects with proper governance structure
- **Compliance Monitoring**: Real-time compliance status in the editor
- **Governance File Navigation**: Easy access to governance files and requirements
- **CLI Integration**: Run specsmith commands directly from VS Code
- **Code Analysis**: Integration with specsmith's code quality analysis tools

## Installation

1. Install the extension from the VS Code marketplace
2. Ensure specsmith is installed: `pipx install specsmith`
3. Open a specsmith-governed project in VS Code

## Commands

- `Specsmith: Initialize Project` - Create a new specsmith project
- `Specsmith: Run Audit` - Execute specsmith audit
- `Specsmith: Check Compliance` - Run compliance check
- `Specsmith: Analyze Code Quality` - Run code quality analysis
- `Specsmith: View Compliance Report` - Open compliance report

## Configuration

The extension can be configured through VS Code settings:

```json
{
    "specsmith.complianceCheckOnSave": true,
    "specsmith.codeAnalysisEnabled": true,
    "specsmith.projectRoot": "."
}
```

## Development

To build and test the extension:

1. Install dependencies: `npm install`
2. Compile: `npm run compile`
3. Run in VS Code: `F5`

## License

MIT
