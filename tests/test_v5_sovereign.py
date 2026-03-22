"""Tests for PRADYSAGICAN v5 — Sovereign Lock, Benchmarks, Feature Registry, Manifest."""
import pytest
import time
import hashlib
from pradysagican.safety.sovereign_lock import SovereignLock, SovereignCredential, LicenseManager


def _make_credential(i, now):
    """Create a properly signed credential."""
    oid = f"gov_{i}"
    name = f"Official {i}"
    dept = "Defense"
    sig = hashlib.sha256(f"{oid}:{name}:{dept}:{now}".encode()).hexdigest()
    return SovereignCredential(
        official_id=oid, name=name, clearance_level=4, department=dept,
        signature_hash=sig, issued_at=now, expires_at=now + 86400,
    )
from pradysagican.benchmarks.benchmark_suite import BenchmarkSuite
from pradysagican.core.feature_registry import FeatureRegistry
from pradysagican.core.system_manifest import SystemManifest


# ── Sovereign Lock ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sovereign_lock_correct_password():
    lock = SovereignLock()
    now = time.time()
    credentials = [_make_credential(i, now) for i in range(3)]
    session = await lock.authenticate("pradyisgod", credentials)
    assert session is not None
    assert session.is_active


@pytest.mark.asyncio
async def test_sovereign_lock_wrong_password():
    lock = SovereignLock()
    now = time.time()
    credentials = [_make_credential(i, now) for i in range(3)]
    session = await lock.authenticate("wrong_password", credentials)
    assert session is None


@pytest.mark.asyncio
async def test_sovereign_lock_insufficient_credentials():
    lock = SovereignLock()
    now = time.time()
    credentials = [_make_credential(0, now)]  # Only 1, need 3
    session = await lock.authenticate("pradyisgod", credentials)
    assert session is None  # Need 3+ officials


@pytest.mark.asyncio
async def test_sovereign_ip_ban():
    lock = SovereignLock()
    lock.ban_ip("192.168.1.100")
    try:
        session = await lock.authenticate("pradyisgod", [], ip_address="192.168.1.100")
        assert session is None  # Should fail for banned IP
    except PermissionError:
        assert True  # Expected


def test_license_manager():
    lm = LicenseManager()
    license = lm.generate_license("Test Org", "PROFESSIONAL", 365)
    assert lm.validate_license(license.license_key)
    # PROFESSIONAL can't modify
    has_modify = lm.check_modification_rights(license.license_key)
    assert not has_modify


# ── Benchmark Suite ───────────────────────────────────────────────────────

def test_benchmark_count():
    bs = BenchmarkSuite()
    # benchmark_count is a property/int, not a method
    count = bs.benchmark_count
    assert count >= 30


@pytest.mark.asyncio
async def test_run_benchmark():
    bs = BenchmarkSuite()
    benchmarks = bs.list_benchmarks()
    result = await bs.run_benchmark(benchmarks[0])
    assert result.percentage >= 0


@pytest.mark.asyncio
async def test_run_all_benchmarks():
    bs = BenchmarkSuite()
    results = await bs.run_all()
    assert len(results) >= 30


@pytest.mark.asyncio
async def test_leaderboard():
    bs = BenchmarkSuite()
    await bs.run_all()
    leaderboard = bs.get_leaderboard()
    assert isinstance(leaderboard, (dict, list, str))


@pytest.mark.asyncio
async def test_gap_analysis():
    bs = BenchmarkSuite()
    await bs.run_all()
    gaps = bs.gap_analysis()
    assert isinstance(gaps, (dict, list))


# ── Feature Registry ──────────────────────────────────────────────────────

def test_feature_count_over_million():
    fr = FeatureRegistry()
    assert fr.total_features() >= 1_000_000


def test_base_features():
    fr = FeatureRegistry()
    base = fr.list_base_features()
    assert len(base) >= 800


def test_unique_features():
    fr = FeatureRegistry()
    unique = fr.list_unique_features()
    assert len(unique) >= 50


def test_feature_search():
    fr = FeatureRegistry()
    results = fr.search_features("consciousness")
    assert len(results) >= 1


# ── System Manifest ───────────────────────────────────────────────────────

def test_manifest_discovery():
    sm = SystemManifest()
    summary = sm.get_architecture_summary()
    assert summary["total_modules"] >= 40
    assert summary["total_classes"] >= 200


def test_manifest_connections():
    sm = SystemManifest()
    connections = sm.get_all_connections()
    assert len(connections) >= 20


def test_manifest_validation():
    sm = SystemManifest()
    issues = sm.validate_wiring()
    assert isinstance(issues, list)
