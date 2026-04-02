# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Importer — detect project structure and generate governance overlay."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from specsmith.config import Platform, ProjectConfig, ProjectType

# File extension → language mapping
_EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".rs": "rust",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "h",
    ".hpp": "hpp",
    ".cs": "csharp",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".dart": "dart",
    ".vhd": "vhdl",
    ".vhdl": "vhdl",
    ".v": "verilog",
    ".sv": "systemverilog",
    ".tf": "terraform",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".bb": "bitbake",
    ".bbappend": "bitbake",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".tex": "latex",
    ".bib": "bibtex",
    ".md": "markdown",
    ".rst": "restructuredtext",
    ".kicad_pcb": "kicad",
    ".kicad_sch": "kicad",
    ".kicad_pro": "kicad",
}

# Build system detection: file → build system name
_BUILD_SYSTEMS: dict[str, str] = {
    "pyproject.toml": "pyproject",
    "setup.py": "setuptools",
    "Cargo.toml": "cargo",
    "go.mod": "go-modules",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
    "package.json": "npm",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "meson.build": "meson",
    "bitbake": "bitbake",
    "west.yml": "west",
    "pubspec.yaml": "flutter",
    "*.csproj": "dotnet",
    "*.sln": "dotnet",
}

# Test framework detection: file/dir → framework
_TEST_INDICATORS: dict[str, str] = {
    "pytest.ini": "pytest",
    "conftest.py": "pytest",
    "tests/": "pytest",
    "test/": "generic",
    "Cargo.toml": "cargo-test",
    "jest.config.js": "jest",
    "jest.config.ts": "jest",
    "vitest.config.ts": "vitest",
    "vitest.config.js": "vitest",
}

# CI detection: path → platform
_CI_INDICATORS: dict[str, str] = {
    ".github/workflows": "github",
    ".gitlab-ci.yml": "gitlab",
    "bitbucket-pipelines.yml": "bitbucket",
    "Jenkinsfile": "jenkins",
    ".circleci": "circleci",
    ".travis.yml": "travis",
}


@dataclass
class DetectionResult:
    """Results from analyzing an existing project."""

    root: Path
    languages: dict[str, int] = field(default_factory=dict)
    primary_language: str = ""
    build_system: str = ""
    test_framework: str = ""
    vcs_platform: str = ""
    has_git: bool = False
    git_remote: str = ""
    existing_governance: list[str] = field(default_factory=list)
    existing_ci: str = ""
    inferred_type: ProjectType | None = None
    file_count: int = 0
    modules: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    # Deep analysis fields
    detected_ci_tools: dict[str, list[str]] = field(default_factory=dict)
    ci_tool_gaps: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    readme_summary: str = ""
    git_recent_commits: list[str] = field(default_factory=list)
    git_contributors: list[str] = field(default_factory=list)


def _detect_vcs_from_remote(remote_url: str) -> str:
    """Infer VCS platform from a git remote URL using proper host parsing."""
    from urllib.parse import urlparse

    # Handle SSH-style remotes: git@github.com:user/repo.git
    if remote_url.startswith("git@"):
        host = remote_url.split("@", 1)[1].split(":", 1)[0].lower()
    else:
        parsed = urlparse(remote_url)
        host = (parsed.hostname or "").lower()

    if host == "github.com":
        return "github"
    if host in ("gitlab.com",) or host.startswith("gitlab."):
        return "gitlab"
    if host in ("bitbucket.org",) or host.startswith("bitbucket."):
        return "bitbucket"
    return ""


