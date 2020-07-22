import wrappingpaper as wp


def test_stack_id():
    def abc(x=None):
        a = wp.get_stack_id(x)
        b = wp.get_stack_id(x)
        return a, b

    a1, b1 = abc()
    assert a1 != b1
    a2, b2 = abc()
    assert a1 == a2 and b1 == b2


def test_uid():
    x = wp.uid('asdf', 10)
    y = wp.uid('wert', 10)
    x2 = wp.uid('asdf', 10)
    assert x // 1e10 == 0
    assert x // 1e9 > 0
    assert x != y and x == x2
