# Governance Plugin API
Plugin manifest file: `specsmith.plugin.yml`.
Supported plugin types:
- `verifier`
- `requirement_importer`
- `test_linker`
- `compliance_mapper`
- `agent_adapter`
- `policy_rule`
- `exporter`
Commands:
```bash
specsmith plugin list
specsmith plugin validate examples/plugins/example-verifier/specsmith.plugin.yml
```
Security notes:
- Keep plugin code in trusted repositories.
- Validate plugin manifests before loading.
- Pin plugin versions and minimum `specsmith_version`.
