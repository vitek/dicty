import datetime

import pytest

import dicty


def test_datetime_field():
    class Object(dicty.DictObject):
        bday = dicty.DatetimeField(name='bDay')

    obj = Object(bday=datetime.datetime(1985, 6, 12, 11, 22, 33))
    assert obj == {'bDay': '1985-06-12 11:22:33'}
    assert obj.bday == datetime.datetime(1985, 6, 12, 11, 22, 33)

    obj = Object.fromjson({'bDay': '1985-06-12 11:22:33'})
    assert obj == {'bDay': '1985-06-12 11:22:33'}
    assert obj.bday == datetime.datetime(1985, 6, 12, 11, 22, 33)


def test_date_field():
    class Object(dicty.DictObject):
        bday = dicty.DateField(name='bDay')

    obj = Object()
    obj.bday = datetime.date(1985, 6, 12)
    assert obj == {'bDay': '1985-06-12'}

    obj = Object(bday=datetime.date(1985, 6, 12))
    assert obj == {'bDay': '1985-06-12'}
    assert obj.bday == datetime.date(1985, 6, 12)

    obj = Object.fromjson({'bDay': '1985-06-12'})
    assert obj == {'bDay': '1985-06-12'}
    assert obj.bday == datetime.date(1985, 6, 12)

def test_native_datetime():
    class Object(dicty.DictObject):
        bday = dicty.NativeDatetimeField(name='bDay')

    obj = Object.fromjson({'bDay': datetime.datetime(1985, 6, 12, 11, 22, 33)})
    assert obj == {'bDay': datetime.datetime(1985, 6, 12, 11, 22, 33)}
    assert obj.bday == datetime.datetime(1985, 6, 12, 11, 22, 33)


def test_native_date():
    class Object(dicty.DictObject):
        bday = dicty.NativeDateField(name='bDay')

    obj = Object.fromjson({'bDay': datetime.date(1985, 6, 12)})
    assert obj == {'bDay': datetime.date(1985, 6, 12)}
    assert obj.bday == datetime.date(1985, 6, 12)
