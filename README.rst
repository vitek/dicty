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

If you don't like naming scheme in your JSON objects, API, protocol, for
instance you don't want to use camel-case names in Python. You can choose
whatever python name you like and manually specify dictionary key:

 .. code-block:: python

    class Foo(dicty.DictObject):
        prop_foo = dicty.Field('propFoo')

    obj = Foo(prop_foo=123)
    obj = Foo.fromjson({'propFoo': 123})
    obj.prop_foo
    obj['propFoo']


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

`NumberField`

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
