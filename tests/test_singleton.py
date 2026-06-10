from typani.singleton import Singleton, SingletonMeta


def test_singleton_returns_same_instance() -> None:
    class MyService(Singleton): ...

    a = MyService()
    b = MyService()
    assert a is b


def test_different_singleton_subclasses_are_independent() -> None:
    class A(Singleton): ...

    class B(Singleton): ...

    assert A() is not B()
    assert A() is A()
    assert B() is B()


def test_singleton_meta_directly() -> None:
    class Config(metaclass=SingletonMeta): ...

    x = Config()
    y = Config()
    assert x is y


def test_singleton_preserves_attributes() -> None:
    class Counter(Singleton):
        def __init__(self) -> None:
            self.count = 0

    c1 = Counter()
    c1.count = 5
    c2 = Counter()
    assert c2.count == 5
    assert c2 is c1
