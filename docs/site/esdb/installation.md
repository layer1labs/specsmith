# ESDB — Installation

## License

The chronomemory ESDB engine is **proprietary software** — a commercial license is required.
Contact [licensing@layer1labs.ai](mailto:licensing@layer1labs.ai).
Terms: [COMMERCIAL-LICENSE.md (ChronoMemory only)](https://github.com/layer1labs/specsmith/blob/develop/COMMERCIAL-LICENSE.md).

If you use specsmith, the simplest path is `pip install "specsmith[esdb]"`.
See the [ESDB overview](../esdb.md#licensing) for the full two-tier licensing summary.

---

## Requirements

- Python **3.10** or later
- No external runtime dependencies

---

## Install via specsmith (recommended)

```bash
# Via pip:
pip install "specsmith[esdb]"

# Via pipx (if specsmith is pipx-managed):
pipx inject specsmith "chronomemory>=0.2.4"
```

Activate your license key:

```bash
specsmith esdb enable --key-file /path/to/your.esdb.key
specsmith esdb status   # confirms ChronoStore is active
```

## Install standalone (without specsmith)

```bash
pip install chronomemory
```

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "chronomemory>=0.2.4",
]
```

**Zero runtime dependencies** — pure Python stdlib (`hashlib`, `json`, `os`, `shutil`, `pathlib`).

---

## Verify installation

```python
import chronomemory
print(chronomemory.__version__)   # 0.2.4

from chronomemory import ChronoStore, ChronoRecord, EsdbBridge
print("OK")
```

Or from the command line:

```bash
python -c "import chronomemory; print(chronomemory.__version__)"
```

---

## Install documentation dependencies

```bash
pip install "chronomemory[docs]"
mkdocs serve   # preview at http://localhost:8000
```

---

## Dependency policy

`chronomemory` has **zero runtime dependencies**. It uses only Python stdlib:
`hashlib`, `json`, `os`, `shutil`, `pathlib`, `dataclasses`, `typing`.

This is enforced by CI: the package is installed with `--no-deps` and the
`dependencies` field is asserted empty.

---

## Platform support

| Platform | Status |
|----------|--------|
| Linux (Ubuntu 22.04+) | ✅ CI tested |
| macOS (12+) | ✅ Supported |
| Windows (Server 2019+) | ✅ CI tested |
