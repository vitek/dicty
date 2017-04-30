import datetime
import re
import sys

import six


class FieldError(Exception):
    def __init__(self, message, path=None):
        super(FieldError, self).__init__(message)
        self.path = path

    def __str__(self):
        if self.path:
            return '{}: {}'.format(self.path, self.args[0])
        else:
            return self.args[0]

    def add_path_info(self, path):
        if self.path:
            if self.path[:1] == '[':
                path = path + self.path
            else:
                path = path + '.' + self.path
        self.path = path

    @classmethod
    def raise_from(cls, exc, path=None):
        obj = cls(str(exc), path)
        if six.PY3:
            six.raise_from(obj, exc)
        else:
            _, _, tb = sys.exc_info()
            six.reraise(cls, obj, tb)


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


class DictyPath(six.text_type):
    def __getattr__(self, attname):
        top = self._field
        if isinstance(top, BaseTypedField):
            field = top.type._fields[attname]
        else:
            field = top._fields[attname]
        return self._new('{}.{}'.format(self, field.key), field)

    @classmethod
    def _new(cls, value, field):
        # TODO: implement object caching and check for name clashing
        obj = cls(value)
        obj.key = field.key
        obj.attname = field.attname
        obj._field = field
        return obj


class DictyItemPath(DictyPath):
    def __iter__(self):
        return iter(six.text_type(self))

    def __getitem__(self, key):
        if type(key) in (six.text_type, six.binary_type) and '.' in key:
            raise IndexError('Dot is not allowed in key')
        return self._new('{}.{}'.format(self, key), self._field)


def base_with_metaclass(meta):
    def new_class(cls):
        return type.__new__(meta, cls.__name__, (cls,), {})
    return new_class


class JSONMetaObject(type):
    objects = {}

    def __new__(mcs, name, bases, attrs):
        fields = []
        lookup_attrs = [attrs]
        for base in bases:
            if issubclass(base, DictObject):
                fields.extend(getattr(base, '_fields', {}).values())
            else:
                lookup_attrs.append(base.__dict__)

        for type_attrs in lookup_attrs:
            for attname, value in six.iteritems(type_attrs):
                if isinstance(value, Field):
                    if value.attname is None:
                        value.attname = attname
                    if value.key is None:
                        value.key = value.attname
                    fields.append(value)

        keys_seen = set()
        fields_index = {}
        for field in fields:
            if field.attname in fields_index or field.key in keys_seen:
                raise DictyRuntimeError(
                    'Duplicate declaration of {} field with key {}'.format(
                        repr(field.attname), repr(field.key)))
            fields_index[field.attname] = field
            keys_seen.add(field.key)
        attrs['_fields'] = fields_index
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
                'Cannot resolve type {}'.format(type_name))


@base_with_metaclass(JSONMetaObject)
class DictObject(dict):
    def __init__(self, **kwargs):
        self._shadow = {}
        for key, value in six.iteritems(kwargs):
            if key not in self._fields:
                raise AttributeError('Unknown field `{}` given'.format(key))
            setattr(self, key, value)

    def hasattr(self, attname):
        return self._fields[attname].key in self

    def validate(self):
        for prop in six.itervalues(self._fields):
            prop.validate(self)

    def jsonize(self):
        json = {}
        for field in six.itervalues(self._fields):
            if field.key in self:
                json[field.key] = field.jsonize(self)
        return json

    @classmethod
    def fromjson(cls, json):
        obj = cls()
        obj.update(json)
        obj.validate()
        return obj


class Field(object):
    attname = None   # Python attribute name
    key = None       # Dictionary key
    path_class = DictyPath

    def __init__(self, key=None, filters=(), optional=False,
                 default=None, default_func=None):
        self.key = key
        self.optional = optional
        self.filters = filters
        self._default = default
        self._default_func = default_func

    def __set__(self, obj, value):
        obj[self.key] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self.path_class._new(self.key, self)
        try:
            return obj[self.key]
        except KeyError:
            value = self.getdefault(obj)
            # Store non-hashable object or objects returned by default_func()
            # Hard to understand implicit logic
            if (getattr(value, '__hash__', None) is None or
                self._default_func is not None):
                obj[self.key] = value
            return value

    def __delete__(self, obj):
        del obj[self.key]

    def getdefault(self, obj):
        if self._default_func is not None:
            return self._default_func(obj)
        if self.optional:
            return self._default
        raise self.not_set_error

    @property
    def not_set_error(self):
        return AttributeError('field {} is not set'.format(self.attname))

    def fromjson(self, value):
        return value

    def run_filters(self, obj):
        value = self.fromjson(obj[self.key])
        for filter in self.filters:
            value = filter(value)
        obj[self.key] = value

    def validate(self, obj):
        if self.key in obj:
            try:
                self.run_filters(obj)
            except ValueError as exc:
                FieldError.raise_from(exc, self.key)
            except FieldError as exc:
                exc.add_path_info(self.key)
                raise
        else:
            if not self.optional:
                raise FieldError('Is required', self.key)

    def jsonize(self, obj):
        return obj[self.key]


