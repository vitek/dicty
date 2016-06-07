import pytest

import dicty


def test_list_field():
    class Foo(dicty.DictObject):
        foo = dicty.ListField()

    obj = Foo()
    assert obj.foo == []
    obj.foo.extend([1, 2, 3])
    assert obj == {'foo': [1, 2, 3]}
    assert obj.jsonize() == {'foo': [1, 2, 3]}

    obj = Foo.fromjson({'foo': [1, 2, 3]})
    assert obj.foo == [1, 2, 3]
    assert obj == {'foo': [1, 2, 3]}
    assert obj.jsonize() == {'foo': [1, 2, 3]}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Foo.fromjson({'foo': 123})
    assert exc.value.path == 'foo'
