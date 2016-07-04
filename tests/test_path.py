import pytest

import dicty


def test_basic_aliasing():
    class Foo(dicty.DictObject):
        foo = dicty.DictField()
        foo_bar = dicty.DictField('fooBar')

        class Bar(dicty.DictObject):
            foo = dicty.DictField()
            foo_bar = dicty.DictField('fooBar')

        nested = dicty.TypedObjectField(Bar)

    assert Foo.foo == 'foo'
    assert Foo.foo_bar == 'fooBar'
    assert Foo.foo_bar.key == 'fooBar'
    assert Foo.foo_bar.attname == 'foo_bar'
    assert Foo.nested == 'nested'
    assert Foo.nested.foo == 'nested.foo'
    assert Foo.nested.foo_bar == 'nested.fooBar'
    assert Foo.nested.foo_bar.key == 'fooBar'
    assert Foo.nested.foo_bar.attname == 'foo_bar'


def test_list_items_indexes():
    class Foo(dicty.DictObject):
        class Bar(dicty.DictObject):
            foo = dicty.DictField()
            foo_bar = dicty.DictField('fooBar')

        nested = dicty.TypedListField(Bar)

    assert Foo.nested == 'nested'
    assert Foo.nested.foo == 'nested.foo'
    assert Foo.nested.foo_bar == 'nested.fooBar'

    assert Foo.nested[1].foo == 'nested.1.foo'
    assert Foo.nested[2].foo_bar == 'nested.2.fooBar'


def test_dict_items_indexes():
    class Foo(dicty.DictObject):
        class Bar(dicty.DictObject):
            foo = dicty.DictField()
            foo_bar = dicty.DictField('fooBar')

        nested = dicty.TypedDictField(Bar)

    assert Foo.nested == 'nested'
    assert Foo.nested.foo == 'nested.foo'
    assert Foo.nested.foo_bar == 'nested.fooBar'

    assert Foo.nested['aaa'].foo == 'nested.aaa.foo'
    assert Foo.nested['bbb'].foo_bar == 'nested.bbb.fooBar'

    with pytest.raises(IndexError):
        assert Foo.nested['x.y'].foo_bar