class ShadowField(Field):
    def tojson(self, value):
        return value

    def run_filters(self, obj):
        value = self.fromjson(obj[self.key])
        for filter in self.filters:
            value = filter(value)
        obj._shadow[self.attname] = value

    def __set__(self, obj, value):
        json_value = self.tojson(value)
        obj._shadow[self.attname] = value
        obj[self.key] = json_value

    def __get__(self, obj, type=None):
        if obj is None:
            return self.path_class._new(self.key, self)
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
        return datetime.datetime.strptime(value, self.format)

    def tojson(self, value):
        return value.strftime(self.format)


class DateField(DatetimeField):
    format = '%Y-%m-%d'

    def fromjson(self, value):
        return super(DateField, self).fromjson(value).date()


class BaseTypedField(Field):
    def __init__(self, type, *args, **kwargs):
        if isinstance(type, six.string_types):
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
        try:
            return self.type(value)
        except ValueError as exc:
            FieldError.raise_from(exc)


class TypedObjectField(BaseTypedField):
    def getdefault(self, obj):
        value = self.type()
        obj[self.key] = value
        return value

    def fromjson(self, value):
        if not isinstance(value, dict):
            raise FieldError('must be dictionary')
        return self.instantiate(value)

    def jsonize(self, obj):
        return obj[self.key].jsonize()


class TypedListField(BaseTypedField):
    path_class = DictyItemPath

    def fromjson(self, value):
        if not isinstance(value, list):
            raise FieldError('must be list')
        retval = []
        for no, item in enumerate(value):
            try:
                retval.append(self.instantiate(item))
            except FieldError as exc:
                exc.add_path_info('[{}]'.format(no))
                raise
        return retval

    def getdefault(self, obj):
        value = []
        obj[self.key] = value
        return value

    def jsonize(self, obj):
        if self.key is None:
            return [i.jsonize() for i in obj]
        return [i.jsonize() for i in obj[self.key]]


class TypedDictField(BaseTypedField):
    path_class = DictyItemPath

    def fromjson(self, value):
        if not isinstance(value, dict):
            raise FieldError('must be dict')
        retval = {}
        for key, item in six.iteritems(value):
            try:
                retval[key] = self.instantiate(item)
            except FieldError as exc:
                exc.add_path_info('[{}]'.format(repr(key)))
                raise
        return retval

    def getdefault(self, obj):
        value = {}
        obj[self.key] = value
        return value

    def jsonize(self, obj):
        return {key: self.type.jsonize(value)
                for key, value in six.iteritems(obj[self.key])}


class BasicTypeField(Field):
    def __init__(self, types, *args, **kwargs):
        self.types = types if type(types) in (tuple, list) else (types,)
        super(BasicTypeField, self).__init__(*args, **kwargs)

    def fromjson(self, value):
        # XXX
        if value is None and self.optional:
            return None
        if type(value) not in self.types:
            raise FieldError(
                'Must be of {} type got {} instead'.format(
                    self.types, type(value)
                )
            )
        return value


class IntegerField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(six.integer_types, *args, **kwargs)


class NumberField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(NumberField, self).__init__(
            six.integer_types + (float,), *args, **kwargs)


class FloatField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__((float,), *args, **kwargs)


class StringField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(StringField, self).__init__(
            (six.text_type, six.binary_type), *args, **kwargs)


class RegexpStringField(StringField):
    regexp = None

    def __init__(self, *args, **kwargs):
        if 'regexp' in kwargs:
            regexp = kwargs.pop('regexp')
            if isinstance(regexp, six.string_types):
                regexp = re.compile(regexp)
            self.regexp = regexp
        super(RegexpStringField, self).__init__(*args, **kwargs)

    def fromjson(self, value):
        value = super(RegexpStringField, self).fromjson(value)
        if self.regexp is not None:
            if not self.regexp.match(value):
                raise FieldError('Does not match regular expression')
        return value


class NativeDatetimeField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(NativeDatetimeField, self).__init__(
            (datetime.datetime,), *args, **kwargs)


class NativeDateField(BasicTypeField):
    def __init__(self, *args, **kwargs):
        super(NativeDateField, self).__init__((datetime.date,), *args, **kwargs)


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
