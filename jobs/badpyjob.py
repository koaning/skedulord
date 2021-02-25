from rich.traceback import install

install()


def func1(a, b):
    return a + b


def func2(c):
    print(c)


if __name__ == "__main__":
    func2(func1(1, '1'))
