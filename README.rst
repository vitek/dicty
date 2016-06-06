Sample usage
============


 .. code-block:: python

    import dicty


    class MyDoc(dicty.DictObject):
        prop1 = dicty.StringField()
        prop2 = dicty.IntegerField()


    doc = MyDoc(prop1='foo', prop2=123)
    print doc.prop1
    print doc['prop2']

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
