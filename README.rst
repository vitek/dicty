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
