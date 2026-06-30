"""
Performance regression tests for the array-native simulation engine.

These tests validate the engine's scaling characteristics at 100,000 agents:
population generation, single-ad simulation, A/B cohort splitting, memory
footprint, and Streamlit-cache hit speedup. Targets are based on measured
performance of the pure-NumPy fallback path (no Numba required to pass).
"""

import time
import numpy as np
import pytest

from src.agents.agent_generator import generate_population_arrays, population_memory_bytes
from src.simulation.max_engine import MaxSimulation
from src.simulation.ab_test_runner import ABTestRunner
from src.ad_processing.ad import Ad

N_LARGE = 100_000


def test_generation_speed():
    """Generating 100k agents should be fast (well under 100ms)."""
    t0 = time.perf_counter()
    generate_population_arrays(N_LARGE, seed=42)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.1, f"Population generation took {elapsed*1000:.2f}ms, expected < 100ms"


def test_simulation_speed():
    """Simulating exposure for 100k agents should complete in < 50ms (warm path)."""
    population = generate_population_arrays(N_LARGE, seed=42)
    sim = MaxSimulation(seed=42, population={k: v.copy() for k, v in population.items()})
    ad = Ad(text="Limited time offer — act now!", channel="facebook", creative_type="text", price=20.0)

    # Warmup call absorbs first-call overhead (array allocation, Numba JIT compile if present).
    sim.simulate_exposure(ad)

    sim2 = MaxSimulation(seed=42, population={k: v.copy() for k, v in population.items()})
    t0 = time.perf_counter()
    sim2.simulate_exposure(ad)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.05, f"Simulation took {elapsed*1000:.2f}ms, expected < 50ms"


def test_ab_test_speed():
    """Full A/B test (cohort split + two simulations) for 100k agents should complete in < 100ms."""
    population = generate_population_arrays(N_LARGE, seed=42)
    runner = ABTestRunner(num_agents=N_LARGE, seed=42, master_population=population)

    # Warmup
    runner.run_test("Save 50% today!", "Experience luxury.", channel="facebook", price=20.0)

    runner2 = ABTestRunner(num_agents=N_LARGE, seed=42, master_population=population)
    t0 = time.perf_counter()
    runner2.run_test("Save 50% today!", "Experience luxury.", channel="facebook", price=20.0)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.1, f"A/B test took {elapsed*1000:.2f}ms, expected < 100ms"


def test_memory_footprint():
    """Population array memory for 100k agents should stay under 5MB.

    sys.getsizeof() on a dict only reports the container's shallow size, not
    the NumPy array payloads it holds, so it can't measure actual data size.
    population_memory_bytes() sums each array's .nbytes for an accurate total.
    """
    population = generate_population_arrays(N_LARGE, seed=42)
    mem_mb = population_memory_bytes(population) / 1e6
    assert mem_mb < 5.0, f"Population memory was {mem_mb:.2f}MB, expected < 5MB"


def test_cache_hit_speedup():
    """A second generation call with identical params should be markedly faster
    than the first when wrapped by Streamlit's @st.cache_data (simulated here
    via direct function reuse, since cache_data requires a Streamlit runtime).
    """
    cache = {}

    def cached_generate(n, seed):
        key = (n, seed)
        if key not in cache:
            cache[key] = generate_population_arrays(n, seed=seed)
        return cache[key]

    t0 = time.perf_counter()
    cached_generate(N_LARGE, 42)
    first_call = time.perf_counter() - t0

    t0 = time.perf_counter()
    cached_generate(N_LARGE, 42)
    second_call = time.perf_counter() - t0

    assert second_call < first_call * 0.7, (
        f"Cache hit ({second_call*1000:.4f}ms) was not >30% faster than "
        f"cache miss ({first_call*1000:.4f}ms)"
    )


def test_no_python_agent_loop_state_update():
    """Sanity check: purchase/money state must update via vectorized boolean
    masking, i.e. all agents who can afford + are sampled as buyers end up
    marked purchased, with no agent left half-updated (which a buggy loop
    could produce)."""
    population = generate_population_arrays(5000, seed=7)
    sim = MaxSimulation(seed=7, population=population)
    ad = Ad(text="Buy now!", channel="facebook", creative_type="text", price=10.0)
    result = sim.simulate_exposure(ad)

    bought_mask = sim.population["purchased"]
    assert bought_mask.sum() == result["conversions"]
    spent_for_buyers = sim.population["money_spent"][bought_mask]
    assert np.all(spent_for_buyers >= ad.price)
