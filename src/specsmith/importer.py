# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Importer — detect project structure and generate governance overlay."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from specsmith.config import Platform, ProjectConfig, ProjectType
from specsmith.languages import EXT_LANG as _EXT_LANG
from specsmith.languages import FILENAME_LANG as _FILENAME_LANG

# FPGA build / project file indicators — used for type inference
_FPGA_INDICATORS: dict[str, str] = {
    "*.xpr": "amd",  # Vivado project (AMD Adaptive Computing)
    "*.xdc": "amd",  # Vivado/AMD constraints
    "*.bit": "amd",  # AMD/Vivado bitstream
    "*.xsa": "amd",  # Vivado exported hardware
    "*.qpf": "intel",  # Quartus project
    "*.qsf": "intel",  # Quartus settings
    "*.qxp": "intel",
    "*.ldf": "lattice",  # Lattice Diamond project
    "*.pdc": "lattice",  # Lattice constraints
    "Makefile": "generic",  # Yosys+nextpnr makefiles often at root
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
    "kas.yml": "kas",
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
    secondary_languages: list[str] = field(default_factory=list)
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
        ".specsmith",
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
            lang = _EXT_LANG.get(ext) or _FILENAME_LANG.get(path.name)
            if lang:
                lang_counter[lang] += 1

    # Config/data/markup formats are common across all projects and
    # should not count as a project's primary programming language.
    _LANG_NOISE = {
        "yaml",
        "toml",
        "json",
        "xml",
        "markdown",
        "html",
        "css",
        "bibtex",
        "cmake",
        "dockerfile",
        "makefile",
        "restructuredtext",
        "asciidoc",
        "latex",
        "graphql",
        "protobuf",
    }

    result.file_count = len(all_files)
    result.languages = dict(lang_counter.most_common())

    # Primary language: first non-noise language in frequency order
    if lang_counter:
        for lang, _count in lang_counter.most_common():
            if lang not in _LANG_NOISE:
                result.primary_language = lang
                break
        if not result.primary_language:  # all langs are noise — use top anyway
            result.primary_language = lang_counter.most_common(1)[0][0]

        # Secondary languages: all others above a minimum threshold (5 files or 5%)
        total = sum(lang_counter.values())
        threshold = max(5, int(total * 0.05))
        result.secondary_languages = [
            lang
            for lang, count in lang_counter.most_common()
            if lang != result.primary_language and count >= threshold and lang not in _LANG_NOISE
        ]

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
        "docs/ARCHITECTURE.md",
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

    # FPGA vendor detection — check for vendor project/constraint file extensions
    if result.primary_language in ("vhdl", "verilog", "systemverilog"):
        for indicator, vendor in _FPGA_INDICATORS.items():
            if indicator.startswith("*") and any(f.name.endswith(indicator[1:]) for f in all_files):
                result.inferred_type = _fpga_type_for_vendor(vendor)
                break

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


def _fpga_type_for_vendor(vendor: str) -> ProjectType:
    """Return the appropriate ProjectType for an FPGA vendor string."""
    from specsmith.config import ProjectType

    mapping = {
        "amd": ProjectType.FPGA_RTL_AMD,
        "xilinx": ProjectType.FPGA_RTL_AMD,  # legacy alias (AMD acquired Xilinx)
        "intel": ProjectType.FPGA_RTL_INTEL,
        "lattice": ProjectType.FPGA_RTL_LATTICE,
    }
    return mapping.get(vendor, ProjectType.FPGA_RTL)


def suggest_name(root: Path) -> str:
    """Suggest a project name from multiple sources (priority order).

    1. pyproject.toml ``[project] name``
    2. package.json ``name``
    3. Cargo.toml ``[package] name``
    4. go.mod first ``module`` path basename
    5. Current git ``remote origin`` repo name
    6. Directory name (last resort)
    """
    import re

    # pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8")
            m = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
            if m:
                return m.group(1)
        except OSError:
            pass

    # package.json
    pkg = root / "package.json"
    if pkg.exists():
        try:
            import json

            data = json.loads(pkg.read_text(encoding="utf-8"))
            name = data.get("name", "")
            if name and not name.startswith("@"):
                return name
            if name.startswith("@"):  # scoped package — use basename
                return name.split("/")[-1]
        except (OSError, ValueError):
            pass

    # Cargo.toml
    cargo = root / "Cargo.toml"
    if cargo.exists():
        try:
            text = cargo.read_text(encoding="utf-8")
            m = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
            if m:
                return m.group(1)
        except OSError:
            pass

    # go.mod
    gomod = root / "go.mod"
    if gomod.exists():
        try:
            text = gomod.read_text(encoding="utf-8")
            m = re.search(r"^module\s+(\S+)", text, re.MULTILINE)
            if m:
                return m.group(1).rstrip("/").split("/")[-1]
        except OSError:
            pass

    # git remote repo name
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode == 0 and r.stdout.strip():
            url = r.stdout.strip()
            basename = url.rstrip("/").split("/")[-1]
            return basename.removesuffix(".git")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return root.name


def suggest_type(result: DetectionResult) -> str:
    """Return the best-fit project type key for a DetectionResult.

    Returns a string matching a ``ProjectType`` value (e.g. 'cli-python').
    """
    from specsmith.config import ProjectType

    if result.inferred_type:
        return result.inferred_type.value
    lang = result.primary_language
    build = result.build_system
    mapping: dict[str, str] = {
        "python": "cli-python",
        "rust": "cli-rust",
        "go": "cli-go",
        "c": "cli-c",
        "cpp": "cli-c",
        "csharp": "dotnet-app",
        "typescript": "fullstack-js",
        "javascript": "web-frontend",
        "dart": "mobile-app",
        "swift": "mobile-app",
        "kotlin": "mobile-app",
        "vhdl": ProjectType.FPGA_RTL.value,
        "verilog": ProjectType.FPGA_RTL.value,
        "systemverilog": ProjectType.FPGA_RTL.value,
        "bitbake": ProjectType.YOCTO_BSP.value,
        "terraform": "devops-iac",
        "latex": "research-paper",
    }
    if build in ("pyproject", "setuptools") and lang == "python":
        return "library-python" if (result.root / "src").exists() else "cli-python"
    if build == "flutter":
        return "mobile-app"
    return mapping.get(lang, "cli-python")


def suggest_auxiliary(result: DetectionResult) -> list[str]:
    """Suggest auxiliary disciplines for a mixed-language project."""
    primary = suggest_type(result)
    all_langs = set(result.languages.keys())
    all_langs.discard(result.primary_language)
    # Remove doc/config/markup languages — they don't constitute a discipline
    noise = {"markdown", "yaml", "toml", "json", "xml", "bibtex", "makefile", "cmake"}
    all_langs -= noise

    aux: list[str] = []
    lang_to_aux: dict[str, str] = {
        "python": "cli-python",
        "c": "embedded-c",
        "cpp": "embedded-hardware",
        "rust": "cli-rust",
        "typescript": "web-frontend",
        "javascript": "web-frontend",
        "bitbake": "yocto-bsp",
        "devicetree": "embedded-hardware",
        "terraform": "devops-iac",
    }
    for lang in all_langs:
        disc = lang_to_aux.get(lang)
        if disc and disc != primary and disc not in aux:
            aux.append(disc)
    return aux


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


# Section heading keywords → governance file mapping.
# Each list is checked with substring matching against lowercased ## headings.
_RULES_KW: list[str] = [
    "hard rule",
    "stop condition",
    "acceptance",
    "forbidden",
    "mandatory",
    "pre-flight",
    "preflight",
    "critical rule",
    "tool invocation",
    "prohibition",
    "enforcement",
    "final rule",
    "phase enforcement",
    "phase 1",
    "phase 2",
    "repository structure",
    ".work/",
    ".work",
    "path-length",
    "directory structure",
]
_WORKFLOW_KW: list[str] = [
    "session",
    "lifecycle",
    "quick command",
    "ledger",
    "new session",
    "resume session",
    "save session",
    "git commit",
    "git update",
    "startup checklist",
    "stop / save",
    "stop/save",
    "push-to-git",
    "push to git",
    "command handling",
    "roadmap",
]
_ROLES_KW: list[str] = [
    "agent role",
    "drafting",
    "agents are",
    "drafting assistance",
]
_CTX_KW: list[str] = [
    "context",
    "window",
    "budget",
    "context window",
    "token",
]
_VERIFY_KW: list[str] = [
    "verification",
    "conflict",
    "consistency",
    "solver",
    "engine mode",
    "benchmark",
    "deployment",
    "connectivity",
    "target",
]
_DRIFT_KW: list[str] = [
    "environment",
    "platform",
    "shell wrapper",
    "bootstrap",
    "scripts",
]


def _clean_diff_markers(text: str) -> str:
    """Strip git diff/merge conflict artifacts from text.

    Removes leading |-, |+, || prefixes and <<<<<<< / >>>>>>> markers.
    """
    import re

    cleaned_lines: list[str] = []
    skip_block = False
    for line in text.splitlines():
        # Skip merge conflict markers entirely
        if line.startswith(("<<<<<<", ">>>>>>", "======")):
            skip_block = not skip_block if line.startswith("<<<<<<") else skip_block
            if line.startswith(">>>>>>>"):
                skip_block = False
            continue
        if skip_block:
            continue
        # Strip diff marker prefixes: |-, |+, ||, leading +, leading -
        stripped = re.sub(r"^\|{1,2}[-+]\s?", "", line)
        stripped = re.sub(r"^[-+]\s(?=[A-Z])", "", stripped)  # +/- before prose
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)


