import datetime
import re
import sys


class FieldError(ValueError):
    def __init__(self, path, message):
        super(FieldError, self).__init__(message)
        self.path = path

    def __str__(self):
        if self.path:
            return '{}: {}'.format(self.path, self.message)
        else:
            return self.message

    @classmethod
    def nested(cls, path, exc):
        if isinstance(exc, FieldError):
            if exc.path[:1] == '[':
                path = path + exc.path
            else:
                path = path + '.' + exc.path
        return cls(path, exc.message)


class DictyRuntimeError(Exception):
    pass


class cached_property(object):
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or func.__name__

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        value = self.func(instance)
        setattr(instance, self.name, value)
        return value


def base_with_metaclass(meta):
    def new_class(cls):
        return type.__new__(meta, cls.__name__, (cls,), {'__metaclass__': meta})
    return new_class


class JSONMetaObject(type):
    objects = {}

    def __new__(mcs, name, bases, attrs):
        fields = {}
        for key, value in attrs.iteritems():
            if isinstance(value, Field):
                if value.attname is None:
                    value.attname = key
                if value.name is None:
                    value.name = value.attname
                fields[key] = value
        attrs['_fields'] = fields
        obj = type.__new__(mcs, name, bases, attrs)
        mcs.register_object(obj)
        return obj

    @classmethod
    def register_object(cls, obj):
        canonical = '{}.{}'.format(obj.__module__, obj.__name__)
        cls.objects[canonical] = obj

    @classmethod
    def resolve_type(cls, type_name):
        try:
            return cls.objects[type_name]
        except KeyError:
            raise DictyRuntimeError(
                "Cannot resolve type {}".format(type_name))


@base_with_metaclass(JSONMetaObject)
class DictObject(dict):
    def __init__(self, **kwargs):
        self._shadow = {}
        for key, value in kwargs.iteritems():
            if key not in self._fields:
                raise AttributeError("Unknown field `{}` given".format(key))
            setattr(self, key, value)

    def hasattr(self, attname):
        return self._fields[attname].name in self

    def validate(self):
        for prop in self._fields.itervalues():
            prop.validate(self)

    def jsonize(self):
        json = {}
        for field in self._fields.itervalues():
            if field.name in self:
                json[field.name] = field.jsonize(self)
        return json

    @classmethod
    def fromjson(cls, json):
        obj = cls()
        obj.update(json)
        obj.validate()
        return obj


class Field(object):
    attname = None   # Python attribute name
    name = None      # Name as in JSON document

    def __init__(self, name=None, filters=(), optional=False,
                 default=None, default_func=None):
        self.name = name
        self.optional = optional
        self.filters = filters
        self._default = default
        self._default_func = default_func

    def __set__(self, obj, value):
        obj[self.name] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        try:
            return obj[self.name]
        except KeyError:
            value = self.getdefault(obj)
            # Store non-hashable object or objects returned by default_func()
            # Hard to understand implicit logic
            if (getattr(value, '__hash__', None) is None or
                self._default_func is not None):
                obj[self.name] = value
            return value

    def __delete__(self, obj):
        del obj[self.name]

    def getdefault(self, obj):
        if self._default_func is not None:
            return self._default_func(obj)
        if self.optional:
            return self._default
        raise self.not_set_error

    @property
    def not_set_error(self):
        return AttributeError("field {} is not set".format(self.attname))

    def fromjson(self, value):
        return value

    def run_filters(self, obj):
        value = self.fromjson(obj[self.name])
        for filter in self.filters:
            value = filter(value)
        obj[self.name] = value

    def validate(self, obj):
        if self.name in obj:
            try:
                self.run_filters(obj)
            except ValueError, e:
                _, _, tb = sys.exc_info()
                raise FieldError.nested(self.name, e), None, tb
        else:
            if not self.optional:
                raise FieldError(self.name, "Is required")

    def jsonize(self, obj):
        return obj[self.name]


class ShadowField(Field):
    def tojson(self, value):
        return value

    def run_filters(self, obj):
        value = self.fromjson(obj[self.name])
        for filter in self.filters:
            value = filter(value)
        obj._shadow[self.attname] = value

    def __set__(self, obj, value):
        json_value = self.tojson(value)
        obj._shadow[self.attname] = value
        obj[self.name] = json_value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        try:
            return obj._shadow[self.attname]
        except KeyError:
            if self.optional:
                return self._default
            raise self.not_set_error


