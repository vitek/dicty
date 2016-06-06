import datetime

import pytest

from dicty import (
    DictObject, Field, DatetimeField, DateField,
    TypedObjectField, TypedListField, TypedDictField,
    FieldError, ShadowField, IntegerField, FloatField, StringField,
    ListField, DictField, BooleanField, RegexpStringField,
    JSONObjectRuntimeError)


def test_simple():
    class Object(DictObject):
        aaa = Field()
        bbb = Field(name='ccc')

    assert isinstance(Object.aaa, Field)

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

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'aaa': 111, 'zzz': 333})
    assert exc.value.path == 'ccc'
    assert exc.value.message == 'Is required'


def test_optional():
    class Object(DictObject):
        aaa = Field(optional=True)

    obj = Object(aaa=123)
    assert obj.aaa == 123

    obj = Object()
    assert obj.aaa is None
    assert 'aaa' not in obj

    obj = Object.fromjson({})
    assert obj == {}


def test_shadow():
    class Object(DictObject):
        foo = ShadowField()
    assert isinstance(Object.foo, Field)

    obj = Object()
    with pytest.raises(AttributeError):
        obj.foo
    obj.foo = 123
    assert obj == {'foo': 123}
    assert obj._shadow == {'foo': 123}

    with pytest.raises(FieldError):
        Object.fromjson({})

    class Object(DictObject):
        foo = ShadowField(optional=True)
    obj = Object()
    assert obj.foo == None
    obj = Object.fromjson({})
    assert obj == {}


def test_filters():
    class Object(DictObject):
        foo = Field(filters=[lambda x: x.upper()])
    obj = Object.fromjson({'foo': 'xxx'})
    assert obj.foo == 'XXX'
    assert obj == {'foo': 'XXX'}


    def failure(value):
        raise ValueError('failure {}'.format(value))

    class Object(DictObject):
        foo = Field(filters=[failure])

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'foo': 'xxx'})
    assert exc.value.path == 'foo'
    assert exc.value.message == 'failure xxx'

    # Shadow filters
    class Object(DictObject):
        foo = ShadowField(filters=[lambda x: x.upper()])

    obj = Object.fromjson({'foo': 'xxx'})
    assert obj.foo == 'XXX'
    assert obj._shadow == {'foo': 'XXX'}
    assert obj == {'foo': 'xxx'}


def test_datetime_field():
    class Object(DictObject):
        bday = DatetimeField(name='bDay')

    obj = Object(bday=datetime.datetime(1985, 6, 12, 11, 22, 33))
    assert obj == {'bDay': '1985-06-12 11:22:33'}
    assert obj.bday == datetime.datetime(1985, 6, 12, 11, 22, 33)

    obj = Object.fromjson({'bDay': '1985-06-12 11:22:33'})
    assert obj == {'bDay': '1985-06-12 11:22:33'}
    assert obj.bday == datetime.datetime(1985, 6, 12, 11, 22, 33)


def test_datetime_field():
    class Object(DictObject):
        bday = DateField(name='bDay')

    obj = Object()
    obj.bday = datetime.date(1985, 6, 12)
    assert obj == {'bDay': '1985-06-12'}

    obj = Object(bday=datetime.date(1985, 6, 12))
    assert obj == {'bDay': '1985-06-12'}
    assert obj.bday == datetime.date(1985, 6, 12)

    obj = Object.fromjson({'bDay': '1985-06-12'})
    assert obj == {'bDay': '1985-06-12'}
    assert obj.bday == datetime.date(1985, 6, 12)


