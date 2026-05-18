# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Documentation-system skills — MkDocs, Sphinx, mdBook, Rustdoc, Doxygen, JSDoc, TypeDoc, OpenAPI.

H23 Documentation Lifecycle Gate: architecture → requirements → tests → docs.
H24 Skills Documentation Required: every new skill appears in docs/site/skills-index.md.

Default recommendations by project type / language:
  Python         → MkDocs (Material) + RTD
  Rust library   → rustdoc (cargo doc) + docs.rs
  Rust app       → mdBook
  C/C++          → Doxygen
  JavaScript     → JSDoc
  TypeScript     → TypeDoc
  Java/Kotlin    → Javadoc / Dokka
  REST API       → OpenAPI/Swagger
  Any project    → UserManual (MANUAL.md) as bare-minimum fallback
"""

from specsmith.skills import SkillDomain, SkillEntry

_PT_DOCS = [
    "python",
    "python-library",
    "rust",
    "rust-library",
    "nodejs",
    "typescript",
    "java",
    "cpp",
    "rest-api",
    "fpga-rtl",
    "fpga-rtl-amd",
    "fpga-rtl-intel",
    "embedded",
    "generic",
]

SKILLS: list[SkillEntry] = [
    # ── MkDocs / ReadTheDocs ──────────────────────────────────────────────
    SkillEntry(
        slug="mkdocs",
        name="MkDocs — Material theme, RTD deploy, nav, admonitions",
        description=(
            "MkDocs with Material theme: project setup, mkdocs.yml nav, "
            "admonitions, code highlighting, ReadTheDocs deploy, and CI integration."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "mkdocs",
            "readthedocs",
            "rtd",
            "material",
            "docs",
            "python",
            "markdown",
            "mkdocs-material",
            "github-pages",
            "ci",
        ],
        project_types=["python", "python-library", "generic"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["mkdocs", "mkdocs-material"],
        body="""\
# MkDocs Skill

**Default documentation system for Python projects.** Also suitable for any project
that needs clean, searchable Markdown-based docs.

## Quick setup
```bash
pip install mkdocs mkdocs-material
mkdocs new docs-project    # creates mkdocs.yml + docs/index.md
cd docs-project
mkdocs serve               # local preview at http://127.0.0.1:8000
```

## Recommended mkdocs.yml
```yaml
site_name: My Project
site_url: https://my-project.readthedocs.io
repo_url: https://github.com/owner/repo

docs_dir: docs/site

theme:
  name: material
  palette:
    - scheme: default
      primary: deep purple
    - scheme: slate
      primary: deep purple
  features:
    - navigation.sections
    - navigation.expand
    - content.code.copy
    - search.suggest
    - navigation.tabs

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api.md
  - Contributing: contributing.md

markdown_extensions:
  - tables
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.details
  - toc:
      permalink: true
```

## ReadTheDocs integration
```yaml
# .readthedocs.yaml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.12"
mkdocs:
  configuration: mkdocs.yml
python:
  install:
    - method: pip
      path: .
      extra_requirements: [docs]
```

```toml
# pyproject.toml [project.optional-dependencies]
docs = ["mkdocs>=1.5", "mkdocs-material>=9.5", "pymdownx>=10"]
```

## GitHub Actions CI deploy to RTD
```yaml
name: Docs
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -e ".[docs]"
      - run: mkdocs build --strict  # fails on warnings
```

## Admonitions
```markdown
!!! note "Title"
    Note body text.

!!! warning
    Warning without custom title.

!!! tip "Pro tip"
    Tip text.
```

## Common pitfalls
- `docs_dir` default is `docs/`; set it explicitly if your layout differs.
- `mkdocs build --strict` turns warnings into errors — always use in CI.
- RTD needs `mkdocs` in `extra_requirements` or the build fails silently.
- Navigation order in `nav:` is not inferred — list every page explicitly.
""",
    ),
    # ── Sphinx ────────────────────────────────────────────────────────────
    SkillEntry(
        slug="sphinx",
        name="Sphinx — reStructuredText / MyST, autodoc, RTD, intersphinx",
        description=(
            "Sphinx documentation engine: conf.py setup, autodoc for API docs, "
            "MyST Markdown support, ReadTheDocs, and intersphinx cross-project links."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "sphinx",
            "readthedocs",
            "rtd",
            "autodoc",
            "rst",
            "myst",
            "python",
            "api-docs",
            "intersphinx",
        ],
        project_types=["python", "python-library"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["sphinx"],
        body="""\
