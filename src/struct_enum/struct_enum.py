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
from typing import Any, MutableMapping, Optional, TypeVar

import msgspec

_E = TypeVar("_E", bound="StructEnum")


class StructEnumDef(msgspec.Struct, frozen=True, kw_only=True):
    """Base for a member's Struct. It supplies the ``value`` field, so subclasses need not.

    kw_only lets subclasses add required fields after ``value``. Subclasses inherit the
    frozen setting from this class, so they need not repeat it.
    """

    value: Optional[str] = None  # None: the member name is the value


def _wrap_namespace(namespace: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Subclass the stdlib namespace so Struct values become (value, spec) pairs.

    The namespace's class is replaced at runtime, which mypy cannot follow, so the
    subclass is built from a value typed Any.
    """
    base: Any = type(namespace)

    class _SpecNamespace(base):  # type: ignore[misc]
        def __setitem__(self, key: str, value: Any) -> None:
            if not key.startswith("_") and isinstance(value, msgspec.Struct):
                struct_value: Optional[str] = getattr(value, "value")
                str_value = struct_value if struct_value is not None else key
                value = (str_value, value)
            super().__setitem__(key, value)

    namespace.__class__ = _SpecNamespace
    return namespace


class _StructEnumMeta(EnumMeta):
    @classmethod
    def __prepare__(  # type: ignore[override]
        metacls, cls: str, bases: tuple[type, ...], **kwds: Any
    ) -> MutableMapping[str, Any]:
        return _wrap_namespace(super().__prepare__(cls, bases, **kwds))


class StructEnum(str, Enum, metaclass=_StructEnumMeta):
    """Base for enums whose members carry a msgspec Struct as ``spec``."""

    # The member's Def instance. Typed Any because each enum's Def class has its own fields.
    spec: Any

    # spec defaults to None only so type checkers accept lookups such as Currency("EUR").
    # Members are always created with a spec.
    def __new__(cls, value: str, spec: Any = None) -> "StructEnum":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.spec = spec
        return obj

    @classmethod
    def filter(cls: type[_E], **props: Any) -> list[_E]:
        """Return the members whose spec matches every given property, in definition order.

        A property matches when the spec field equals the value. A tuple field matches
        when it contains the value. An unknown property raises AttributeError.
        """

        def matches(member: _E) -> bool:
            for key, wanted in props.items():
                actual = getattr(member.spec, key)
                if isinstance(actual, tuple):
                    if wanted not in actual:
                        return False
                elif actual != wanted:
                    return False
            return True

        return [member for member in cls if matches(member)]

    def __getattr__(self, name: str) -> Any:
        # Runs only when normal lookup fails, so str and Enum attributes win over
        # spec fields. Read spec via object.__getattribute__ to avoid recursing here.
        return getattr(object.__getattribute__(self, "spec"), name)