class DatetimeField(ShadowField):
    format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, *args, **kwargs):
        self.format = kwargs.pop('format', self.format)
        super(DatetimeField, self).__init__(*args, **kwargs)

    def fromjson(self, value):
        if isinstance(value, datetime.datetime):
            return value
        return datetime.datetime.strptime(value, self.format)

    def tojson(self, value):
        return value.strftime(self.format)


class NativeDatetimeField(DatetimeField):
    def tojson(self, value):
        return value


class DateField(DatetimeField):
    format = '%Y-%m-%d'

    def fromjson(self, value):
        if isinstance(value, datetime.date):
            return value
        return super(DateField, self).fromjson(value).date()


class BaseTypedField(Field):
    def __init__(self, type, *args, **kwargs):
        if isinstance(type, basestring):
            self.type_reference = type
        else:
            self.type = type
        self.is_json_object = hasattr(type, 'fromjson')
        super(BaseTypedField, self).__init__(*args, **kwargs)

    @cached_property
    def type(self):
        return JSONMetaObject.resolve_type(self.type_reference)

    def instantiate(self, value):
        if self.is_json_object:
            return self.type.fromjson(value)
        return self.type(value)


class TypedObjectField(BaseTypedField):
    def getdefault(self, obj):
        value = self.type()
        obj[self.name] = value
        return value

    def fromjson(self, value):
        if not isinstance(value, dict):
            raise ValueError("must be dictionary")
        return self.instantiate(value)

    def jsonize(self, obj):
        return obj[self.name].jsonize()


class TypedListField(BaseTypedField):
    def fromjson(self, value):
        if not isinstance(value, list):
            raise ValueError("must be list")
        retval = []
        for no, item in enumerate(value):
            try:
                retval.append(self.instantiate(item))
            except ValueError, e:
                _, _, tb = sys.exc_info()
                raise FieldError.nested('[{}]'.format(no), e), None, tb
        return retval

    def getdefault(self, obj):
        value = []
        obj[self.name] = value
        return value

    def jsonize(self, obj):
        if self.name is None:
            return [i.jsonize() for i in obj]
        return [i.jsonize() for i in obj[self.name]]


class TypedDictField(BaseTypedField):
    def fromjson(self, value):
        if not isinstance(value, dict):
            raise ValueError("must be dict")
        retval = {}
        for key, item in value.iteritems():
            try:
                retval[key] = self.instantiate(item)
            except ValueError, e:
                _, _, tb = sys.exc_info()
                raise FieldError.nested('[{}]'.format(repr(key)), e), None, tb
        return retval

    def getdefault(self, obj):
        value = {}
        obj[self.name] = value
        return value

    def jsonize(self, obj):
        return {key: self.type.jsonize(value)
                for key, value in obj[self.name].iteritems()}


class BasicTypeField(Field):
    def __init__(self, types, *args, **kwargs):
        self.types = types if type(types) in (tuple, list) else (types,)
        super(BasicTypeField, self).__init__(*args, **kwargs)

    def fromjson(self, value):
        # XXX
        if value is None and self.optional:
            return None
        if type(value) not in self.types:
            raise ValueError("Must be of {} type got {} instead".format(
                self.types, type(value)))
        return value


class IntegerField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__((int, long), *args, **kwargs)


class NumberField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(NumberField, self).__init__((int, long, float), *args, **kwargs)


class FloatField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__((float,), *args, **kwargs)


class StringField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(StringField, self).__init__((unicode, str), *args, **kwargs)


class RegexpStringField(StringField):
    regexp = None

    def __init__(self, *args, **kwargs):
        if 'regexp' in kwargs:
            regexp = kwargs.pop('regexp')
            if isinstance(regexp, basestring):
                regexp = re.compile(regexp)
            self.regexp = regexp
        super(RegexpStringField, self).__init__(*args, **kwargs)

    def fromjson(self, value):
        value = super(RegexpStringField, self).fromjson(value)
        if self.regexp is not None:
            if not self.regexp.match(value):
                raise ValueError("Does not match regular expression")
        return value


class ListField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__((list,), *args, **kwargs)

    def getdefault(self, obj):
        return []


class DictField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(DictField, self).__init__((dict,), *args, **kwargs)

    def getdefault(self, obj):
        return {}


class BooleanField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__((bool,), *args, **kwargs)
