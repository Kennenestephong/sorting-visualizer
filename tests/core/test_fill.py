from sorting_visualizer.core.fill import FillMode, generate


def test_random_is_permutation_of_1_to_n():
    out = generate(50, FillMode.RANDOM, seed=1)
    assert sorted(out) == list(range(1, 51))


def test_reversed_is_descending():
    assert generate(5, FillMode.REVERSED) == [5, 4, 3, 2, 1]


def test_nearly_sorted_is_mostly_sorted():
    out = generate(100, FillMode.NEARLY_SORTED, seed=1)
    misplaced = sum(1 for i, v in enumerate(out) if v != i + 1)
    assert 0 < misplaced <= 20  # a few swaps only


def test_seed_is_reproducible():
    assert generate(30, FillMode.RANDOM, seed=7) == generate(30, FillMode.RANDOM, seed=7)


def test_small_sizes_do_not_crash():
    assert generate(0, FillMode.NEARLY_SORTED) == []
    assert generate(1, FillMode.NEARLY_SORTED) == [1]