# Sphinx Skill

Sphinx is the standard for Python library API documentation (numpy, Django, etc.).
Use MkDocs for narrative docs; use Sphinx when you need autodoc API generation.

## Quick setup
```bash
pip install sphinx sphinx-rtd-theme myst-parser
mkdir docs && cd docs
sphinx-quickstart        # interactive — choose "separate source and build"
```

## conf.py essentials
```python
extensions = [
    "sphinx.ext.autodoc",      # generate API docs from docstrings
    "sphinx.ext.viewcode",     # link to source
    "sphinx.ext.intersphinx",  # cross-project links
    "myst_parser",             # Markdown support
]
html_theme = "sphinx_rtd_theme"
# Auto-import project
import sys, os
sys.path.insert(0, os.path.abspath("../src"))
# intersphinx: link to Python stdlib docs
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
```

## Autodoc usage
```rst
.. automodule:: mypackage.module
   :members:
   :undoc-members:
   :show-inheritance:
```

```markdown
<!-- MyST version -->
```{eval-rst}
.. autofunction:: mypackage.utils.helper
```
```

## Build
```bash
make html       # builds to docs/_build/html/
make linkcheck  # validates all external links
```

## Common pitfalls
- Use `myst-parser` to write docs in Markdown instead of RST.
- `autodoc` requires the package to be importable — add `sys.path` in conf.py.
- RTD: set `python.install` to install your package's extras.
""",
    ),
    # ── mdBook ────────────────────────────────────────────────────────────
    SkillEntry(
        slug="mdbook",
        name="mdBook — Rust book-format docs, GitHub Pages, CI",
        description=(
            "mdBook: the Rust ecosystem standard for project-level documentation. "
            "book.toml setup, SUMMARY.md structure, GitHub Pages deployment, and CI."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "mdbook",
            "rust",
            "docs",
            "markdown",
            "github-pages",
            "book",
            "ci",
        ],
        project_types=["rust"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["mdbook"],
        body="""\
# mdBook Skill

**Default documentation system for Rust applications.** Use `cargo doc` + docs.rs
for API reference; use mdBook for guides, architecture docs, and user manuals.

## Quick setup
```bash
cargo install mdbook
mdbook init docs        # creates docs/book.toml and docs/src/
cd docs
mdbook serve            # live preview at http://localhost:3000
mdbook build            # output to docs/book/
```

## book.toml
```toml
[book]
title    = "My Project"
authors  = ["Your Name"]
language = "en"
src      = "src"

[build]
build-dir = "book"

[output.html]
default-theme = "navy"
git-repository-url = "https://github.com/owner/repo"
edit-url-template  = "https://github.com/owner/repo/edit/main/docs/{path}"
```

## SUMMARY.md structure
```markdown
# Summary

- [Introduction](./intro.md)
- [Getting Started](./getting-started.md)
- [Architecture](./architecture.md)
  - [Governance](./arch/governance.md)
- [Configuration](./config.md)
- [Contributing](./contributing.md)
```

## GitHub Pages deploy (Actions)
```yaml
name: Deploy mdBook
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cargo install mdbook
      - run: mdbook build docs
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/book
```

## Common pitfalls
- `SUMMARY.md` controls navigation — unlisted pages are not accessible.
- Links in mdBook are relative to the source file, not the book root.
- Use mdBook pre-processors (e.g. `mdbook-mermaid`) for diagrams.
""",
    ),
    # ── Rustdoc / cargo doc ───────────────────────────────────────────────
    SkillEntry(
        slug="rustdoc",
        name="rustdoc — cargo doc, docs.rs, intra-doc links, doctests",
        description=(
            "Rust cargo doc: writing doc comments, intra-doc links, doctests, "
            "docs.rs auto-publish, and #![deny(missing_docs)] enforcement."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "rustdoc",
            "cargo",
            "docs-rs",
            "rust",
            "api-docs",
            "doctests",
            "intra-doc-links",
        ],
        project_types=["rust", "rust-library"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["rustup", "cargo"],
        body="""\
# rustdoc Skill

**Default API documentation system for Rust libraries.** Every published crate on
crates.io gets free docs.rs hosting automatically.

