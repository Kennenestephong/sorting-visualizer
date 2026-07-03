from sorting_visualizer.core.events import Compare, Swap, Overwrite, MarkSorted


def test_events_are_frozen_and_carry_fields():
    assert Compare(1, 2).i == 1 and Compare(1, 2).j == 2
    assert Swap(3, 4).j == 4
    ow = Overwrite(0, 9, 5)
    assert (ow.i, ow.value, ow.old) == (0, 9, 5)
    assert MarkSorted(7).i == 7


def test_events_equal_by_value():
    assert Compare(1, 2) == Compare(1, 2)
    assert Swap(1, 2) != Swap(2, 1)
