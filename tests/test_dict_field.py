import pytest

import dicty


def test_dict_field():
    class Foo(dicty.DictObject):
        foo = dicty.DictField()

    obj = Foo()
    assert obj.foo == {}
    obj.foo.update({1: 2, 3: 4})
    assert obj == {'foo': {1: 2, 3: 4}}
    assert obj.jsonize() == {'foo': {1: 2, 3: 4}}

    obj = Foo.fromjson({'foo': {1: 2, 3: 4}})
    assert obj.foo == {1: 2, 3: 4}
    assert obj == {'foo': {1: 2, 3: 4}}
    assert obj.jsonize() == {'foo': {1: 2, 3: 4}}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Foo.fromjson({'foo': 123})
    assert exc.value.path == 'foo'
