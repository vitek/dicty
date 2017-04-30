import pytest

import dicty


def test_basic():
    class Nested(dicty.DictObject):
        foo = dicty.Field()

    class Object(dicty.DictObject):
        nested = dicty.TypedListField(Nested)

    obj = Object.fromjson({'nested': [{'foo': 123}]})
    assert obj.nested[0].foo == 123

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'nested': [{}]})
    assert exc.value.path == 'nested[0].foo'
    assert exc.value.args == ('Is required',)

    obj = Object()
    assert obj.nested == []
    obj.nested.append(Nested(foo=123))
    assert obj == {'nested': [{'foo': 123}]}
    assert obj.jsonize() == {'nested': [{'foo': 123}]}

    with pytest.raises(dicty.FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.args == ('must be list',)
