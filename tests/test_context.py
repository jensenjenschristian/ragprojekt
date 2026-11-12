from src.context import reorder_for_context


def test_five_items():
    assert reorder_for_context([1, 2, 3, 4, 5]) == [1, 3, 5, 4, 2]


def test_best_first_second_last():
    out = reorder_for_context(list("abcdef"))
    assert out[0] == "a" and out[-1] == "b"


def test_edge_cases():
    assert reorder_for_context([]) == []
    assert reorder_for_context(["only"]) == ["only"]


def test_nothing_lost_or_duplicated():
    items = list(range(10))
    assert sorted(reorder_for_context(items)) == items