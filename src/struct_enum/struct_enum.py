"""StructEnum: a str enum whose members carry a msgspec Struct.

Each member is written as ``NAME = SomeDef(...)``. The member's string value is the
Struct's ``value`` field when it is set, and the member name otherwise. The Struct is
available as ``member.spec``. Its fields are also readable directly on the member, as
``member.field``; ``member.spec.field`` keeps working too.

The mechanism: a metaclass wraps the class namespace, so that each Struct assignment
becomes a ``(value, spec)`` pair before Enum builds the members. The base ``__new__``
then creates the str member from ``value`` and keeps ``spec``.
"""

from enum import Enum, EnumMeta
from typing import Optional

import msgspec


class StructEnumDef(msgspec.Struct, frozen=True, kw_only=True):
    """Base for a member's Struct. It supplies the ``value`` field, so subclasses need not.

    kw_only lets subclasses add required fields after ``value``. Subclasses inherit the
    frozen setting from this class, so they need not repeat it.
    """

    value: Optional[str] = None  # None: the member name is the value


def _wrap_namespace(namespace):
    """Subclass the stdlib namespace so Struct values become (value, spec) pairs."""
    base = type(namespace)

    class _SpecNamespace(base):
        def __setitem__(self, key, value):
            if not key.startswith("_") and isinstance(value, msgspec.Struct):
                str_value = value.value if value.value is not None else key
                value = (str_value, value)
            super().__setitem__(key, value)

    namespace.__class__ = _SpecNamespace
    return namespace


class _StructEnumMeta(EnumMeta):
    @classmethod
    def __prepare__(metacls, cls, bases, **kwds):
        return _wrap_namespace(super().__prepare__(cls, bases, **kwds))


class StructEnum(str, Enum, metaclass=_StructEnumMeta):
    """Base for enums whose members carry a msgspec Struct as ``spec``."""

    spec: msgspec.Struct

    def __new__(cls, value, spec):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.spec = spec
        return obj

    @classmethod
    def filter(cls, **props):
        """Return the members whose spec matches every given property, in definition order.

        A property matches when the spec field equals the value. A tuple field matches
        when it contains the value. An unknown property raises AttributeError.
        """

        def matches(member):
            for key, wanted in props.items():
                actual = getattr(member.spec, key)
                if isinstance(actual, tuple):
                    if wanted not in actual:
                        return False
                elif actual != wanted:
                    return False
            return True

        return [member for member in cls if matches(member)]

    def __getattr__(self, name):
        # Runs only when normal lookup fails, so str and Enum attributes win over
        # spec fields. Read spec via object.__getattribute__ to avoid recursing here.
        return getattr(object.__getattribute__(self, "spec"), name)
