"""Tests for OMEGA Memory Citadel cross-tier internals (O45-O48)."""

from pradysagican.omega.memory_citadel import MemoryCitadelAPI


def test_retrieve_hides_metadata_by_default() -> None:
    citadel = MemoryCitadelAPI()
    citadel.store("fact about user", {"key": "timezone", "value": "IST"})

    plain = citadel.retrieve("fact about user", include_metadata=False)
    meta = citadel.retrieve("fact about user", include_metadata=True)

    assert plain["items"]
    assert meta["items"]
    assert "_citadel_meta" not in plain["items"][0]
    assert "_citadel_meta" in meta["items"][0]


def test_garbage_collection_deduplicates_and_caps_tier() -> None:
    citadel = MemoryCitadelAPI()
    for _ in range(3):
        citadel.store("fact", {"key": "duplicate", "value": "same"})
    for i in range(20):
        citadel.store("fact", {"key": f"k{i}", "value": str(i)})

    stats = citadel.garbage_collect(max_entries_per_tier=10, keep_recent=5)
    semantic = citadel.retrieve("fact", limit=100, include_metadata=True)["items"]

    assert stats["removed_duplicates"] >= 2
    assert len(semantic) <= 10


def test_synchronize_invalidates_conflicts_and_syncs_latest() -> None:
    citadel = MemoryCitadelAPI()
    # Tier 3 source (semantic)
    citadel.store("fact", {"key": "planet", "value": "earth"})
    # Tier 1 conflict (working/default route)
    citadel.store("hello", {"key": "planet", "value": "mars"})

    sync = citadel.synchronize(source_tier=3, target_tiers=(1, 2))
    working = citadel.retrieve("hello", limit=20, include_metadata=True)["items"]

    assert sync["invalidated"] >= 1
    assert sync["synced"] >= 1
    assert any(e.get("key") == "planet" and e.get("value") == "earth" for e in working)
    assert not any(e.get("key") == "planet" and e.get("value") == "mars" for e in working)


def test_compress_tier_moves_summaries_and_keeps_recent() -> None:
    citadel = MemoryCitadelAPI()
    for i in range(12):
        citadel.store("what happened yesterday", {"content": f"event-{i}"})

    result = citadel.compress_tier(tier=2, target_tier=3, group_size=3, keep_recent=2)
    episodic = citadel.retrieve("what happened yesterday", limit=20, include_metadata=True)["items"]
    semantic = citadel.retrieve("fact", limit=20, include_metadata=True)["items"]

    assert result["compressed_groups"] > 0
    assert result["removed_entries"] == 10
    assert len(episodic) == 2
    assert any(item.get("compressed") is True for item in semantic)


def test_rehearsal_priority_prefers_high_importance() -> None:
    citadel = MemoryCitadelAPI()
    citadel.store("hello", {"content": "low", "importance": 0.1})
    citadel.store("hello", {"content": "high", "importance": 0.9})

    rehearsal = citadel.rehearse(sample_size=1, strategy="priority")

    assert rehearsal["count"] == 1
    assert rehearsal["items"][0]["content"] == "high"