## Doc comments
```rust
/// One-line summary.
///
/// Longer explanation goes here. Supports Markdown including **bold**, `code`,
/// and code blocks.
///
/// # Examples
///
/// ```rust
/// use mylib::greet;
/// assert_eq!(greet("world"), "Hello, world!");
/// ```
///
/// # Errors
/// Returns [`MyError::Empty`] when the input is empty.
///
/// # Panics
/// Panics if `n` is zero.
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}
```

```rust
//! Crate-level documentation (top of lib.rs with `//!`).
//!
//! # Overview
//! This crate provides ...
```

## Build and open
```bash
cargo doc --open               # build + open in browser
cargo doc --no-deps --open     # faster: skip deps
cargo doc -p my-crate --open   # specific crate in workspace
```

## Intra-doc links
```rust
/// See also [`crate::other_module::OtherType`].
/// Equivalent to calling [`Self::method`].
/// Use the [`std::collections::HashMap`] for ...
```

## Enforce complete docs (lib.rs or Cargo.toml)
```rust
// lib.rs
#![deny(missing_docs)]
#![deny(rustdoc::broken_intra_doc_links)]
```
```toml
# Cargo.toml [package.metadata.docs.rs]
[package.metadata.docs.rs]
all-features = true          # build docs with all features enabled
rustdoc-args = ["--cfg", "docsrs"]  # for conditional docs
```

## CI
```yaml
- name: Check docs
  run: cargo doc --no-deps --all-features 2>&1 | grep -v "^warning:" && exit 0
  # Treat warnings as errors:
  env:
    RUSTDOCFLAGS: "-D warnings"
```

## Common pitfalls
- `missing_docs` lint is off by default — enable it explicitly in lib.rs.
- Intra-doc links need `use` in scope OR full crate path prefixed with `crate::`.
- docs.rs builds with nightly for some features; use `#[cfg(docsrs)]` guards.
- Doctests run as unit tests (`cargo test --doc`) — keep them compilable.
""",
    ),
    # ── Doxygen ──────────────────────────────────────────────────────────
    SkillEntry(
        slug="doxygen",
        name="Doxygen — C/C++ API docs, Doxyfile, HTML + LaTeX output",
        description=(
            "Doxygen documentation for C, C++, and multi-language projects: "
            "Doxyfile setup, doc comment syntax, HTML output, Graphviz call graphs, "
            "and CI integration."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "doxygen",
            "c",
            "cpp",
            "c++",
            "api-docs",
            "doxyfile",
            "graphviz",
            "html",
            "latex",
        ],
        project_types=["cpp", "c", "embedded"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["doxygen", "graphviz"],
        body="""\
# Doxygen Skill

**Standard API documentation for C and C++ projects.** Also supports Python, Java,
Fortran, and VHDL/Verilog (with limited RTL support).

## Generate Doxyfile
```bash
doxygen -g                # generates Doxyfile in current directory
doxygen Doxyfile          # build docs → html/ and latex/
```

## Key Doxyfile settings
```
PROJECT_NAME           = "My Project"
PROJECT_NUMBER         = "0.1.0"
OUTPUT_DIRECTORY       = docs/doxygen
INPUT                  = src/ include/
RECURSIVE              = YES
EXTRACT_ALL            = YES
EXTRACT_PRIVATE        = NO
GENERATE_HTML          = YES
GENERATE_LATEX         = NO
HAVE_DOT               = YES    # requires graphviz
CALL_GRAPH             = YES
CALLER_GRAPH           = YES
CLASS_DIAGRAMS         = YES
COLLABORATION_GRAPH    = YES
WARN_IF_UNDOCUMENTED   = YES
WARN_AS_ERROR          = NO     # set YES in CI
FILE_PATTERNS          = *.c *.h *.cpp *.hpp
```

## Doc comment syntax (C/C++)
```c
/**
 * @brief One-line summary.
 *
 * Longer description. Supports Markdown if MARKDOWN_SUPPORT = YES.
 *
 * @param[in]  buf   Input buffer (caller-owned).
 * @param[in]  len   Length of buf in bytes.
 * @param[out] out   Output value; set to parsed integer.
 * @return  0 on success, negative errno on failure.
 *
 * @note Thread-safe.
 * @warning Not reentrant when LOG_LEVEL > 2.
 *
 * @code
 * uint8_t buf[] = {0x01, 0x02};
 * int32_t out;
 * parse_header(buf, 2, &out);  // out == 0x0102
 * @endcode
 */
int parse_header(const uint8_t *buf, size_t len, int32_t *out);
```