def detect_project(root: Path) -> DetectionResult:
    """Walk an existing project and detect its structure.

    Returns a DetectionResult with inferred configuration.
    """
    result = DetectionResult(root=root)

    # Walk directory tree
    lang_counter: Counter[str] = Counter()
    all_files: list[Path] = []
    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".work",
        "build",
        "dist",
        "target",
        ".tox",
        ".eggs",
    }

    for path in root.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_file():
            all_files.append(path)
            ext = path.suffix.lower()
            lang = _EXT_LANG.get(ext)
            if lang:
                lang_counter[lang] += 1

    result.file_count = len(all_files)
    result.languages = dict(lang_counter.most_common())
    if lang_counter:
        result.primary_language = lang_counter.most_common(1)[0][0]

    # Build system — check root AND first-level subdirectories
    for indicator, system in _BUILD_SYSTEMS.items():
        if indicator.startswith("*"):
            if any(f.name.endswith(indicator[1:]) for f in all_files):
                result.build_system = system
                break
        elif (root / indicator).exists():
            result.build_system = system
            break
    if not result.build_system:
        for subdir in root.iterdir():
            if not subdir.is_dir() or subdir.name in skip_dirs or subdir.name.startswith("."):
                continue
            for indicator, system in _BUILD_SYSTEMS.items():
                if not indicator.startswith("*") and (subdir / indicator).exists():
                    result.build_system = system
                    break
            if result.build_system:
                break

    # Test framework — check root AND first-level subdirectories
    for indicator, framework in _TEST_INDICATORS.items():
        if indicator.endswith("/"):
            if (root / indicator.rstrip("/")).is_dir():
                result.test_framework = framework
                break
        elif (root / indicator).exists():
            result.test_framework = framework
            break
    if not result.test_framework:
        for subdir in root.iterdir():
            if not subdir.is_dir() or subdir.name in skip_dirs or subdir.name.startswith("."):
                continue
            for indicator, framework in _TEST_INDICATORS.items():
                if indicator.endswith("/"):
                    if (subdir / indicator.rstrip("/")).is_dir():
                        result.test_framework = framework
                        break
                elif (subdir / indicator).exists():
                    result.test_framework = framework
                    break
            if result.test_framework:
                break

    # CI detection
    for indicator, platform in _CI_INDICATORS.items():
        if (root / indicator).exists():
            result.existing_ci = platform
            result.vcs_platform = platform if platform in ("github", "gitlab", "bitbucket") else ""
            break

    # Git
    git_dir = root / ".git"
    result.has_git = git_dir.exists()
    if result.has_git:
        try:
            remote = subprocess.run(
                ["git", "-C", str(root), "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if remote.returncode == 0:
                result.git_remote = remote.stdout.strip()
                result.vcs_platform = _detect_vcs_from_remote(result.git_remote)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Existing governance
    for gov_file in (
        "AGENTS.md",
        "LEDGER.md",
        "CLAUDE.md",
        "GEMINI.md",
        "docs/REQUIREMENTS.md",
        "docs/TEST_SPEC.md",
        "docs/architecture.md",
    ):
        if (root / gov_file).exists():
            result.existing_governance.append(gov_file)

    # Detect modules (Python packages, Rust crates, Go packages, etc.)
    result.modules = _detect_modules(root, result.primary_language)

    # Detect test files
    result.test_files = _detect_test_files(root, all_files)

    # Detect entry points
    result.entry_points = _detect_entry_points(root, result.primary_language)

    # Infer project type
    result.inferred_type = _infer_type(result)

    # Deep analysis: CI tools, dependencies, README, git history
    result.detected_ci_tools = _parse_ci_tools(root)
    result.dependencies = _parse_dependencies(root)
    result.readme_summary = _extract_readme_summary(root)
    if result.has_git:
        result.git_recent_commits = _extract_git_commits(root)
        result.git_contributors = _extract_git_contributors(root)

    # CI tool gap analysis
    if result.detected_ci_tools and result.inferred_type:
        from specsmith.tools import list_tools_for_type

        expected = list_tools_for_type(result.inferred_type)
        for cmd in expected.lint[:1]:
            tool = cmd.split()[0]
            ci_all = " ".join(t for tools in result.detected_ci_tools.values() for t in tools)
            if tool not in ci_all:
                result.ci_tool_gaps.append(f"lint: {tool}")
        for cmd in expected.test[:1]:
            tool = cmd.split()[0]
            ci_all = " ".join(t for tools in result.detected_ci_tools.values() for t in tools)
            if tool not in ci_all:
                result.ci_tool_gaps.append(f"test: {tool}")
        for cmd in expected.security[:1]:
            tool = cmd.split()[0]
            ci_all = " ".join(t for tools in result.detected_ci_tools.values() for t in tools)
            if tool not in ci_all:
                result.ci_tool_gaps.append(f"security: {tool}")

    return result


def _detect_modules(root: Path, language: str) -> list[str]:
    """Detect major modules/packages in the project."""
    modules: list[str] = []
    _skip = {"tests", "test", ".git", ".venv", "venv", "node_modules", "__pycache__"}

    if language == "python":
        src = root / "src"
        if src.exists():
            for d in src.iterdir():
                if d.is_dir() and (d / "__init__.py").exists():
                    modules.append(d.name)
        else:
            for d in root.iterdir():
                if d.is_dir() and (d / "__init__.py").exists() and d.name not in _skip:
                    modules.append(d.name)
        # Also check first-level subdirs (e.g., backend/glossa_lab/)
        for subdir in root.iterdir():
            if not subdir.is_dir() or subdir.name in _skip or subdir.name.startswith("."):
                continue
            for d in subdir.iterdir():
                if (
                    d.is_dir()
                    and (d / "__init__.py").exists()
                    and d.name not in _skip
                    and d.name not in modules
                ):
                    modules.append(d.name)
    elif language == "rust":
        if (root / "src" / "lib.rs").exists():
            modules.append("lib")
        if (root / "src" / "main.rs").exists():
            modules.append("main")
    elif language == "go":
        for d in root.iterdir():
            if d.is_dir() and d.name not in ("vendor", ".git"):
                go_files = list(d.glob("*.go"))
                if go_files:
                    modules.append(d.name)
    elif language in ("javascript", "typescript"):
        src = root / "src"
        if src.exists():
            for d in src.iterdir():
                if d.is_dir():
                    modules.append(d.name)

    return sorted(modules)


def _detect_test_files(root: Path, all_files: list[Path]) -> list[str]:
    """Find test files."""
    test_patterns = ("test_", "_test.", ".test.", ".spec.", "tests/", "test/")
    tests: list[str] = []
    for f in all_files:
        rel = str(f.relative_to(root))
        if any(p in rel.lower() for p in test_patterns):
            tests.append(rel)
    return sorted(tests[:50])  # Cap at 50 for readability


def _detect_entry_points(root: Path, language: str) -> list[str]:
    """Find likely entry points."""
    entries: list[str] = []
    candidates = {
        "python": ["src/*/cli.py", "src/*/__main__.py", "manage.py", "app.py", "main.py"],
        "rust": ["src/main.rs"],
        "go": ["cmd/*/main.go", "main.go"],
        "javascript": ["src/index.js", "src/index.ts", "index.js", "server.js", "app.js"],
        "typescript": ["src/index.ts", "src/main.ts"],
    }
    for pattern in candidates.get(language, []):
        for match in root.glob(pattern):
            entries.append(str(match.relative_to(root)))
    return entries


# ---------------------------------------------------------------------------
# Deep analysis helpers
# ---------------------------------------------------------------------------

# Tool name → ToolSet category mapping for CI parsing
_TOOL_CATEGORY: dict[str, str] = {
    "ruff": "lint",
    "eslint": "lint",
    "clippy": "lint",
    "vale": "lint",
    "clang-tidy": "lint",
    "golangci-lint": "lint",
    "tflint": "lint",
    "mypy": "typecheck",
    "tsc": "typecheck",
    "cppcheck": "typecheck",
    "pytest": "test",
    "jest": "test",
    "vitest": "test",
    "cargo test": "test",
    "go test": "test",
    "ctest": "test",
    "pip-audit": "security",
    "npm audit": "security",
    "cargo audit": "security",
    "govulncheck": "security",
    "tfsec": "security",
    "checkov": "security",
}


def _parse_ci_tools(root: Path) -> dict[str, list[str]]:
    """Parse CI config files and extract tool commands by category."""
    tools: dict[str, list[str]] = {}
    ci_files: list[Path] = []

    # GitHub Actions
    wf_dir = root / ".github" / "workflows"
    if wf_dir.exists():
        ci_files.extend(wf_dir.glob("*.yml"))
        ci_files.extend(wf_dir.glob("*.yaml"))
    # GitLab
    gl = root / ".gitlab-ci.yml"
    if gl.exists():
        ci_files.append(gl)
    # Bitbucket
    bb = root / "bitbucket-pipelines.yml"
    if bb.exists():
        ci_files.append(bb)

    for ci_file in ci_files:
        try:
            content = ci_file.read_text(encoding="utf-8")
            for tool_name, category in _TOOL_CATEGORY.items():
                if tool_name in content:
                    tools.setdefault(category, [])
                    if tool_name not in tools[category]:
                        tools[category].append(tool_name)
        except Exception:  # noqa: BLE001
            continue

    return tools


def _parse_dependencies(root: Path) -> list[str]:
    """Extract dependency names from build config files."""
    deps: list[str] = []

    # Python: pyproject.toml (check root and subdirs)
    for pyproject in [root / "pyproject.toml", *root.glob("*/pyproject.toml")]:
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                # Simple extraction: lines matching '"package>=version"'
                import re

                for m in re.findall(r'"([a-zA-Z][a-zA-Z0-9_-]*)(?:[><=!]|\[)', content):
                    if m not in deps and m not in ("python",):
                        deps.append(m)
            except Exception:  # noqa: BLE001
                continue

    # Node: package.json
    for pkg_json in [root / "package.json", *root.glob("*/package.json")]:
        if pkg_json.exists():
            try:
                import json

                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                for section in ("dependencies", "devDependencies"):
                    for name in data.get(section, {}):
                        if name not in deps:
                            deps.append(name)
            except Exception:  # noqa: BLE001
                continue

    return deps[:50]  # Cap for readability


def _extract_readme_summary(root: Path) -> str:
    """Extract first heading + first paragraph from README.md."""
    readme = root / "README.md"
    if not readme.exists():
        return ""
    try:
        lines = readme.read_text(encoding="utf-8").splitlines()
        summary_parts: list[str] = []
        found_heading = False
        for line in lines:
            if line.startswith("#") and not found_heading:
                found_heading = True
                continue
            if found_heading:
                stripped = line.strip()
                if not stripped:
                    if summary_parts:
                        break
                    continue
                if stripped.startswith("#"):
                    break
                # Skip badges
                if stripped.startswith("[!") or stripped.startswith("[!["):
                    continue
                summary_parts.append(stripped)
        return " ".join(summary_parts)[:500]
    except Exception:  # noqa: BLE001
        return ""


def _extract_git_commits(root: Path) -> list[str]:
    """Get recent git commit messages."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def _extract_git_contributors(root: Path) -> list[str]:
    """Get contributor list from git history."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "shortlog", "-sn", "--no-merges", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [ln.strip() for ln in result.stdout.strip().splitlines()[:10] if ln.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def _infer_type(result: DetectionResult) -> ProjectType:
    """Infer the best ProjectType from detection results."""
    lang = result.primary_language
    build = result.build_system

    # Hardware types
    if lang in ("vhdl", "verilog", "systemverilog"):
        return ProjectType.FPGA_RTL
    if lang == "bitbake" or build == "bitbake":
        return ProjectType.YOCTO_BSP

    # Language-specific
    if lang == "rust":
        if "lib" in result.modules:
            return ProjectType.LIBRARY_RUST
        return ProjectType.CLI_RUST
    if lang == "go":
        return ProjectType.CLI_GO
    if lang in ("c", "cpp", "h", "hpp"):
        if build == "west":
            return ProjectType.EMBEDDED_HARDWARE
        if build == "cmake":
            if any("lib" in m for m in result.modules):
                return ProjectType.LIBRARY_C
            return ProjectType.CLI_C
        return ProjectType.EMBEDDED_HARDWARE
    if lang == "csharp":
        return ProjectType.DOTNET_APP
    if lang in ("dart", "swift", "kotlin"):
        return ProjectType.MOBILE_APP
    if lang == "kicad":
        return ProjectType.PCB_HARDWARE
    if lang == "terraform":
        return ProjectType.DEVOPS_IAC
    if lang == "latex":
        return ProjectType.RESEARCH_PAPER
    if lang == "protobuf":
        return ProjectType.API_SPECIFICATION
    if lang == "graphql":
        return ProjectType.API_SPECIFICATION

    # JS/TS
    if lang in ("javascript", "typescript", "jsx", "tsx"):
        if build == "npm":
            pkg = result.root / "package.json"
            if pkg.exists():
                content = pkg.read_text(encoding="utf-8")
                if "react" in content or "vue" in content or "angular" in content:
                    # Check if there's also a server
                    if (result.root / "server").exists() or "express" in content:
                        return ProjectType.FULLSTACK_JS
                    return ProjectType.WEB_FRONTEND
        return ProjectType.FULLSTACK_JS

    # Python types
    if lang == "python":
        if build in ("pyproject", "setuptools"):
            # Check for CLI entry point
            if any("cli.py" in e for e in result.entry_points):
                return ProjectType.CLI_PYTHON
            # Check for web framework
            if (result.root / "manage.py").exists():
                return ProjectType.BACKEND_FRONTEND
            return ProjectType.LIBRARY_PYTHON
        # Check for ML indicators — require strong signals, not just data/ dir
        has_notebooks = any(f.suffix == ".ipynb" for f in result.root.rglob("*.ipynb"))
        has_ml_marker = (result.root / "requirements-ml.txt").exists() or (
            (result.root / "notebooks").is_dir() and has_notebooks
        )
        if has_ml_marker:
            return ProjectType.DATA_ML
        return ProjectType.CLI_PYTHON

    return ProjectType.CLI_PYTHON  # Safe default


def generate_import_config(result: DetectionResult) -> ProjectConfig:
    """Generate a ProjectConfig from detection results."""
    return ProjectConfig(
        name=result.root.name,
        type=result.inferred_type or ProjectType.CLI_PYTHON,
        platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
        language=result.primary_language or "python",
        description=f"Imported project ({result.file_count} files detected)",
        git_init=False,  # Already has git
        vcs_platform=result.vcs_platform,
        detected_build_system=result.build_system,
        detected_test_framework=result.test_framework,
    )


def generate_overlay(
    result: DetectionResult,
    target: Path,
    *,
    force: bool = False,
) -> list[Path]:
    """Generate governance overlay files for an existing project."""
    from datetime import date

    created: list[Path] = []

    def _write(rel_path: str, content: str) -> None:
        path = target / rel_path
        if path.exists() and not force:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path)

    name = result.root.name
    lang = result.primary_language or "unknown"
    today = date.today().isoformat()
    ptype = result.inferred_type.value if result.inferred_type else "unknown"

    # AGENTS.md
    _write(
        "AGENTS.md",
        f"# {name} — Agent Governance\n\n"
        "This project was imported by specsmith. The governance files contain "
        "detected structure. Review and enrich with your agent.\n\n"
        "## Project Summary\n"
        f"- **Language**: {lang}\n"
        f"- **Build system**: {result.build_system or 'not detected'}\n"
        f"- **Test framework**: {result.test_framework or 'not detected'}\n"
        f"- **Files detected**: {result.file_count}\n"
        f"- **Modules**: {', '.join(result.modules) or 'none detected'}\n\n"
        "## Workflow Rules\n"
        "1. Read AGENTS.md fully before starting any task.\n"
        "2. Log all changes in LEDGER.md.\n"
        "3. Map changes to requirements in docs/REQUIREMENTS.md.\n"
        "4. Verify against docs/TEST_SPEC.md.\n",
    )

    # LEDGER.md
    _write(
        "LEDGER.md",
        "# Change Ledger\n\n"
        f"## {today} — specsmith import\n"
        f"- Imported project: {name}\n"
        f"- Detected type: {ptype}\n"
        f"- Language: {lang}\n"
        f"- Build system: {result.build_system}\n",
    )

    # docs/REQUIREMENTS.md
    reqs = "# Requirements\n\nRequirements auto-generated from project detection.\n\n"
    for module in result.modules:
        mu = module.upper().replace(" ", "-")
        reqs += (
            f"## REQ-{mu}-001\n"
            f"- **Component**: {module}\n"
            f"- **Status**: Draft\n"
            f"- **Description**: [Describe requirements for {module}]\n\n"
        )
    if result.build_system:
        reqs += (
            "## REQ-BUILD-001\n"
            f"- **Build system**: {result.build_system}\n"
            "- **Status**: Draft\n"
            f"- **Description**: Project builds successfully with {result.build_system}\n\n"
        )
    _write("docs/REQUIREMENTS.md", reqs)

    # docs/TEST_SPEC.md
    tests = "# Test Specification\n\nTests auto-generated from project detection.\n\n"
    for i, test_file in enumerate(result.test_files[:20], 1):
        tests += f"## TEST-{i:03d}\n- **File**: {test_file}\n- **Status**: Detected\n"
        for module in result.modules:
            if module in test_file:
                tests += f"- **Requirement**: REQ-{module.upper()}-001\n"
                break
        tests += "\n"
    _write("docs/TEST_SPEC.md", tests)

    # docs/architecture.md
    arch = (
        f"# Architecture — {name}\n\n"
        "Architecture auto-generated from project detection.\n\n"
        "## Overview\n"
        f"- **Language**: {lang}\n"
        f"- **Build system**: {result.build_system or 'not detected'}\n"
        f"- **Test framework**: {result.test_framework or 'not detected'}\n\n"
    )
    if result.modules:
        arch += "## Modules\n"
        for module in result.modules:
            arch += f"- **{module}**: [Describe module purpose]\n"
        arch += "\n"
    if result.entry_points:
        arch += "## Entry Points\n"
        for ep in result.entry_points:
            arch += f"- `{ep}`\n"
        arch += "\n"
    if result.languages:
        arch += "## Language Distribution\n"
        for lang_name, count in sorted(result.languages.items(), key=lambda x: -x[1]):
            arch += f"- {lang_name}: {count} files\n"
    _write("docs/architecture.md", arch)

    # --- Modular governance files (merge: only create if missing) ---
    _write(
        "docs/governance/rules.md",
        "# Rules\n\nH1: Never modify governance files without a proposal.\n"
        "H2: All proposals require human approval.\n"
        "H3: The ledger is append-only.\n",
    )
    _write(
        "docs/governance/workflow.md",
        "# Workflow\n\n1. Propose changes\n2. Get approval\n"
        "3. Execute\n4. Verify\n5. Record in ledger\n",
    )
    _write(
        "docs/governance/roles.md",
        "# Roles\n\n- **Human**: Approves proposals\n- **Agent**: Proposes and executes\n",
    )
    _write(
        "docs/governance/context-budget.md",
        "# Context Budget\n\nKeep governance files small. Lazy-load per task.\n",
    )
    _write(
        "docs/governance/verification.md",
        "# Verification\n\nRun verification tools before marking tasks complete.\n",
    )
    _write(
        "docs/governance/drift-metrics.md",
        "# Drift Metrics\n\nUse `specsmith audit` to check governance health.\n",
    )

    # --- CI config (merge: only create if no CI detected) ---
    if not result.existing_ci and result.vcs_platform:
        try:
            from specsmith.vcs import get_platform

            config = generate_import_config(result)
            platform = get_platform(result.vcs_platform)
            ci_files = platform.generate_all(config, target)
            created.extend(ci_files)
        except (ValueError, Exception):  # noqa: BLE001
            pass  # Best-effort

    return created
