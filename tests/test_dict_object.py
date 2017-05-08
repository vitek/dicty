import pytest

import dicty


def test_duplicate_keys():
    with pytest.raises(dicty.DictyRuntimeError):
        class A(dicty.DictObject):
            foo = dicty.Field('foo')
            bar = dicty.Field('foo')


def test_field_override():
    class A(dicty.DictObject):
        bar = dicty.Field(default='a')

    class B(A):
        bar = dicty.Field(default='b', optional=True, override=True)

    obj = B()
    assert obj.bar == 'b'


def test_field_override_error():
    with pytest.raises(dicty.DictyRuntimeError):
        class A(dicty.DictObject):
            bar = dicty.Field(override=True)


def test_subclasses():
    class A(dicty.DictObject):
        a = dicty.Field()

    class B(A):
        b = dicty.Field()

    assert sorted(B._fields.keys()) == ['a', 'b']

    obj = B.fromjson({'a': 1, 'b': 2})
    assert obj.jsonize() == {'a': 1, 'b': 2}


def test_minins():
    class AMixIn():
        a = dicty.Field()

    class B(dicty.DictObject, AMixIn):
        b = dicty.Field()

    assert sorted(B._fields.keys()) == ['a', 'b']

    obj = B.fromjson({'a': 1, 'b': 2})
    assert obj.jsonize() == {'a': 1, 'b': 2}


def test_subclass_duplicate_errors():
    class A(dicty.DictObject):
        a = dicty.Field('a')

    with pytest.raises(dicty.DictyRuntimeError) as exc:
        class B(A):
            a = dicty.Field('b')
    assert exc.value.args == (
        'Duplicate declaration of \'a\' field with key \'b\'',
    )
