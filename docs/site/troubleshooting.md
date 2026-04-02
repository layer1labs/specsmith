# Troubleshooting

## Installation Issues

### `pip install specsmith` finds no package
Check your Python version (requires 3.10+) and that pip is up to date: `pip install --upgrade pip`.

### `python -m specsmith` gives "No module named specsmith.__main__"
Update to the latest version: `pip install --upgrade specsmith`.

## Import Issues

### Import detects the wrong project type
Override during import — when prompted "Proceed with these settings?" answer `n`, then select the correct type from the list. Or override language: you'll be prompted for it.

### Import doesn't detect my build system
Currently detected: pyproject.toml, Cargo.toml, go.mod, package.json, CMakeLists.txt, west.yml, build.gradle.kts, pubspec.yaml, *.csproj, Makefile. If yours isn't listed, [file an issue](https://github.com/BitConcepts/specsmith/issues/new?template=feature_request.md).

### Import overwrote my AGENTS.md
Without `--force`, import never overwrites existing files. If you used `--force`, that's the intended behavior. Re-create your AGENTS.md or restore from git.

## Audit Issues

### "REQ(s) without test coverage"
Your REQUIREMENTS.md has requirement IDs (e.g., `REQ-CLI-001`) that don't appear in any `Covers:` line in TEST_SPEC.md. Add `Covers: REQ-CLI-001` references to your test entries.

### "CI config missing expected tools"
Your CI config doesn't reference the tools expected for your project type. Run `specsmith audit --fix` to regenerate CI from the tool registry, or manually add the missing tools.

## CI Issues

### Generated CI fails: tool not found
The CI config assumes tools are installed in the CI environment. For example, `ruff` needs `pip install ruff` in the CI step. Check that the setup step installs the tool. specsmith generates these install steps, but if you've modified the CI, they may be missing.

### Dependabot config has wrong ecosystem
The ecosystem is inferred from `language` in scaffold.yml, not from the project type. If your config says `language: python` but you need `npm`, update the language field.

## Doctor Issues

### "No scaffold.yml found"
Doctor requires scaffold.yml. Run `specsmith import --project-dir .` to generate one, or create it manually.

### Tool shows as "not found" but it's installed
Doctor checks `shutil.which()` — the tool must be on your PATH. Virtual environments, conda environments, or tools installed in non-standard locations may not be found. Activate your environment first.

## Template Issues

### "'tools' is undefined" error in diff/upgrade
Upgrade to the latest version: `pip install --upgrade specsmith`.

## General

### How do I start over with governance?
```bash
specsmith import --project-dir . --force
```
This regenerates all governance files from detection, overwriting existing ones.

### How do I see what specsmith would generate without creating files?
There's no dry-run mode yet. Use a temporary directory:
```bash
mkdir /tmp/test && specsmith init --config scaffold.yml --output-dir /tmp/test --no-git
```
