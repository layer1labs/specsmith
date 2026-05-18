"""languages — Canonical language/extension registry for specsmith.

This module is the **single source of truth** for language support across:
  - specsmith CLI (import detection, phase checks, info/scan commands)
  - Kairos (GovernancePanel chips, language scanner)

Verilog vs SystemVerilog note
-------------------------------
These are DISTINCT languages and must NOT be merged:
  - Verilog (IEEE 1364, .v) — original HDL, found in legacy cores and old
    Xilinx ISE / Quartus II projects. Most simulators still support it.
  - SystemVerilog (IEEE 1800, .sv / .svh) — superset of Verilog. Adds design
    extensions (interfaces, packages, enums) AND verification extensions
    (assertions, classes, covergroups). The dominant HDL for new FPGA work.
  Tools like iverilog, Verilator, and Questa handle both; GHDL handles VHDL only.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Extension → internal language key
# ---------------------------------------------------------------------------
# Keys are always lowercase. Values are canonical internal identifiers.
# Multiple extensions can map to the same language key.

EXT_LANG: dict[str, str] = {
    # Systems languages
    ".c": "c",
    ".h": "c",  # headers usually associated with C
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    # Managed runtimes
    ".py": "python",
    ".pyw": "python",
    ".cs": "csharp",
    ".vb": "vbnet",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".groovy": "groovy",
    # JavaScript / TypeScript ecosystem
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    # Mobile / cross-platform
    ".swift": "swift",
    ".dart": "dart",
    ".mm": "objc",
    # HDL / FPGA / EDA  ← VERILOG AND SYSTEMVERILOG ARE DISTINCT
    ".vhd": "vhdl",
    ".vhdl": "vhdl",
    ".v": "verilog",  # IEEE 1364 Verilog (legacy .v files)
    ".sv": "systemverilog",  # IEEE 1800 SystemVerilog (design files)
    ".svh": "systemverilog",  # SystemVerilog header/interface files
    # Scripting / shells
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "bash",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".psd1": "powershell",
    ".cmd": "cmd",
    ".bat": "cmd",
    ".lua": "lua",
    ".rb": "ruby",
    ".php": "php",
    ".pl": "perl",
    # Functional / academic
    ".hs": "haskell",
    ".lhs": "haskell",
    ".ml": "ocaml",
    ".mli": "ocaml",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".clj": "clojure",
    ".nim": "nim",
    ".zig": "zig",
    # Web / markup
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".less": "css",
    ".vue": "vue",
    ".svelte": "svelte",
    # Data / config / markup
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".jsonc": "json",
    ".xml": "xml",
    ".sql": "sql",
    ".tf": "terraform",
    ".tfvars": "terraform",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    # Build systems
    # (Makefile has no extension — detected by name, not here)
    ".cmake": "cmake",
    # Embedded / Linux
    ".bb": "bitbake",
    ".bbappend": "bitbake",
    ".bbclass": "bitbake",
    ".inc": "bitbake",  # also used by C but bitbake is the primary use
    ".dts": "devicetree",
    ".dtsi": "devicetree",
    # Documentation
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "restructuredtext",
    ".tex": "latex",
    ".bib": "bibtex",
    ".adoc": "asciidoc",
    # Hardware / EDA (non-HDL)
    ".kicad_pcb": "kicad",
    ".kicad_sch": "kicad",
    ".kicad_pro": "kicad",
    ".sch": "kicad",  # legacy KiCad schematic
    # Data science
    ".r": "r",
    ".rmd": "r",
    ".jl": "julia",
    # .m is ambiguous (Objective-C or MATLAB) — resolved by broader context
    ".ipynb": "jupyter",
}

# ---------------------------------------------------------------------------
# Internal language key → human-readable display name
# ---------------------------------------------------------------------------

LANG_DISPLAY: dict[str, str] = {
    "c": "C",
    "cpp": "C++",
    "rust": "Rust",
    "go": "Go",
    "python": "Python",
    "csharp": "C#",
    "vbnet": "VB.NET",
    "java": "Java",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "groovy": "Groovy",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "swift": "Swift",
    "dart": "Dart",
    "objc": "Objective-C",
    "vhdl": "VHDL",
    "verilog": "Verilog",  # IEEE 1364 — keep distinct from SV
    "systemverilog": "SystemVerilog",  # IEEE 1800 — keep distinct from Verilog
    "bash": "Bash",
    "powershell": "PowerShell",
    "cmd": "Cmd / Batch",
    "lua": "Lua",
    "ruby": "Ruby",
    "php": "PHP",
    "perl": "Perl",
    "haskell": "Haskell",
    "ocaml": "OCaml",
    "elixir": "Elixir",
    "erlang": "Erlang",
    "clojure": "Clojure",
    "nim": "Nim",
    "zig": "Zig",
    "html": "HTML",
    "css": "CSS",
    "vue": "Vue",
    "svelte": "Svelte",
    "yaml": "YAML",
    "toml": "TOML",
    "json": "JSON",
    "xml": "XML",
    "sql": "SQL",
    "terraform": "Terraform / HCL",
    "protobuf": "Protobuf",
    "graphql": "GraphQL",
    "cmake": "CMake",
    "bitbake": "BitBake",
    "devicetree": "DeviceTree",
    "markdown": "Markdown",
    "restructuredtext": "reStructuredText",
    "latex": "LaTeX",
    "bibtex": "BibTeX",
    "asciidoc": "AsciiDoc",
    "kicad": "KiCad",
    "r": "R",
    "julia": "Julia",
    "matlab": "MATLAB",
    "jupyter": "Jupyter Notebook",
    "makefile": "Makefile",  # detected by filename, not extension
}

# ---------------------------------------------------------------------------
# Internal language key → category (for UI grouping)
# ---------------------------------------------------------------------------

LANG_CATEGORY: dict[str, str] = {
    "c": "Systems",
    "cpp": "Systems",
    "rust": "Systems",
    "go": "Systems",
    "python": "Managed",
    "csharp": "Managed",
    "vbnet": "Managed",
    "java": "Managed",
    "kotlin": "Managed",
    "scala": "Managed",
    "groovy": "Managed",
    "javascript": "Web / JS",
    "typescript": "Web / JS",
    "swift": "Mobile",
    "dart": "Mobile",
    "objc": "Mobile",
    "vhdl": "HDL / FPGA",
    "verilog": "HDL / FPGA",
    "systemverilog": "HDL / FPGA",
    "bash": "Scripting",
    "powershell": "Scripting",
    "cmd": "Scripting",
    "lua": "Scripting",
    "ruby": "Scripting",
    "php": "Scripting",
    "perl": "Scripting",
    "haskell": "Functional",
    "ocaml": "Functional",
    "elixir": "Functional",
    "erlang": "Functional",
    "clojure": "Functional",
    "nim": "Systems",
    "zig": "Systems",
    "html": "Web / Markup",
    "css": "Web / Markup",
    "vue": "Web / JS",
    "svelte": "Web / JS",
    "yaml": "Config / Data",
    "toml": "Config / Data",
    "json": "Config / Data",
    "xml": "Config / Data",
    "sql": "Config / Data",
    "terraform": "DevOps / IaC",
    "protobuf": "Config / Data",
    "graphql": "Config / Data",
    "cmake": "Build",
    "makefile": "Build",
    "bitbake": "Embedded / Linux",
    "devicetree": "Embedded / Linux",
    "markdown": "Documentation",
    "restructuredtext": "Documentation",
    "latex": "Documentation",
    "bibtex": "Documentation",
    "asciidoc": "Documentation",
    "kicad": "Hardware / EDA",
    "r": "Data Science",
    "julia": "Data Science",
    "matlab": "Data Science",
    "jupyter": "Data Science",
}

# Filename-only detection (no extension) — checked separately by name
FILENAME_LANG: dict[str, str] = {
    "Makefile": "makefile",
    "GNUmakefile": "makefile",
    "makefile": "makefile",
    "Dockerfile": "dockerfile",
    "Jenkinsfile": "groovy",
    "Vagrantfile": "ruby",
    "Rakefile": "ruby",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def display_name(lang_key: str) -> str:
    """Return human-readable display name for a language key."""
    return LANG_DISPLAY.get(lang_key, lang_key.title())


def category(lang_key: str) -> str:
    """Return UI category for a language key."""
    return LANG_CATEGORY.get(lang_key, "Other")


def all_display_names() -> list[str]:
    """Sorted unique display names for all known languages."""
    return sorted(set(LANG_DISPLAY.values()))


def lang_key_from_display(display: str) -> str | None:
    """Reverse-lookup: display name → internal key. Case-insensitive."""
    normalized = display.lower()
    for key, disp in LANG_DISPLAY.items():
        if disp.lower() == normalized:
            return key
    return None


def detect_language(ext: str) -> str | None:
    """Return language key for a file extension (including leading dot)."""
    return EXT_LANG.get(ext.lower())


def extensions_for(lang_key: str) -> list[str]:
    """Return all file extensions that map to the given language key."""
    return sorted(ext for ext, lang in EXT_LANG.items() if lang == lang_key)
