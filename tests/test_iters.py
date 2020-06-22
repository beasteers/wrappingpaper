import wrappingpaper as wp


def test_iters():
    items = list(range(10))

    # test precheck
    it = iter(items)
    first, it = wp.pre_check_iter(it, 3)
    assert first == [0, 1, 2]
    assert list(it) == items

    # test run forever
    N = 3
    repit = wp.run_iter_forever(lambda: items)
    assert list(wp.limit(repit, len(items) * N)) == items * N

    # test run forever returns None if empty
    it = iter(items)
    repit = wp.run_iter_forever(lambda: it, none_if_empty=True)
    assert list(wp.limit(repit, len(items) + 2)) == items + [None]*2