## GitHub Actions CI
```yaml
- name: Generate Doxygen docs
  run: |
    sudo apt-get install -y doxygen graphviz
    doxygen Doxyfile
  # Deploy to GitHub Pages:
  # uses: peaceiris/actions-gh-pages@v3
  #   with: {publish_dir: docs/doxygen/html}
```

## VHDL/Verilog (limited)
```
OPTIMIZE_OUTPUT_VHDL = YES   # or OPTIMIZE_OUTPUT_FOR_C, etc.
FILE_PATTERNS        = *.vhd *.vhdl *.v *.sv
```

## Common pitfalls
- Install `graphviz` for call graphs (`dot` must be on PATH).
- `RECURSIVE = YES` is off by default — set it to scan subdirectories.
- Use `WARN_AS_ERROR = YES` in CI to catch undocumented exports.
- For large projects: enable `USE_MATHJAX = YES` for equation rendering.
""",
    ),
    # ── JSDoc ─────────────────────────────────────────────────────────────
    SkillEntry(
        slug="jsdoc",
        name="JSDoc — JavaScript API docs, @param/@returns, HTML output",
        description=(
            "JSDoc documentation for JavaScript: jsdoc.json config, @param/@returns "
            "annotations, type definitions, and GitHub Pages deploy."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "jsdoc",
            "javascript",
            "js",
            "api-docs",
            "nodejs",
            "npm",
            "html-docs",
        ],
        project_types=["nodejs", "javascript"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["node", "jsdoc"],
        body="""\
# JSDoc Skill

**Standard API documentation for JavaScript projects.** Use TypeDoc for TypeScript.

## Setup
```bash
npm install --save-dev jsdoc jsdoc-clean-jsdoc-theme
```

## jsdoc.json
```json
{
  "source": {"include": ["src"], "includePattern": ".js$"},
  "opts": {
    "recurse": true,
    "destination": "docs/api",
    "readme": "README.md"
  },
  "plugins": ["plugins/markdown"],
  "templates": {"default": {"outputSourceFiles": true}}
}
```

## Doc comment syntax
```javascript
/**
 * Parses a URL and returns its components.
 *
 * @param {string} url - The URL to parse.
 * @param {Object} [options={}] - Parsing options.
 * @param {boolean} [options.strict=false] - Strict mode.
 * @returns {URLComponents} Parsed components.
 * @throws {TypeError} When `url` is not a string.
 *
 * @example
 * const parts = parseUrl('https://example.com/path?q=1');
 * console.log(parts.hostname); // 'example.com'
 */
function parseUrl(url, options = {}) { ... }

/**
 * @typedef {Object} URLComponents
 * @property {string} protocol - URL scheme (e.g. 'https').
 * @property {string} hostname - Host without port.
 * @property {string} pathname - Path portion.
 */
```

## Build and CI
```bash
./node_modules/.bin/jsdoc -c jsdoc.json
```
```yaml
# GitHub Actions
- run: npx jsdoc -c jsdoc.json
- uses: peaceiris/actions-gh-pages@v3
  with: {publish_dir: docs/api}
```

## Common pitfalls
- JSDoc types are not checked — use TypeDoc for TypeScript type safety.
- `@param {Type}` is positional, not named — match parameter order exactly.
- Private members: add `@private` or use `@access private` to hide from output.
""",
    ),
    # ── TypeDoc ──────────────────────────────────────────────────────────
    SkillEntry(
        slug="typedoc",
        name="TypeDoc — TypeScript API docs, reflection, themes",
        description=(
            "TypeDoc documentation for TypeScript projects: typedoc.json config, "
            "type-aware reflection, TSDoc comments, and GitHub Pages deploy."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "typedoc",
            "typescript",
            "ts",
            "api-docs",
            "tsdoc",
            "nodejs",
            "npm",
        ],
        project_types=["typescript", "nodejs"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["node", "typedoc"],
        body="""\
# TypeDoc Skill

**Default API documentation system for TypeScript projects.** TypeDoc reads your
TypeScript source and generates type-aware API documentation.

