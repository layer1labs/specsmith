# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for CodityAdapter (REQ-354, TEST-354/355) and codity-ai-review skill (REQ-356, TEST-356).

Covers:
    TEST-354 — CodityAdapter generates GitHub workflow by default
    TEST-355 — CodityAdapter detects GitLab and Azure VCS
    TEST-356 — codity-ai-review skill in governance catalog
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.config import ProjectConfig, ProjectType
from specsmith.integrations import get_adapter, list_adapters
from specsmith.integrations.codity import CodityAdapter


@pytest.fixture
def config() -> ProjectConfig:
    return ProjectConfig(
        name="test-project",
        type=ProjectType.CLI_PYTHON,
        language="python",
        description="Test project",
        git_init=False,
    )


# ---------------------------------------------------------------------------
# TEST-354 — CodityAdapter generates GitHub workflow by default
# ---------------------------------------------------------------------------


class TestCodityAdapterGitHub:
    """TEST-354: Default VCS (no signals) → GitHub workflow generated."""

    def test_adapter_name(self) -> None:
        assert CodityAdapter().name == "codity"

    def test_adapter_in_registry(self) -> None:
        assert "codity" in list_adapters()

    def test_get_adapter(self) -> None:
        adapter = get_adapter("codity")
        assert isinstance(adapter, CodityAdapter)

    def test_generates_github_workflow(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = CodityAdapter()
        files = adapter.generate(config, tmp_path)
        workflow = tmp_path / ".github" / "workflows" / "codity-review.yml"
        assert workflow.exists(), "GitHub Actions workflow not created"
        assert workflow in files

    def test_github_workflow_content(self, config: ProjectConfig, tmp_path: Path) -> None:
        CodityAdapter().generate(config, tmp_path)
        content = (tmp_path / ".github" / "workflows" / "codity-review.yml").read_text(
            encoding="utf-8"
        )
        assert "codity review --staged" in content
        assert "https://cli.codity.ai/install.sh" in content
        assert "CODITY_ACCESS_TOKEN" in content
        assert "actions/checkout@v4" in content

    def test_generates_setup_doc(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = CodityAdapter()
        files = adapter.generate(config, tmp_path)
        setup_doc = tmp_path / "docs" / "codity-setup.md"
        assert setup_doc.exists(), "docs/codity-setup.md not created"
        assert setup_doc in files

    def test_setup_doc_content(self, config: ProjectConfig, tmp_path: Path) -> None:
        CodityAdapter().generate(config, tmp_path)
        content = (tmp_path / "docs" / "codity-setup.md").read_text(encoding="utf-8")
        assert "codity login" in content
        assert "codity init" in content
        assert "codity doctor" in content
        assert "codity review --staged" in content

    def test_appends_ledger_when_present(self, config: ProjectConfig, tmp_path: Path) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# LEDGER\n\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = ledger.read_text(encoding="utf-8")
        assert "codity login" in content
        assert "codity doctor" in content
        assert "Codity" in content

    def test_github_ledger_entry_mentions_github_app(
        self, config: ProjectConfig, tmp_path: Path
    ) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# LEDGER\n\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = ledger.read_text(encoding="utf-8")
        assert "https://github.com/apps/codity" in content

    def test_skips_ledger_when_absent(self, config: ProjectConfig, tmp_path: Path) -> None:
        # Should not raise even when LEDGER.md does not exist.
        adapter = CodityAdapter()
        files = adapter.generate(config, tmp_path)
        # Only workflow + setup doc expected
        assert len(files) == 2


# ---------------------------------------------------------------------------
# TEST-355 — CodityAdapter VCS detection (GitLab / Azure)
# ---------------------------------------------------------------------------


class TestCodityAdapterVCSDetection:
    """TEST-355: VCS detection from scaffold.yml content and directory heuristics."""

    def test_detect_github_default(self, tmp_path: Path) -> None:
        assert CodityAdapter()._detect_vcs(tmp_path) == "github"

    def test_detect_gitlab_from_scaffold_yml(self, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: gitlab\n", encoding="utf-8")
        assert CodityAdapter()._detect_vcs(tmp_path) == "gitlab"

    def test_detect_gitlab_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: GitLab\n", encoding="utf-8")
        assert CodityAdapter()._detect_vcs(tmp_path) == "gitlab"

    def test_detect_azure_from_scaffold_yml(self, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: azure\n", encoding="utf-8")
        assert CodityAdapter()._detect_vcs(tmp_path) == "azure"

    def test_detect_gitlab_from_gitlab_ci_file(self, tmp_path: Path) -> None:
        (tmp_path / ".gitlab-ci.yml").write_text("stages: [test]\n", encoding="utf-8")
        assert CodityAdapter()._detect_vcs(tmp_path) == "gitlab"

    def test_detect_azure_from_azure_pipelines_file(self, tmp_path: Path) -> None:
        (tmp_path / "azure-pipelines.yml").write_text("trigger: none\n", encoding="utf-8")
        assert CodityAdapter()._detect_vcs(tmp_path) == "azure"

    def test_gitlab_workflow_file_path(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: gitlab\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        assert (tmp_path / ".gitlab-ci-codity.yml").exists()
        assert not (tmp_path / ".github").exists()

    def test_gitlab_workflow_has_pat_setup(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: gitlab\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = (tmp_path / ".gitlab-ci-codity.yml").read_text(encoding="utf-8")
        assert "codity config set-pat --provider gitlab" in content

    def test_azure_workflow_file_path(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: azure\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        assert (tmp_path / ".azure-pipelines" / "codity-review.yml").exists()

    def test_azure_workflow_has_pat_setup(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: azure\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = (tmp_path / ".azure-pipelines" / "codity-review.yml").read_text(encoding="utf-8")
        assert "codity config set-pat --provider azure" in content

    def test_gitlab_ledger_entry_mentions_pat(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: gitlab\n", encoding="utf-8")
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# LEDGER\n\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = ledger.read_text(encoding="utf-8")
        assert "CODITY_GITLAB_PAT" in content

    def test_azure_ledger_entry_mentions_pat(self, config: ProjectConfig, tmp_path: Path) -> None:
        (tmp_path / "scaffold.yml").write_text("vcs: azure\n", encoding="utf-8")
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# LEDGER\n\n", encoding="utf-8")
        CodityAdapter().generate(config, tmp_path)
        content = ledger.read_text(encoding="utf-8")
        assert "CODITY_AZURE_PAT" in content


# ---------------------------------------------------------------------------
# TEST-356 — codity-ai-review skill is in governance skills catalog
# ---------------------------------------------------------------------------


class TestCoditySkill:
    """TEST-356: codity-ai-review skill present and correct in governance catalog."""

    def _get_codity_skill(self):
        from specsmith.skills.governance import SKILLS

        matches = [s for s in SKILLS if s.slug == "codity-ai-review"]
        assert matches, "codity-ai-review skill not found in governance SKILLS"
        return matches[0]

    def test_skill_exists(self) -> None:
        self._get_codity_skill()

    def test_skill_domain(self) -> None:
        from specsmith.skills import SkillDomain

        skill = self._get_codity_skill()
        assert skill.domain == SkillDomain.GOVERNANCE

    def test_skill_tags(self) -> None:
        skill = self._get_codity_skill()
        assert "codity" in skill.tags
        assert "ai-review" in skill.tags
        assert "pre-commit" in skill.tags

    def test_skill_body_review_staged(self) -> None:
        skill = self._get_codity_skill()
        assert "codity review --staged" in skill.body

    def test_skill_body_login(self) -> None:
        skill = self._get_codity_skill()
        assert "codity login" in skill.body

    def test_skill_body_init(self) -> None:
        skill = self._get_codity_skill()
        assert "codity init" in skill.body

    def test_skill_body_scan_staged(self) -> None:
        skill = self._get_codity_skill()
        assert "codity scan --staged" in skill.body

    def test_skill_body_test_gen_staged(self) -> None:
        skill = self._get_codity_skill()
        assert "codity test-gen --staged" in skill.body

    def test_skill_body_doctor(self) -> None:
        skill = self._get_codity_skill()
        assert "codity doctor" in skill.body

    def test_skill_body_integrate_command(self) -> None:
        skill = self._get_codity_skill()
        assert "specsmith integrate codity" in skill.body

    def test_skill_body_high_severity(self) -> None:
        skill = self._get_codity_skill()
        assert "HIGH severity" in skill.body

    def test_skill_body_gitlab_pat(self) -> None:
        skill = self._get_codity_skill()
        assert "set-pat --provider gitlab" in skill.body

    def test_skill_body_azure_pat(self) -> None:
        skill = self._get_codity_skill()
        assert "set-pat --provider azure" in skill.body


# ---------------------------------------------------------------------------
# TEST-357 — AGENTS.md template contains Codity.ai pre-commit rule
# ---------------------------------------------------------------------------


class TestAgentsMdTemplate:
    """TEST-357: agents.md.j2 contains Codity.ai Code Review section."""

    def _read_template(self) -> str:
        pkg_path = Path(__file__).parent.parent / "src" / "specsmith" / "templates"
        tmpl = pkg_path / "agents.md.j2"
        return tmpl.read_text(encoding="utf-8")

    def test_template_has_codity_section(self) -> None:
        content = self._read_template()
        assert "Codity.ai Code Review" in content

    def test_template_has_review_staged(self) -> None:
        content = self._read_template()
        assert "codity review --staged" in content

    def test_template_has_high_severity_rule(self) -> None:
        content = self._read_template()
        assert "HIGH" in content

    def test_template_has_medium_severity(self) -> None:
        content = self._read_template()
        assert "MEDIUM" in content

    def test_template_has_integrate_command(self) -> None:
        content = self._read_template()
        assert "specsmith integrate codity" in content
