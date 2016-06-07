import dicty


def test_optional():
    class Object(dicty.DictObject):
        aaa = dicty.Field(optional=True)

    obj = Object(aaa=123)
    assert obj.aaa == 123

    obj = Object()
    assert obj.aaa is None
    assert 'aaa' not in obj

    obj = Object.fromjson({})
    assert obj == {}


def test_default():
    class Object(dicty.DictObject):
        aaa = dicty.Field(default=123, optional=True)

    obj = Object(aaa=777)
    assert obj.aaa == 777
    assert obj['aaa'] == 777

    obj = Object()
    assert obj.aaa == 123
    assert 'aaa' not in obj


def test_default_side_effect():
    class Object(dicty.DictObject):
        aaa = dicty.Field(optional=True, default=[])

    obj = Object()
    assert not obj.hasattr(Object.aaa.attname)
    assert 'aaa' not in obj
    assert obj.aaa == []
    assert obj.hasattr(Object.aaa.attname)
    assert obj['aaa'] == []


def test_default_func():
    class Object(dicty.DictObject):
        aaa = dicty.Field(default_func=lambda obj: 123, optional=True)

    obj = Object()
    assert obj.aaa == 123
    assert obj['aaa'] == 123
