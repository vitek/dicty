DictObject
==========

Subclassing this type you can declare your object model. `DictObject` itself is
`dict` subclass so you can access object properties as attribute or as an item:

 .. code-block:: python

    class Foo(dicty.DictObject):
        foo = dicty.Field()

    obj = Foo(foo='bar')
    obj.foo     # 'bar'
    obj['foo']  # 'bar'

Object constructor accepts properties as keyword arguments, or you can create
instance with `fromjson()` classmethod that takes object dictionary (e.g. result
`json.loads()`) as an argument:

 .. code-block:: python

    obj = Foo(foo='bar')
    obj = Foo.fromjson({'foo': 'bar'})

You can pass `DictObject` instance directly to json library or call `jsonize()`
method first that will return plain dict version of your object with only
declared fields left:

 .. code-block:: python

    obj = Foo.fromjson({'foo': 123, 'bar': 123})
    obj == {'foo': 123, 'bar': 123}
    obj.jsonize() == {'foo': 123}

Name aliasing
-------------

If you don't like naming scheme in JSON objects, API and so on. Dicty allows to
choose whatever python name you like while manually specify dictionary key. For
instance map camel-case keys to their underscore counterparts:

 .. code-block:: python

    class Foo(dicty.DictObject):
        prop_foo = dicty.Field('propFoo')

    obj = Foo(prop_foo=123)
    obj = Foo.fromjson({'propFoo': 123})
    obj.prop_foo
    obj['propFoo']


Subclassing
-----------

`DictObject` supports subclassing:

  .. code-block:: python

    class Foo(dicty.DictObject):
        foo = dicty.Field()


    class Bar(Foo):
        bar = dicty.Field()


    obj = Bar.fromjson({'foo': 1, 'bar': 2})
    print obj.jsonize()  # {'foo': 1, 'bar': 2}

Mixins are supported as well:

  .. code-block:: python

    class FooMixIn(object):
        foo = dicty.Field()


    class Bar(dicty.DictObject, FooMixIn):
        bar = dicty.Field()


    obj = Bar.fromjson({'foo': 1, 'bar': 2})
    print obj.jsonize()  # {'foo': 1, 'bar': 2}


Fields
======

`dicty.Field` is baseclass for all dicty fields. You can use itself directly to
declare a field with no special type info.

Optional fields and default values
----------------------------------

Accessing field that is not set will lead to `AttributeError`:
You can specify default value for your field:

 .. code-block:: python

    class Foo(dicty.DictObject):
        foo = dicty.Field()

    obj = Foo()
    obj.foo  # raises AttributeError

You can mark field as optional, in this case `None` will be returned if it was
not set before:

 .. code-block:: python

    class Foo(dicty.DictObject):
        foo = dicty.Field(optional=True)

    obj = Foo()
    obj.foo  # None

For optional fields you can specify default value other than `None` with
`default` argument:

 .. code-block:: python

    class Foo(dicty.DictObject):
        foo = dicty.Field(optional=True, default=123)

    obj = Foo()
    obj.foo  # 123
    obj == {}

Please note that default value does not affect internal dictionary. But if
default value is NOT hashable dict key will be set on `getattr` access.

There is also an option to suply `default_func` it's get default value for
object's field. It takes object instance as an argument. Value returned by
`default_func` is always stored in dict:

 .. code-block:: python

    class Foo(dicty.DictObject):
        id = dicty.Field(optional=True, default_func=lambda obj: uuid.uuid4().hex)

    obj = Foo()
    obj == {}
    obj.id  # Would be populated with newly generated UUID
    obj == {'id': '07d0af8affaf46c885cc251e17dbc37a'}


Available Fields
----------------

Dicty is shipped with the follwing:

`BooleanField`

`DateField`

`DatetimeField`

`DictField`

`FloatField`

`IntegerField`

`ListField`

`NativeDateField`

`NativeDatetimeField`

`NumericField`

`RegexpStringField`

`StringField`

`TypedDictField`

`TypedListField`

`TypedObjectField`


Sample usage
============

With dicty you can easily describe your data model and then use it to encode/decode JSON objects. It supports
data validataion, optional parameters, default values, nested objects and so on. 


 .. code-block:: python

    import dicty


    class MyDoc(dicty.DictObject):
        prop1 = dicty.StringField()
        prop2 = dicty.IntegerField()

    # Regular constructor
    doc = MyDoc(prop1='foo', prop2=123)
    print doc.prop1     # you can access values as attributes
    print doc['prop2']  # as well as dictionary items

    print json.dumps(doc)
    print json.dumps(doc.jsonify()) # Jsonify will clean and validate output data

    # Create instance from dictionary
    doc = MyDoc.fromjson({'prop1': 'foo', 'prop2': 123})

    # would raise dicty.FieldError here
    doc = MyDoc.fromjson({'prop1': 123, 'prop2': 123})


Nested Objects
==============

 .. code-block:: python

    import dicty


    class Foo(dicty.DictObject):
        class Bar(dicty.DictObject):
            prop = dicty.StringField()

        bar = dicty.TypedObjectField(Bar)

    obj = Foo()
    obj.bar.prop = 123
    print obj # {'bar': {'prop': 123}}


.. _CornerApp: https://cornerapp.com/


Mongo-style key pathes
======================

Dicty allows to build key pathes that can be used to create mongo query:

 .. code-block:: python

    class Foo(dicty.DictObject):
        bar = dicty.Field('myBar')

    print Foo.bar         # 'myBar' full path to the item
    print Foo.bar.key     # 'myBar' only leaf key
    print Foo.bar.attname # 'bar' python attribute name


Nested object:

 .. code-block:: python

    class Bar(dicty.DictObject):
        foo = dicty.TypedObjectField(Foo)

    print Bar.foo            # 'foo'
    print Bar.foo.bar        # 'foo.myBar'

List of objects:

 .. code-block:: python

    class Bar(dicty.DictObject):
        items = dicty.TypedListField(Foo)

    print Bar.items.foo        # 'items.myBar' without index
    print Bar.items[0].foo     # 'items.0.myBar' indexed path

Dict of objects:

 .. code-block:: python

    class Bar(dicty.DictObject):
        items = dicty.TypedDictField(Foo)

    # With index
    print Bar.items['maurice'].bar  # 'items.maurice.myBar'

    # Would raise IndexError
    print Bar.items['x.y'].bar
