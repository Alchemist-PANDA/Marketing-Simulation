"""
Vectorized population generator.

The original Agent-object generator (base_agent.create_persona_set) builds
one Python dataclass instance per agent via a Python loop — fine for
thousands of agents, but the dominant cost at 100k-1M scale. This module
generates the exact same statistical population directly as float32 NumPy
arrays, with zero per-agent Python object construction.
"""

from typing import Dict, Optional
import numpy as np

# (low, high) uniform ranges per archetype, matching base_agent.create_archetype_agent
ARCHETYPE_TRAIT_RANGES = {
    'price_sensitive': {
        'openness': (0.3, 0.6), 'conscientiousness': (0.8, 1.0),
        'extraversion': (0.2, 0.5), 'agreeableness': (0.4, 0.7), 'neuroticism': (0.1, 0.4),
    },
    'impulsive': {
        'openness': (0.6, 0.9), 'conscientiousness': (0.1, 0.4),
        'extraversion': (0.8, 1.0), 'agreeableness': (0.4, 0.7), 'neuroticism': (0.6, 0.9),
    },
    'social_proof': {
        'openness': (0.5, 0.8), 'conscientiousness': (0.4, 0.7),
        'extraversion': (0.6, 0.9), 'agreeableness': (0.8, 1.0), 'neuroticism': (0.2, 0.5),
    },
    'skeptical': {
        'openness': (0.1, 0.4), 'conscientiousness': (0.5, 0.8),
        'extraversion': (0.1, 0.4), 'agreeableness': (0.1, 0.4), 'neuroticism': (0.8, 1.0),
    },
}

ARCHETYPES = ['price_sensitive', 'impulsive', 'social_proof', 'skeptical']
DEFAULT_DISTRIBUTION = {
    'price_sensitive': 0.30,
    'impulsive': 0.25,
    'social_proof': 0.25,
    'skeptical': 0.20,
}


def generate_population_arrays(
    n: int,
    seed: Optional[int] = None,
    distribution: Optional[Dict[str, float]] = None
) -> Dict[str, np.ndarray]:
    """
    Generate a population of n agents as float32 NumPy arrays.

    No Python object construction per-agent — entire population materializes
    via vectorized np.random calls, then is shuffled once.

    Returns a dict of float32/int8 arrays, each of length n:
        openness, conscientiousness, extraversion, agreeableness, neuroticism,
        price_sensitivity, trust_sensitivity, urgency_sensitivity, skepticism,
        money, archetype_idx, money_spent, purchased
    """
    rng = np.random.RandomState(seed)
    distribution = distribution or DEFAULT_DISTRIBUTION

    counts = {a: int(n * w) for a, w in distribution.items()}
    # Fix rounding so total == n
    remainder = n - sum(counts.values())
    keys = list(counts.keys())
    i = 0
    while remainder > 0:
        counts[keys[i % len(keys)]] += 1
        remainder -= 1
        i += 1

    trait_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    arrays = {t: [] for t in trait_names}
    archetype_idx_chunks = []

    for arch_i, archetype in enumerate(ARCHETYPES):
        count = counts.get(archetype, 0)
        if count == 0:
            continue
        ranges = ARCHETYPE_TRAIT_RANGES[archetype]
        for t in trait_names:
            lo, hi = ranges[t]
            arrays[t].append(rng.uniform(lo, hi, count).astype(np.float32))
        archetype_idx_chunks.append(np.full(count, arch_i, dtype=np.int8))

    population = {t: np.concatenate(arrays[t]) for t in trait_names}
    population['archetype_idx'] = np.concatenate(archetype_idx_chunks)
    population['money'] = rng.uniform(50, 2000, n).astype(np.float32)

    # Shuffle once so archetype blocks don't correlate with array position
    perm = rng.permutation(n)
    for key in population:
        population[key] = population[key][perm]

    # Derived sensitivities (vectorized, matches Agent.__init__ formulas)
    population['price_sensitivity'] = population['conscientiousness'] * 0.8
    population['trust_sensitivity'] = population['agreeableness'] * 0.7
    population['urgency_sensitivity'] = (
        population['extraversion'] * 0.5 + population['neuroticism'] * 0.4
    )
    population['skepticism'] = population['neuroticism'] * 0.3

    population['money_spent'] = np.zeros(n, dtype=np.float32)
    population['purchased'] = np.zeros(n, dtype=np.bool_)

    return population


def population_memory_bytes(population: Dict[str, np.ndarray]) -> int:
    """Total bytes consumed by a population's arrays."""
    return sum(arr.nbytes for arr in population.values())


def archetype_name(idx: int) -> str:
    return ARCHETYPES[idx]
