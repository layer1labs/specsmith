# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the AI Provider & Model Intelligence system (REQ-220..REQ-227)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Provider Registry (REQ-220)
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    def test_provider_entry_validation(self):
        from specsmith.agent.provider_registry import ProviderEntry, ProviderError

        # Valid entry
        e = ProviderEntry(id="test", name="Test", provider_type="byoe", base_url="http://localhost:8000/v1")
        e.validate()  # should not raise

        # Invalid: empty id
        with pytest.raises(ProviderError):
            ProviderEntry(id="", name="Test", provider_type="byoe").validate()

        # Invalid: whitespace in id
        with pytest.raises(ProviderError):
            ProviderEntry(id="has space", name="Test", provider_type="byoe").validate()

        # Invalid: bad provider type
        with pytest.raises(ProviderError):
            ProviderEntry(id="test", name="Test", provider_type="invalid").validate()

    def test_registry_crud(self, tmp_path):
        from specsmith.agent.provider_registry import ProviderEntry, ProviderError, ProviderRegistry

        reg = ProviderRegistry(path=tmp_path / "providers.json")
        assert len(reg.providers) == 0

        # Add
        reg.add(ProviderEntry(id="ollama-local", name="Local Ollama", provider_type="ollama"))
        assert len(reg.providers) == 1

        # Get
        entry = reg.get("ollama-local")
        assert entry is not None
        assert entry.name == "Local Ollama"

        # Duplicate add fails
        with pytest.raises(ProviderError):
            reg.add(ProviderEntry(id="ollama-local", name="Dupe", provider_type="ollama"))

        # Remove
        reg.remove("ollama-local")
        assert len(reg.providers) == 0

    def test_registry_persistence(self, tmp_path):
        from specsmith.agent.provider_registry import ProviderEntry, ProviderRegistry

        path = tmp_path / "providers.json"
        reg = ProviderRegistry(path=path)
        reg.add(ProviderEntry(id="vllm-1", name="vLLM Home", provider_type="vllm", base_url="http://10.0.0.1:8000/v1"))

        # Reload
        reg2 = ProviderRegistry(path=path)
        assert len(reg2.providers) == 1
        assert reg2.get("vllm-1").base_url == "http://10.0.0.1:8000/v1"

    def test_to_public_dict_redacts_key(self):
        from specsmith.agent.provider_registry import ProviderEntry

        e = ProviderEntry(id="test", name="Test", provider_type="cloud", api_key="sk-secret123", base_url="http://api.example.com")
        d = e.to_public_dict()
        assert d["api_key"] == "***"
        assert d["api_key_set"] is True

    def test_cloud_provider_auto_fills_url(self):
        from specsmith.agent.provider_registry import ProviderEntry

        e = ProviderEntry(id="my-openai", name="OpenAI", provider_type="cloud", provider_id="openai")
        e.validate()
        assert "api.openai.com" in e.base_url


# ---------------------------------------------------------------------------
# Execution Profiles (REQ-221)
# ---------------------------------------------------------------------------


class TestExecutionProfiles:
    def test_builtin_profiles_exist(self):
        from specsmith.agent.execution_profiles import ExecutionProfileStore

        store = ExecutionProfileStore()
        assert len(store.profiles) >= 5
        ids = {p.id for p in store.profiles}
        assert "unrestricted" in ids
        assert "local-only" in ids
        assert "budget" in ids
        assert "performance" in ids
        assert "air-gapped" in ids

    def test_default_is_unrestricted(self):
        from specsmith.agent.execution_profiles import ExecutionProfileStore

        store = ExecutionProfileStore()
        assert store.default().id == "unrestricted"

    def test_allows_provider_filtering(self):
        from specsmith.agent.execution_profiles import ExecutionProfileStore

        store = ExecutionProfileStore()
        local = store.get("local-only")
        assert local is not None
        assert local.allows_provider("my-ollama", "ollama")
        assert not local.allows_provider("my-openai", "cloud")

        unrestricted = store.get("unrestricted")
        assert unrestricted.allows_provider("anything", "cloud")

    def test_air_gapped_only_vllm(self):
        from specsmith.agent.execution_profiles import ExecutionProfileStore

        store = ExecutionProfileStore()
        ag = store.get("air-gapped")
        assert ag.allows_provider("my-vllm", "vllm")
        assert not ag.allows_provider("my-ollama", "ollama")
        assert not ag.allows_provider("my-openai", "cloud")


# ---------------------------------------------------------------------------
# Model Intelligence (REQ-223)
# ---------------------------------------------------------------------------