def test_typed_object_field():
    class Nested(DictObject):
        foo = Field()

    class Object(DictObject):
        nested = TypedObjectField(Nested)

    obj = Object.fromjson({'nested': {'foo': 123}})
    assert obj.nested.foo == 123

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'nested': {}})
    assert exc.value.path == 'nested.foo'
    assert exc.value.message == 'Is required'

    obj = Object()
    assert obj.nested == {}
    obj.nested.foo = 321
    assert obj == {'nested': {'foo': 321}}

    with pytest.raises(FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.message == 'must be dictionary'


def test_typed_list_field():
    class Nested(DictObject):
        foo = Field()

    class Object(DictObject):
        nested = TypedListField(Nested)

    obj = Object.fromjson({'nested': []})
    assert obj.nested == []

    obj = Object.fromjson({'nested': [{'foo': 123}]})
    assert obj.nested[0].foo == 123

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'nested': [{}]})
    assert exc.value.path == 'nested[0].foo'
    assert exc.value.message == 'Is required'

    obj = Object()
    assert obj.nested == []
    obj.nested.append(Nested(foo=123))
    assert obj == {'nested': [{'foo': 123}]}

    with pytest.raises(FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.message == 'must be list'


def test_typed_dict_field():
    class Nested(DictObject):
        foo = Field()

    class Object(DictObject):
        nested = TypedDictField(Nested)

    obj = Object.fromjson({'nested': {}})
    assert obj.nested == {}

    obj = Object.fromjson({'nested': {'xxx': {'foo': 123}}})
    assert obj.nested['xxx'].foo == 123

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'nested': {'xxx':{}}})
    assert exc.value.path == "nested['xxx'].foo"
    assert exc.value.message == 'Is required'

    obj = Object()
    assert obj.nested == {}
    obj.nested['xxx'] = Nested(foo=123)
    assert obj == {'nested': {'xxx': {'foo': 123}}}

    with pytest.raises(FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.message == 'must be dict'


def test_integer_field():
    class Object(DictObject):
        foo = IntegerField()

    obj = Object.fromjson({'foo': 123})
    assert obj == {'foo': 123}

    obj = Object.fromjson({'foo': 123L})
    assert obj == {'foo': 123L}

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'foo': 1.223})
    assert exc.value.path == 'foo'
    assert exc.value.message == (
        "Must be of (<type 'int'>, <type 'long'>) type "
        "got <type 'float'> instead")


def test_float_field():
    class Object(DictObject):
        foo = FloatField()

    obj = Object.fromjson({'foo': 1.234})
    assert obj == {'foo': 1.234}

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'foo': 123})
    assert exc.value.path == 'foo'
    assert exc.value.message == (
        "Must be of (<type 'float'>,) type "
        "got <type 'int'> instead")


def test_string_field():
    class Object(DictObject):
        foo = StringField()

    obj = Object.fromjson({'foo': "string"})
    assert obj == {'foo': "string"}

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'foo': 123})
    assert exc.value.path == 'foo'
    assert exc.value.message == (
        "Must be of (<type 'unicode'>, <type 'str'>) type "
        "got <type 'int'> instead")


def test_regexp_string_field():
    class Object(DictObject):
        foo = RegexpStringField(regexp="^a+$")

    obj = Object.fromjson({'foo': "aaa"})
    assert obj == {'foo': "aaa"}

    with pytest.raises(FieldError) as exc:
        obj = Object.fromjson({'foo': "bbb"})
    assert exc.value.path == 'foo'
    assert exc.value.message == "Does not match regular expression"


def test_references():
    class Object1(DictObject):
        pass

    class Foo(DictObject):
        obj1 = TypedObjectField('test_dicty.Object1')
        obj2 = TypedObjectField('test_dicty.ObjectXXX')

    obj = Foo()
    assert isinstance(obj.obj1, Object1)
    with pytest.raises(JSONObjectRuntimeError):
        obj.obj2


def test_dict_of_lists_of_objects_regression():
    class Foo(DictObject):
        foo = StringField()

    class Bar(DictObject):
        foos = TypedDictField(
            TypedListField(Foo), optional=True)

    o = Bar.fromjson({'foos': {'x':[{'foo': 'foo'}, {'foo': 'bar'}]}})
    assert o.jsonize() == {'foos': {'x':[{'foo': 'foo'}, {'foo': 'bar'}]}}