def _detect_content_issues(text: str) -> list[str]:
    """Detect quality issues in source text. Returns list of warnings."""
    import re

    warnings: list[str] = []
    lines = text.splitlines()
    diff_marker_count = 0
    for i, line in enumerate(lines, 1):
        # Diff markers
        if re.match(r"^\|{1,2}[-+]", line):
            diff_marker_count += 1
        # Merge conflict markers
        if line.startswith(("<<<<<<", ">>>>>>")):
            warnings.append(f"  Line {i}: unresolved merge conflict marker")
    if diff_marker_count > 0:
        warnings.append(
            f"  {diff_marker_count} line(s) with git diff markers (|-, |+) — auto-stripped"
        )
    return warnings


def _deduplicate_paragraphs(text: str) -> str:
    """Remove duplicate paragraphs within a text block."""
    paragraphs = text.split("\n\n")
    seen: set[str] = set()
    unique: list[str] = []
    for para in paragraphs:
        normalized = para.strip()
        if not normalized:
            continue
        # Use first 200 chars as dedup key (handles minor formatting diffs)
        key = normalized[:200].lower()
        if key not in seen:
            seen.add(key)
            unique.append(para)
    return "\n\n".join(unique)


def _extract_governance_sections(root: Path) -> dict[str, str]:
    """Extract modular governance content from existing AGENTS.md.

    If AGENTS.md exists and is large, extract sections into modular files.
    Unmatched sections are collected into rules.md so nothing is lost.
    Diff markers are stripped and duplicate paragraphs are removed.
    """
    defaults = {
        "rules": (
            "# Rules\n\n"
            "H1: Never modify governance files without a proposal.\n"
            "H2: All proposals require human approval.\n"
            "H3: The ledger is append-only.\n"
        ),
        "session-protocol": (
            "# Session Protocol\n\n"
            "1. Propose changes\n2. Get approval\n"
            "3. Execute\n4. Verify\n5. Record in ledger\n"
        ),
        "roles": (
            "# Roles\n\n- **Human**: Approves proposals\n- **Agent**: Proposes and executes\n"
        ),
        "context-budget": (
            "# Context Budget\n\nKeep governance files small. Lazy-load per task.\n"
        ),
        "verification": (
            "# Verification\n\nRun verification tools before marking tasks complete.\n"
        ),
        "drift-metrics": ("# Drift Metrics\n\nUse `specsmith audit` to check governance health.\n"),
    }

    agents_path = root / "AGENTS.md"
    if not agents_path.exists():
        return defaults

    raw_content = agents_path.read_text(encoding="utf-8")
    if len(raw_content.splitlines()) < 50:
        return defaults  # Too short to extract from

    # P0: Detect and report content issues, then clean diff markers
    issues = _detect_content_issues(raw_content)
    if issues:
        import sys

        print("\n[specsmith] Content quality warnings in AGENTS.md:", file=sys.stderr)  # noqa: T201
        for w in issues:
            print(w, file=sys.stderr)  # noqa: T201

    content = _clean_diff_markers(raw_content)

    # Parse AGENTS.md into sections by ## headings
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_heading and current_lines:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_heading and current_lines:
        sections[current_heading] = "\n".join(current_lines).strip()

    if not sections:
        return defaults

    # Classify each section into a governance category
    category_map: list[tuple[str, list[str]]] = [
        ("rules", _RULES_KW),
        ("session-protocol", _WORKFLOW_KW),
        ("roles", _ROLES_KW),
        ("context-budget", _CTX_KW),
        ("verification", _VERIFY_KW),
        ("drift-metrics", _DRIFT_KW),
    ]

    buckets: dict[str, list[tuple[str, str]]] = {
        "rules": [],
        "session-protocol": [],
        "roles": [],
        "context-budget": [],
        "verification": [],
        "drift-metrics": [],
    }
    unmatched: list[tuple[str, str]] = []

    # Body-level content keywords for secondary classification.
    # Used when heading doesn't match — scan body text for strong signals.
    _BODY_ARCHITECTURE_KW = [
        "register map",
        "address offset",
        "0x0",
        "register name",
        "block diagram",
        "data flow",
        "interface spec",
        "directory layout",
        "src/",
        "repository structure",
        "milestone",
        "roadmap",
        "completion",
        "phase 2 target",
    ]
    _BODY_DRIFT_KW = [
        "subst v:",
        "path-length",
        "one-time setup",
        "per-machine",
        "environment variable",
        "install once",
        "bootstrap",
        "windows path",
        "ntfs",
    ]

    for heading, body in sections.items():
        key_lower = heading.lower()
        matched = False
        for category, keywords in category_map:
            if any(kw in key_lower for kw in keywords):
                buckets[category].append((heading, body))
                matched = True
                break  # First match wins
        if not matched:
            # Secondary pass: scan body content for strong topic signals
            body_lower = body[:2000].lower()  # Cap scan for performance
            if any(kw in body_lower for kw in _BODY_ARCHITECTURE_KW):
                buckets["verification"].append((heading, body))  # technical reference
            elif any(kw in body_lower for kw in _BODY_DRIFT_KW):
                buckets["drift-metrics"].append((heading, body))
            else:
                unmatched.append((heading, body))

    # Unmatched sections go to rules.md as project-specific rules
    if unmatched:
        buckets["rules"].extend(unmatched)

    # Build output
    titles = {
        "rules": "# Rules",
        "session-protocol": "# Session Protocol",
        "roles": "# Roles",
        "context-budget": "# Context Budget",
        "verification": "# Verification",
        "drift-metrics": "# Environment & Platform",
    }
    result = dict(defaults)
    for category, items in buckets.items():
        if not items:
            continue
        parts: list[str] = [titles[category] + "\n"]
        for heading, body in items:
            parts.append(f"## {heading}\n")
            parts.append(body)
            parts.append("")
        # P1: Deduplicate paragraphs within each governance file
        result[category] = _deduplicate_paragraphs("\n".join(parts)) + "\n"

    return result


