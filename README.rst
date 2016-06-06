Sample usage
============


 .. code-block:: python

    import jsonobject


    class MyDoc(jsonobject.DictObject):
        prop1 = jsonobject.StringField()
        prop2 = jsonobject.IntegerField()


    doc = MyDoc(prop1='foo', prop2=123)
    print doc.prop1
    print doc['prop2']

    doc = MyDoc.fromjson({'prop1': 'foo', 'prop2': 123})

    # would raise jsonobject.FieldError here
    doc = MyDoc.fromjson({'prop1': 123, 'prop2': 123})


Nested Objects
==============

 .. code-block:: python

    import jsonobject


    class Foo(jsonobject.DictObject):
        class Bar(jsonobject.DictObject):
            prop = jsonobject.StringField()

        bar = jsonobject.TypedObjectField(Bar)

    obj = Foo()
    obj.bar.prop = 123
    print obj # {'bar': {'prop': 123}}
