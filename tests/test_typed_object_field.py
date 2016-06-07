import pytest

import dicty


def test_typed_object_field():
    class Nested(dicty.DictObject):
        foo = dicty.Field()

    class Object(dicty.DictObject):
        nested = dicty.TypedObjectField(Nested)

    obj = Object.fromjson({'nested': {'foo': 123}})
    assert obj.nested.foo == 123

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'nested': {}})
    assert exc.value.path == 'nested.foo'
    assert exc.value.message == 'Is required'

    obj = Object()
    assert obj.nested == {}
    obj.nested.foo = 321
    assert obj == {'nested': {'foo': 321}}

    with pytest.raises(dicty.FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.message == 'must be dictionary'


def test_references():
    class Object1(dicty.DictObject):
        pass

    class Foo(dicty.DictObject):
        obj1 = dicty.TypedObjectField(
            'tests.test_typed_object_field.Object1')
        obj2 = dicty.TypedObjectField(
            'tests.test_typed_object_field.ObjectNotFound')

    obj = Foo()
    assert isinstance(obj.obj1, Object1)
    with pytest.raises(dicty.DictyRuntimeError):
        obj.obj2