def _infer_type(result: DetectionResult) -> ProjectType:
    """Infer the best ProjectType from detection results."""
    lang = result.primary_language
    build = result.build_system

    # Hardware types
    if lang in ("vhdl", "verilog", "systemverilog"):
        return ProjectType.FPGA_RTL
    if lang == "bitbake" or build in ("bitbake", "kas"):
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
    # Prefer README summary; fall back to generic description
    description = (
        result.readme_summary[:120]
        if result.readme_summary
        else f"Imported {result.primary_language or 'project'} library"
    )
    # Write the installed specsmith version as spec_version so the generated
    # scaffold.yml immediately matches the tool and the auto-update prompt
    # never fires unnecessarily on first use.
    try:
        from specsmith import __version__ as _installed_ver

        spec_version = _installed_ver
    except Exception:  # noqa: BLE001
        spec_version = "0.3.0"  # safe fallback
    return ProjectConfig(
        name=result.root.name,
        type=result.inferred_type or ProjectType.CLI_PYTHON,
        platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
        language=result.primary_language or "python",
        spec_version=spec_version,
        description=description,
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
    all_langs = [lang] + (result.secondary_languages or [])
    lang_display = ", ".join(all_langs) if len(all_langs) > 1 else lang
    today = date.today().isoformat()
    ptype = result.inferred_type.value if result.inferred_type else "unknown"

    # AGENTS.md
    _write(
        "AGENTS.md",
        f"# {name} — Agent Governance\n\n"
        "This project was imported by specsmith. The governance files contain "
        "detected structure. Review and enrich with your agent.\n\n"
        "## Project Summary\n"
        f"- **Languages**: {lang_display}\n"
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

    # docs/REQUIREMENTS.md — skip if project already has one (anywhere under docs/)
    existing_reqs = list(target.glob("docs/**/REQUIREMENTS*")) + list(
        target.glob("docs/**/requirements*")
    )
    if not (existing_reqs and not force):
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

    # docs/TEST_SPEC.md — skip if project already has one
    existing_tests = list(target.glob("docs/**/TEST_SPEC*")) + list(
        target.glob("docs/**/test_spec*")
    )
    if not (existing_tests and not force):
        tests = "# Test Specification\n\nTests auto-generated from project detection.\n\n"
        for i, test_file in enumerate(result.test_files[:20], 1):
            tests += f"## TEST-{i:03d}\n- **File**: {test_file}\n- **Status**: Detected\n"
            for module in result.modules:
                if module in test_file:
                    # Use 'Covers:' — matches the audit's _TEST_COVERS_PATTERN
                    tests += f"  Covers: REQ-{module.upper().replace('-', '_')}-001\n"
                    break
            tests += "\n"
        # Add an explicit build test so REQ-BUILD-001 has coverage
        if result.build_system:
            n = len(result.test_files[:20]) + 1
            tests += (
                f"## TEST-{n:03d}\n"
                "- **Type**: integration\n"
                f"- **Description**: Project installs and {result.test_framework or 'runs'} successfully\n"  # noqa: E501
                "  Covers: REQ-BUILD-001\n"
                "- **Status**: Detected\n\n"
            )
        _write("docs/TEST_SPEC.md", tests)

    # docs/architecture.md — skip if project has architecture doc anywhere under docs/
    existing_arch = list(target.glob("docs/**/ARCHITECTURE*")) + list(
        target.glob("docs/**/architecture*")
    )
    if not (existing_arch and not force):
        arch = (
            f"# Architecture \u2014 {name}\n\n"
            "Architecture auto-generated from project detection.\n\n"
            "## Overview\n"
            f"- **Languages**: {lang_display}\n"
            f"- **Build system**: {result.build_system or 'not detected'}\n"
            f"- **Test framework**: {result.test_framework or 'not detected'}\n\n"
        )
        if result.modules:
            arch += "## Modules\n"
            for module in result.modules:
                mu = module.upper().replace("-", "_")
                # Reference the auto-generated requirement so validate passes
                arch += f"- **{module}**: [Describe module purpose] (see REQ-{mu}-001)\n"
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
        if result.build_system:
            arch += "\n## Build\n"
            arch += f"- Build system: {result.build_system} (see REQ-BUILD-001)\n"
        _write("docs/ARCHITECTURE.md", arch)

    # --- Modular governance files ---
    # If AGENTS.md exists and is rich, extract sections from it.
    # Otherwise use generic stubs.
    gov = _extract_governance_sections(target)
    _write("docs/governance/RULES.md", gov["rules"])
    _write("docs/governance/SESSION-PROTOCOL.md", gov["session-protocol"])
    _write(
        "docs/governance/LIFECYCLE.md",
        "# Project Lifecycle\n\n"
        "See `specsmith phase show` for current phase readiness.\n"
        "See `specsmith phase list` for the full AEE lifecycle.\n",
    )
    _write("docs/governance/ROLES.md", gov["roles"])
    _write("docs/governance/CONTEXT-BUDGET.md", gov["context-budget"])
    _write("docs/governance/VERIFICATION.md", gov["verification"])
    _write("docs/governance/DRIFT-METRICS.md", gov["drift-metrics"])

    # Migrate old WORKFLOW.md files if found
    import shutil as _shutil

    old_gov_wf = target / "docs" / "governance" / "WORKFLOW.md"
    new_sp = target / "docs" / "governance" / "SESSION-PROTOCOL.md"
    if old_gov_wf.exists() and not new_sp.exists():
        _shutil.move(str(old_gov_wf), str(new_sp))
        created.append(new_sp)
    elif old_gov_wf.exists():
        old_gov_wf.unlink()  # new file already exists, remove old one

    old_doc_wf = target / "docs" / "WORKFLOW.md"
    if old_doc_wf.exists():
        old_doc_wf.unlink()  # replaced by LIFECYCLE.md + phase system

    # If existing AGENTS.md is oversized, back it up and replace with a hub.
    agents_path = target / "AGENTS.md"
    if agents_path.exists():
        agents_lines = len(agents_path.read_text(encoding="utf-8").splitlines())
        if agents_lines > 200:
            backup_path = target / "AGENTS.md.bak"
            if not backup_path.exists():
                import shutil

                shutil.copy2(agents_path, backup_path)

            hub = (
                f"# {name} \u2014 Agent Governance\n\n"
                f"**Type:** {ptype}  \n"
                f"**Language:** {lang}  \n\n"
                "---\n\n"
                "## Governance File Registry\n\n"
                "| File | Content | Load timing |\n"
                "| ---- | ------- | ----------- |\n"
                "| `docs/governance/RULES.md` | Hard rules, stop conditions, "
                "project-specific rules | Every session start |\n"
                "| `docs/governance/SESSION-PROTOCOL.md` | Session lifecycle, "
                "save/push protocol | Every session start |\n"
                "| `docs/governance/LIFECYCLE.md` | AEE phase lifecycle, "
                "readiness gates | Every session start |\n"
                "| `docs/governance/ROLES.md` | Agent role boundaries | "
                "Every session start |\n"
                "| `docs/governance/CONTEXT-BUDGET.md` | Context management | "
                "Every session start |\n"
                "| `docs/governance/VERIFICATION.md` | Verification, "
                "consistency | When verifying |\n"
                "| `docs/governance/DRIFT-METRICS.md` | Environment, "
                "platform | On audit |\n\n"
                "Other project documents:\n\n"
                "| File | Content |\n"
                "| ---- | ------- |\n"
                "| `LEDGER.md` | Append-only work record |\n"
                "| `docs/REQUIREMENTS.md` | Formal requirements |\n"
                "| `docs/TEST_SPEC.md` | Test cases |\n"
                "| `docs/ARCHITECTURE.md` | Architecture |\n\n"
                "---\n\n"
                f"*Original AGENTS.md ({agents_lines} lines) backed up "
                "to AGENTS.md.bak. Content extracted into modular "
                "governance files above.*\n"
            )
            agents_path.write_text(hub, encoding="utf-8")
            created.append(agents_path)

    # Initialize credit tracking with unlimited budget
    specsmith_dir = target / ".specsmith"
    if not specsmith_dir.exists():
        from specsmith.credits import CreditBudget, save_budget

        save_budget(target, CreditBudget())  # unlimited by default
        created.append(target / ".specsmith" / "credit-budget.json")

    # --- Community files (only create if missing) ---
    _write(
        "CONTRIBUTING.md",
        f"# Contributing to {name}\n\n"
        "See `AGENTS.md` for governance and `LEDGER.md` for session state.\n\n"
        "## Workflow\n"
        "All changes follow: propose \u2192 check \u2192 execute \u2192 verify \u2192 record.\n",
    )
    _write(
        "SECURITY.md",
        f"# Security Policy\n\n"
        f"To report a vulnerability in {name}, please use the repository's "
        "private vulnerability reporting feature. Do not open a public issue.\n",
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