## Setup
```bash
npm install --save-dev typedoc typedoc-plugin-markdown
```

## typedoc.json
```json
{
  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "readme": "README.md",
  "excludePrivate": true,
  "excludeProtected": false,
  "excludeInternal": true,
  "includeVersion": true,
  "theme": "default",
  "plugin": ["typedoc-plugin-markdown"]
}
```

## TSDoc comment syntax
```typescript
/**
 * Fetches a user by their unique identifier.
 *
 * @param userId - The unique user ID.
 * @param options - Optional fetch configuration.
 * @returns A promise resolving to the user, or `null` if not found.
 * @throws {@link ApiError} When the request fails.
 *
 * @example
 * ```typescript
 * const user = await getUser('usr_123');
 * console.log(user?.name);
 * ```
 *
 * @public
 */
async function getUser(
  userId: string,
  options?: FetchOptions,
): Promise<User | null> { ... }
```

## Build and CI
```bash
npx typedoc --options typedoc.json
```
```yaml
- run: npx typedoc --options typedoc.json
```

## Common pitfalls
- TypeDoc requires `tsconfig.json` — set `compilerOptions.declaration: true`.
- Use `@internal` to exclude implementation details from output.
- `@remarks`, `@see`, `@deprecated` follow TSDoc standard (not plain JSDoc).
""",
    ),
    # ── Javadoc / Dokka ──────────────────────────────────────────────────
    SkillEntry(
        slug="javadoc",
        name="Javadoc / Dokka — Java and Kotlin API docs",
        description=(
            "Javadoc for Java and Dokka for Kotlin/mixed projects: "
            "@param/@return syntax, Gradle integration, and CI publishing."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "javadoc",
            "dokka",
            "java",
            "kotlin",
            "android",
            "gradle",
            "api-docs",
        ],
        project_types=["java", "kotlin", "android"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["java", "gradle"],
        body="""\
# Javadoc / Dokka Skill

Use **Javadoc** for pure Java projects, **Dokka** for Kotlin or mixed Java/Kotlin.

## Javadoc comment syntax
```java
/**
 * Parses a configuration file and returns a config object.
 *
 * @param path  Path to the configuration file. Must be readable.
 * @param strict If {@code true}, unknown keys cause a parse error.
 * @return      Populated {@link Config} instance.
 * @throws      IOException if the file cannot be read.
 * @throws      ParseException if the file is malformed.
 *
 * @since 1.0
 * @see Config
 */
public static Config parseConfig(Path path, boolean strict)
        throws IOException, ParseException { ... }
```

## Generate Javadoc (Gradle)
```groovy
// build.gradle
javadoc {
    options.encoding = 'UTF-8'
    options.author   = true
    options.version  = true
    options.links    = ['https://docs.oracle.com/en/java/javase/21/docs/api/']
    failOnError = true
}
```
```bash
./gradlew javadoc    # output to build/docs/javadoc/
```

## Dokka (Kotlin / mixed)
```kotlin
// build.gradle.kts
plugins { id("org.jetbrains.dokka") version "1.9.20" }
```
```bash
./gradlew dokkaHtml   # output to build/dokka/html/
```

## CI publish to GitHub Pages
```yaml
- run: ./gradlew javadoc
- uses: peaceiris/actions-gh-pages@v3
  with: {publish_dir: build/docs/javadoc}
```

## Common pitfalls
- Always set `failOnError = true` in Gradle to catch undocumented public members.
- `@param` names must exactly match method parameter names.
- Dokka uses KDoc format (triple-slash `///`) for Kotlin; JSDoc-style for Java.
""",
    ),
    # ── OpenAPI / Swagger ─────────────────────────────────────────────────
    SkillEntry(
        slug="openapi",
        name="OpenAPI / Swagger — REST API specs, validation, codegen",
        description=(
            "OpenAPI 3.1 specification: YAML/JSON schema authoring, Swagger UI, "
            "redocly validation, code generation, and CI enforcement."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "openapi",
            "swagger",
            "rest",
            "api-spec",
            "yaml",
            "json-schema",
            "codegen",
            "redocly",
            "spectral",
        ],
        project_types=["rest-api", "python", "nodejs", "typescript", "java"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["node"],
        body="""\
# OpenAPI / Swagger Skill

