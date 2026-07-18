import pytest

from specsmith.esdb import SqliteRecord, SqliteStore
from specsmith.guided_compression import ContextElement, GuidedCompressor, guided_compress


def test_conversation_and_convenience_compression_are_callable(tmp_path) -> None:
    history = [
        {"role": "user", "content": "Keep the exact release constraint."},
        {"role": "assistant", "content": "Acknowledged."},
    ]

    direct = GuidedCompressor(tmp_path).compress_from_conversation(history)
    convenience = guided_compress(tmp_path, history=history)

    assert direct.original_size > 0
    assert convenience.original_size == direct.original_size


def test_esdb_compression_is_a_real_class_method_and_reads_active_records(tmp_path) -> None:
    with SqliteStore(tmp_path) as store:
        store.upsert(
            SqliteRecord(
                id="REQ-999",
                kind="requirement",
                label="Preserve this requirement",
                data={"status": "implemented"},
            )
        )
        store.upsert(
            SqliteRecord(
                id="OLD-001",
                kind="fact",
                status="tombstone",
                label="Do not load",
            )
        )

    result = GuidedCompressor(tmp_path).compress_from_esdb()

    assert result.original_size > 0
    assert result.elements_preserved + result.elements_summarized == 1


@pytest.mark.parametrize(
    ("target_fill_pct", "expected"),
    [(20, "discard"), (20.1, "summarize"), (40, "summarize"), (40.1, "preserve")],
)
def test_medium_tier_compression_boundaries(
    tmp_path, target_fill_pct: float, expected: str
) -> None:
    element = ContextElement(
        element_id="medium",
        element_type="conversation_turn",
        content="boundary behavior",
        metadata={"adjusted_tier": "TIER_MEDIUM"},
    )

    assert GuidedCompressor(tmp_path)._decide_action(element, target_fill_pct) == expected
