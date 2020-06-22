import time


def interval_checker(sec):
    def f():
        f.ts.append(current())
    f.ts = []
    f.t0 = time.time()
    f.sec = sec

    def current():
        return int((time.time() - f.t0) / f.sec)

    def check():
        assert (
            f.ts == list(range(len(f.ts))) or
            f.ts == list(range(1, 1 + len(f.ts))))

    f.current = current
    f.check = check
    return f