class TestModelIntelligence:
    def test_score_model_for_role(self):
        from specsmith.agent.model_intelligence import score_model_for_role

        score = score_model_for_role("gpt-4.1", "coder")
        assert 50 < score < 100

    def test_rank_models(self):
        from specsmith.agent.model_intelligence import rank_models_for_role

        models = ["gpt-4.1", "claude-opus-4", "qwen2.5:3b"]
        ranked = rank_models_for_role("coder", models)
        assert len(ranked) == 3
        # gpt-4.1 should rank higher than qwen2.5:3b for coding
        scores = {m: s for m, s in ranked}
        assert scores["gpt-4.1"] > scores["qwen2.5:3b"]

    def test_classifier_favors_local(self):
        from specsmith.agent.model_intelligence import rank_models_for_role

        models = ["gpt-4.1", "qwen2.5:3b"]
        ranked = rank_models_for_role("classifier", models)
        # qwen2.5:3b has speed+cost_efficiency scores, should win for classifier
        assert ranked[0][0] == "qwen2.5:3b"

    def test_score_store_persistence(self, tmp_path):
        from specsmith.agent.model_intelligence import ModelScoreStore

        store = ModelScoreStore(path=tmp_path / "scores.json")
        store.update_scores("custom-model", {"humaneval": 75, "ifeval": 80})

        store2 = ModelScoreStore(path=tmp_path / "scores.json")
        assert "custom-model" in store2.scores
        assert store2.scores["custom-model"]["humaneval"] == 75


# ---------------------------------------------------------------------------
# Session Init (REQ-225)
# ---------------------------------------------------------------------------


class TestSessionInit:
    def test_init_session_on_specsmith_itself(self):
        from specsmith.session_init import init_session

        ctx = init_session(".")
        assert ctx.is_governed is True
        assert ctx.health_score > 0
        assert ctx.session_id.startswith("SS-")
        assert ctx.compliance_score > 0

    def test_init_session_ungovemed_dir(self, tmp_path):
        from specsmith.session_init import init_session

        ctx = init_session(tmp_path)
        assert ctx.is_governed is False
        assert ctx.needs_import is True

    def test_session_context_to_dict(self):
        from specsmith.session_init import SessionContext

        ctx = SessionContext(project_dir="/tmp/test", project_name="test")
        d = ctx.to_dict()
        assert d["project_name"] == "test"
        assert "compliance_score" in d
        assert "health_score" in d


# ---------------------------------------------------------------------------
# Compliance (REQ-224)
# ---------------------------------------------------------------------------


class TestCompliance:
    def test_compliance_summary_on_specsmith(self):
        from specsmith.compliance import get_compliance_summary

        s = get_compliance_summary(".")
        assert s.total_requirements > 0
        assert s.total_tests > 0
        assert s.compliance_score > 0
        assert isinstance(s.trace_matrix, list)

    def test_governance_rules_status(self):
        from specsmith.compliance import get_governance_rules_status

        rules = get_governance_rules_status(".")
        assert len(rules) == 14  # H1-H14
        assert all(r["id"].startswith("H") for r in rules)

    def test_compliance_summary_empty_project(self, tmp_path):
        from specsmith.compliance import get_compliance_summary

        s = get_compliance_summary(tmp_path)
        assert s.total_requirements == 0
        assert s.compliance_score == 0


# ---------------------------------------------------------------------------
# Datasources (REQ-222)
# ---------------------------------------------------------------------------


class TestDatasources:
    def test_patentsview_client_instantiates(self):
        from specsmith.datasources.patentsview import PatentsViewClient

        client = PatentsViewClient()
        assert client.name == "PatentsView"
        assert client.source_id == "patentsview"

    def test_all_clients_have_required_methods(self):
        from specsmith.datasources.citations import CitationsClient
        from specsmith.datasources.fpd import FPDClient
        from specsmith.datasources.odp import ODPClient
        from specsmith.datasources.patentsview import PatentsViewClient
        from specsmith.datasources.pfw import PFWClient
        from specsmith.datasources.ppubs import PPUBSClient
        from specsmith.datasources.ptab import PTABClient

        for cls in [PatentsViewClient, PPUBSClient, ODPClient, PFWClient, CitationsClient, FPDClient, PTABClient]:
            client = cls() if cls in (PPUBSClient, ODPClient, CitationsClient, FPDClient, PTABClient) else cls("")
            assert hasattr(client, "search")
            assert hasattr(client, "get")
            assert hasattr(client, "test_connection")
            assert hasattr(client, "name")
            assert hasattr(client, "source_id")

    def test_base_http_helpers_exist(self):
        from specsmith.datasources.base import DataSourceError, http_get, http_post

        assert callable(http_get)
        assert callable(http_post)
        assert issubclass(DataSourceError, RuntimeError)
