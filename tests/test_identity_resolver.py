from specsmith.config_resolver import ResolvedConfig
from specsmith.identity import resolve_identity


def test_identity_dimensions_are_distinct_and_explainable(tmp_path) -> None:
    config = ResolvedConfig(
        {"identity": {"actor_id": "actor", "agent_id": "agent", "replica_id": "replica"}},
        {
            "identity.actor_id": "local",
            "identity.agent_id": "project",
            "identity.replica_id": "environment",
        },
        (),
    )
    identity = resolve_identity(config, tmp_path, session_id="session")
    assert len(set(identity.event_attribution().values())) == 4
    assert identity.provenance["actor_id"] == "local"


def test_optional_provider_detection_is_read_only_and_stable(tmp_path) -> None:
    config = ResolvedConfig({}, {}, ())
    calls = []

    def detector():
        calls.append(True)
        return {"actor_id": "provider-user", "display_name": "Display Only"}

    identity = resolve_identity(config, tmp_path, session_id="s", detectors=(detector,))
    assert calls == [True]
    assert identity.actor_id == "provider-user"
    assert "token" not in identity.event_attribution()
