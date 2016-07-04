import pytest

import dicty


def test_simple():
    class Object(dicty.DictObject):
        aaa = dicty.Field()
        bbb = dicty.Field('ccc')

    obj = Object()
    assert obj == {}
    obj.aaa = 111
    assert obj.aaa == 111
    assert obj == {'aaa': 111}
    obj.bbb = 222
    assert obj.bbb == 222
    assert obj == {'aaa': 111, 'ccc': 222}

    obj = Object(aaa=111, bbb=222)
    assert obj.aaa == 111
    assert obj.bbb == 222
    assert {'aaa': 111, 'ccc': 222} == obj

    obj = Object.fromjson({'aaa': 111, 'ccc': 222, 'zzz': 333})
    assert obj.aaa == 111
    assert obj.bbb == 222
    assert obj['zzz'] == 333
    assert not hasattr(obj, 'zzz')

    obj = Object()
    with pytest.raises(AttributeError):
        obj.aaa

    with pytest.raises(AttributeError):
        obj = Object(zzz=123)

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'aaa': 111, 'zzz': 333})
    assert exc.value.path == 'ccc'
    assert exc.value.message == 'Is required'


def test_field_deletion():
    class Object(dicty.DictObject):
        foo = dicty.Field()

    obj = Object()
    with pytest.raises(KeyError):
        del obj.foo

    obj = Object(foo=123)
    del obj.foo
    assert 'foo' not in obj