**Standard REST API documentation and contract specification.**
OpenAPI 3.1 is JSON Schema aligned; Swagger 2.0 is legacy.

## Minimal openapi.yaml
```yaml
openapi: "3.1.0"
info:
  title: My API
  version: "0.1.0"
  description: Short description of the API.
  contact:
    name: BitConcepts
    url: https://bitconcepts.tech

servers:
  - url: http://localhost:8421
    description: Local development

paths:
  /health:
    get:
      summary: Liveness probe
      operationId: health_check
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/HealthResponse"

components:
  schemas:
    HealthResponse:
      type: object
      required: [ok]
      properties:
        ok:
          type: boolean
          example: true
```

## Serve Swagger UI locally
```bash
npx @stoplight/prism-cli mock openapi.yaml  # mock server on port 4010
npx @redocly/cli preview-docs openapi.yaml  # Redocly live preview
# Or via Docker:
docker run -p 8080:8080 -e SWAGGER_JSON=/api/openapi.yaml \
  -v $(pwd):/api swaggerapi/swagger-ui
```

## Validate
```bash
# Redocly (recommended — strictest validation)
npx @redocly/cli lint openapi.yaml

# Spectral (customisable rules)
npx @stoplight/spectral-cli lint openapi.yaml
```

## CI
```yaml
- name: Validate OpenAPI spec
  run: npx @redocly/cli lint openapi.yaml
```

## Code generation
```bash
# Server stubs (Python FastAPI, TypeScript Express, Java Spring, etc.)
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g python-fastapi -o generated/

# Client SDKs
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g typescript-fetch -o client-sdk/
```

## Integration with Python (FastAPI)
```python
# FastAPI auto-generates /docs (Swagger UI) and /redoc
from fastapi import FastAPI
app = FastAPI(title="My API", openapi_url="/openapi.yaml")
```

## Common pitfalls
- Use `openapi: 3.1.0` (not 3.0.x) for full JSON Schema alignment.
- `$ref` paths are relative to the file — use anchors or bundles for large specs.
- Commit `openapi.yaml` to version control — it IS the contract.
- Run `redocly lint --extends recommended` in CI to catch style issues.
""",
    ),
    # ── User Manual (bare-minimum fallback) ───────────────────────────────
    SkillEntry(
        slug="user-manual-md",
        name="User Manual — MANUAL.md bare-minimum documentation",
        description=(
            "Minimal single-file user manual (MANUAL.md) for projects that do not "
            "yet have a full documentation system. Covers installation, quick start, "
            "command reference, and configuration. Recommended default when no other "
            "doc system is configured."
        ),
        domain=SkillDomain.DOCS,
        tags=[
            "manual",
            "user-manual",
            "markdown",
            "docs",
            "minimal",
            "getting-started",
            "readme",
        ],
        project_types=_PT_DOCS,
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# User Manual Skill

**Bare-minimum documentation for any project.** When you are not ready to set up
MkDocs, mdBook, or another full docs system, maintain a single `MANUAL.md` at the
project root. It is always better than no documentation.

This is the **suggested default** in Kairos (Settings → Documentation) for new
projects until a dedicated documentation system is configured.

## Template — MANUAL.md
```markdown
# <Project Name> — User Manual

> One-line description of what this project does.

## Requirements
- OS: Linux / macOS / Windows
- Runtime: Python 3.11+ / Rust 1.75+ / Node 20+

## Installation
```bash
# From PyPI / crates.io / npm:
pip install myproject
# cargo install myproject
# npm install -g myproject
```

## Quick Start
```bash
myproject --help
myproject run --task "do something"
```

## Command Reference
| Command | Description |
|---------|-------------|
| `myproject run` | Start the agent |
| `myproject audit` | Run governance audit |

## Configuration
| Key | Default | Description |
|-----|---------|-------------|
| `MYPROJECT_PORT` | `8421` | Server port |

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history.

## License
MIT — see [LICENSE](LICENSE).
```

## When to graduate to a full docs system
- Project has > 5 commands or > 2 configuration files → add MkDocs
- Project is a Python library → add Sphinx / RTD
- Project is a Rust crate → add rustdoc / mdBook
- Project has a REST API → add OpenAPI

## Common pitfalls
- Keep MANUAL.md in version control — it is part of the product.
- Update MANUAL.md in the same commit as the feature it describes (H23).
""",
    ),
]
