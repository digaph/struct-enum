# StructEnum

`StructEnum` is a `str` enum whose members carry typed properties. Each member is a
[msgspec](https://github.com/msgspec/msgspec/) `Struct`, so the properties are checked and
cheap to encode and decode.

## Installation

```bash
pip install struct-enum
```

Requires Python 3.10 or later. msgspec is installed as a dependency.

## Example

```python
from struct_enum import StructEnum, StructEnumDef


class ColorDef(StructEnumDef, frozen=True):
    hex: str
    family: str


class Color(StructEnum):
    RED = ColorDef(hex="#e53935", family="warm")
    ORANGE = ColorDef(hex="#fb8c00", family="warm")
    BLUE = ColorDef(hex="#1e88e5", family="cool", value="azure")
    GREEN = ColorDef(hex="#43a047", family="cool")


Color.RED == "RED"              # the member name is the value by default
Color.BLUE == "azure"           # an explicit value overrides it
Color("azure") is Color.BLUE    # look up a member by its value
Color.RED.hex                   # spec fields are read directly on the member
Color.RED.spec.family           # the same field through .spec
```

## Nested members

A property can hold another `StructEnum` member. The nested member keeps its own
properties, so you can chain through them:

```python
class ShirtDef(StructEnumDef, frozen=True):
    color: Color
    sizes: tuple[str, ...]


class Shirt(StructEnum):
    CREW = ShirtDef(color=Color.RED, sizes=("S", "M", "L"))
    POLO = ShirtDef(color=Color.BLUE, sizes=("M", "L", "XL"))
    TEE = ShirtDef(color=Color.GREEN, sizes=("S", "M"), value="t-shirt")


Shirt.CREW.color is Color.RED   # the nested member itself
Shirt.CREW.color.hex            # and its properties, chained
```

## Filtering

`filter(**props)` returns the members whose properties match every given value. Filtering
on a nested member compares against the member itself, and a tuple property matches when it
contains the value:

```python
Color.filter(family="warm")     # [Color.RED, Color.ORANGE]
Shirt.filter(color=Color.BLUE)  # [Shirt.POLO]
Shirt.filter(sizes="XL")        # [Shirt.POLO]
Shirt.filter(sizes="S", color=Color.RED)  # [Shirt.CREW]
```

An unknown property raises `AttributeError`, so a misspelled name fails loudly instead of
returning nothing.

## Concepts

- **Member value.** A member's string value is its `value` field when set, and its name
  otherwise.
- **`StructEnumDef`.** The base for a member's Struct. It supplies the `value` field, so
  a subclass only declares its own properties. Subclasses inherit `frozen`.
- **`spec`.** Each member keeps its Struct as `member.spec`. A property can also be read
  directly on the member, as `member.field`.
- **`filter(**props)`.** Returns the members whose properties match all the given values,
  in definition order.

## Caveats

- A property whose name matches an attribute of `str` or `Enum`, such as `name` or
  `upper`, is shadowed on the member. Read it through `member.spec`.
- A member's Struct must have a `value` field. Subclassing `StructEnumDef` provides one.
  A plain `msgspec.Struct` without it fails when the enum is defined.
- Requires Python 3.10 or later and msgspec 0.21.0 or later. msgspec 0.20 and earlier
  cannot encode a `StructEnum` member nested in another Struct.

## Development

```bash
uv sync
uv run pytest
uv run mypy
```

The package ships type annotations (`py.typed`), so IDEs and type checkers use them when you
import `struct_enum`. `uv run mypy` checks the annotations.

## License

BSD 3-Clause. See [LICENSE](LICENSE).
