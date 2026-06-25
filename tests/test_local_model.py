# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for local_model.py: hardware-aware Ollama model selector and CLI.

REQ-385, REQ-386
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# REQ-385 — LocalModelInfo and detect_local_model
# ---------------------------------------------------------------------------


class TestDetectLocalModel:
    def test_apple_silicon_32gb_returns_32b_model(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=36.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.model == "qwen2.5-coder:32b"
        assert "apple-silicon" in info.hardware

    def test_apple_silicon_24gb_returns_14b_model(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=24.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.model == "qwen2.5-coder:14b"

    def test_apple_silicon_10gb_returns_7b_model(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=10.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.model == "qwen2.5-coder:7b"

    def test_apple_silicon_4gb_returns_none(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=4.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is None

    def test_nvidia_24gb_returns_32b_model(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=24.0),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.model == "qwen2.5-coder:32b"
        assert "nvidia" in info.hardware

    def test_nvidia_rtx4070_8gb_returns_7b_model(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=8.0),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.model == "qwen2.5-coder:7b"

    def test_nvidia_4gb_returns_none(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=4.0),
        ):
            info = detect_local_model()

        assert info is None

    def test_cpu_only_returns_none(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is None

    def test_local_model_info_pull_cmd(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=24.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is not None
        assert info.pull_cmd == f"ollama pull {info.model}"
        assert info.runtime == "ollama"

    def test_local_model_info_hf_repo(self) -> None:
        from specsmith.local_model import detect_local_model

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=24.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            info = detect_local_model()

        assert info is not None
        assert "Qwen" in info.hf_repo


class TestPickModel:
    def test_pick_model_returns_7b_at_exact_threshold(self) -> None:
        from specsmith.local_model import _pick_model

        result = _pick_model(7.0, tier_32b=20.0, tier_14b=10.0, tier_7b=7.0)
        assert result == "qwen2.5-coder:7b"

    def test_pick_model_returns_none_below_threshold(self) -> None:
        from specsmith.local_model import _pick_model

        result = _pick_model(5.0, tier_32b=20.0, tier_14b=10.0, tier_7b=7.0)
        assert result is None

    def test_pick_model_returns_32b_at_exact_32b_threshold(self) -> None:
        from specsmith.local_model import _pick_model

        result = _pick_model(20.0, tier_32b=20.0, tier_14b=10.0, tier_7b=7.0)
        assert result == "qwen2.5-coder:32b"


class TestEnsureLocalModel:
    def test_returns_false_when_ollama_not_installed(self) -> None:
        from specsmith.local_model import ensure_local_model

        with patch("shutil.which", return_value=None):
            assert ensure_local_model("qwen2.5-coder:7b") is False

    def test_returns_true_when_model_already_present(self) -> None:
        from specsmith.local_model import ensure_local_model

        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            assert ensure_local_model("qwen2.5-coder:7b") is True

    def test_returns_true_after_successful_pull(self) -> None:
        from specsmith.local_model import ensure_local_model

        responses = [
            MagicMock(returncode=1),  # ollama show — not present
            MagicMock(returncode=0),  # ollama pull — success
        ]
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", side_effect=responses),
        ):
            assert ensure_local_model("qwen2.5-coder:7b") is True

    def test_returns_false_on_pull_failure(self) -> None:
        from specsmith.local_model import ensure_local_model

        responses = [
            MagicMock(returncode=1),  # ollama show — not present
            MagicMock(returncode=1),  # ollama pull — failure
        ]
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", side_effect=responses),
        ):
            assert ensure_local_model("qwen2.5-coder:7b") is False


# ---------------------------------------------------------------------------
# REQ-386 — specsmith local-model CLI
# ---------------------------------------------------------------------------


class TestLocalModelCLI:
    def test_local_model_group_registered(self) -> None:
        from specsmith.cli import main

        assert "local-model" in main.commands  # type: ignore[attr-defined]

    def test_detect_subcommand_registered(self) -> None:
        from specsmith.cli import main

        lm = main.commands["local-model"]  # type: ignore[attr-defined]
        assert "detect" in lm.commands  # type: ignore[attr-defined]

    def test_setup_subcommand_registered(self) -> None:
        from specsmith.cli import main

        lm = main.commands["local-model"]  # type: ignore[attr-defined]
        assert "setup" in lm.commands  # type: ignore[attr-defined]

    def test_detect_prints_model_when_gpu_present(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main
        from specsmith.local_model import LocalModelInfo

        mock_info = LocalModelInfo(
            model="qwen2.5-coder:14b",
            runtime="ollama",
            hardware="apple-silicon-24gb",
            vram_gb=24.0,
            pull_cmd="ollama pull qwen2.5-coder:14b",
        )

        runner = CliRunner()
        with patch("specsmith.local_model.detect_local_model", return_value=mock_info):
            result = runner.invoke(main, ["local-model", "detect"])

        assert result.exit_code == 0
        assert "qwen2.5-coder:14b" in result.output
        assert "apple-silicon" in result.output

    def test_detect_prints_skip_message_for_cpu_only(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        with patch("specsmith.local_model.detect_local_model", return_value=None):
            result = runner.invoke(main, ["local-model", "detect"])

        assert result.exit_code == 0
        assert "GPU" in result.output or "cpu" in result.output.lower() or "No GPU" in result.output

    def test_detect_json_output_parseable(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main
        from specsmith.local_model import LocalModelInfo

        mock_info = LocalModelInfo(
            model="qwen2.5-coder:7b",
            runtime="ollama",
            hardware="nvidia-8gb",
            vram_gb=8.0,
            pull_cmd="ollama pull qwen2.5-coder:7b",
        )

        runner = CliRunner()
        with patch("specsmith.local_model.detect_local_model", return_value=mock_info):
            result = runner.invoke(main, ["local-model", "detect", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["recommended"] == "qwen2.5-coder:7b"
        assert data["runtime"] == "ollama"

    def test_detect_json_none_for_cpu_only(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        with patch("specsmith.local_model.detect_local_model", return_value=None):
            result = runner.invoke(main, ["local-model", "detect", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["recommended"] is None

    def test_setup_skips_when_no_gpu(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("specsmith.local_model.detect_local_model", return_value=None),
        ):
            result = runner.invoke(main, ["local-model", "setup"])

        assert result.exit_code == 0
        assert "GPU" in result.output or "skip" in result.output.lower()

    def test_setup_fails_when_ollama_not_installed(self) -> None:
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        with patch("shutil.which", return_value=None):
            result = runner.invoke(main, ["local-model", "setup"])

        assert result.exit_code != 0
        assert "Ollama" in result.output or "ollama" in result.output


# ---------------------------------------------------------------------------
# REQ-387 — detect_local_models (multi-role) + config persistence (REQ-391)
# ---------------------------------------------------------------------------


class TestDetectLocalModels:
    """Multi-role model detection (TEST-395)."""

    def test_nvidia_16gb_returns_all_three_roles(self) -> None:
        from specsmith.local_model import ModelRole, detect_local_models

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=16.0),
        ):
            roles = detect_local_models()

        assert ModelRole.coding in roles
        assert ModelRole.general in roles
        assert ModelRole.reasoning in roles
        assert roles[ModelRole.coding].model == "qwen2.5-coder:14b"
        assert roles[ModelRole.general].model == "qwen2.5:14b"
        assert roles[ModelRole.reasoning].model == "deepseek-r1:14b"

    def test_nvidia_8gb_returns_7b_tiers(self) -> None:
        from specsmith.local_model import ModelRole, detect_local_models

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=8.0),
        ):
            roles = detect_local_models()

        assert roles[ModelRole.coding].model == "qwen2.5-coder:7b"
        assert roles[ModelRole.general].model == "qwen2.5:7b"
        # 8 GB is at the 7b threshold; reasoning model should still be present
        assert ModelRole.reasoning in roles

    def test_apple_silicon_24gb_returns_14b_tiers(self) -> None:
        from specsmith.local_model import ModelRole, detect_local_models

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=24.0),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            roles = detect_local_models()

        assert roles[ModelRole.coding].model == "qwen2.5-coder:14b"
        assert roles[ModelRole.general].model == "qwen2.5:14b"

    def test_cpu_only_returns_empty_dict(self) -> None:
        from specsmith.local_model import detect_local_models

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=None),
        ):
            roles = detect_local_models()

        assert roles == {}

    def test_nvidia_4gb_returns_empty_dict(self) -> None:
        """Below minimum threshold — empty dict, not an error."""
        from specsmith.local_model import detect_local_models

        with (
            patch("specsmith.local_model._detect_apple_silicon_gb", return_value=None),
            patch("specsmith.local_model._detect_nvidia_vram_gb", return_value=4.0),
        ):
            roles = detect_local_models()

        assert roles == {}


class TestLocalModelsConfig:
    """Config persistence round-trip (TEST-395, REQ-391)."""

    def test_save_and_load_round_trips(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from specsmith.local_model import (
            LocalModelInfo,
            ModelRole,
            load_local_models_config,
            save_local_models_config,
        )

        roles = {
            ModelRole.general: LocalModelInfo(
                model="qwen2.5:14b",
                runtime="ollama",
                hardware="nvidia-16gb",
                vram_gb=16.0,
                pull_cmd="ollama pull qwen2.5:14b",
            ),
            ModelRole.coding: LocalModelInfo(
                model="qwen2.5-coder:14b",
                runtime="ollama",
                hardware="nvidia-16gb",
                vram_gb=16.0,
                pull_cmd="ollama pull qwen2.5-coder:14b",
            ),
            ModelRole.reasoning: LocalModelInfo(
                model="deepseek-r1:14b",
                runtime="ollama",
                hardware="nvidia-16gb",
                vram_gb=16.0,
                pull_cmd="ollama pull deepseek-r1:14b",
            ),
        }
        save_local_models_config(tmp_path, roles)
        loaded = load_local_models_config(tmp_path)

        assert loaded["general"] == "qwen2.5:14b"
        assert loaded["coding"] == "qwen2.5-coder:14b"
        assert loaded["reasoning"] == "deepseek-r1:14b"

    def test_load_returns_empty_dict_when_file_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from specsmith.local_model import load_local_models_config

        assert load_local_models_config(tmp_path) == {}

    def test_load_returns_empty_dict_on_corrupt_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from specsmith.local_model import load_local_models_config

        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()
        (spec_dir / "local-models.yml").write_text(":::not yaml:::", encoding="utf-8")
        # Should not raise; returns empty dict
        result = load_local_models_config(tmp_path)
        assert isinstance(result, dict)

    def test_save_creates_specsmith_dir_if_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from specsmith.local_model import (
            LocalModelInfo,
            ModelRole,
            save_local_models_config,
        )

        roles = {
            ModelRole.coding: LocalModelInfo(
                model="qwen2.5-coder:7b",
                runtime="ollama",
                hardware="nvidia-8gb",
                vram_gb=8.0,
                pull_cmd="ollama pull qwen2.5-coder:7b",
            ),
        }
        save_local_models_config(tmp_path, roles)
        assert (tmp_path / ".specsmith" / "local-models.yml").exists()
