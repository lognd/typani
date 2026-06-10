import typani


def test_package_imports() -> None:
    assert hasattr(typani, "Result")
    assert hasattr(typani, "Ok")
    assert hasattr(typani, "Err")
    assert hasattr(typani, "Unit")
    assert hasattr(typani, "Unreachable")
    assert hasattr(typani, "Option")
    assert hasattr(typani, "Some")
    assert hasattr(typani, "Nothing")
    assert hasattr(typani, "singleton")
    assert hasattr(typani, "Singleton")
    assert hasattr(typani, "SingletonMeta")
    assert hasattr(typani, "SingletonModel")
    assert hasattr(typani, "StrictSingleton")
    assert hasattr(typani, "StrictSingletonMeta")
    assert hasattr(typani, "ErrorSet")
    assert hasattr(typani, "merge")
    assert hasattr(typani, "dispatch")
