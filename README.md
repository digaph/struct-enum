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


class CurrencyDef(StructEnumDef, frozen=True):
    symbol: str
    decimals: int


class Currency(StructEnum):
    EUR = CurrencyDef(symbol="€", decimals=2)
    JPY = CurrencyDef(symbol="¥", decimals=0, value="yen")


Currency.EUR == "EUR"            # the member name is the value by default
Currency.JPY == "yen"            # an explicit value overrides it
Currency("yen") is Currency.JPY  # look up a member by its value
Currency.EUR.symbol              # spec fields are read directly on the member
Currency.EUR.spec.decimals       # the same field through .spec
Currency.filter(decimals=2)      # [Currency.EUR]
```

## Concepts

- **Member value.** A member's string value is its `value` field when set, and its name
  otherwise.
- **`StructEnumDef`.** The base for a member's Struct. It supplies the `value` field, so
  a subclass only declares its own properties. Subclasses inherit `frozen`.
- **`spec`.** Each member keeps its Struct as `member.spec`. A property can also be read
  directly on the member, as `member.field`.
- **`filter(**props)`.** Returns the members whose properties match all the given
  values, in definition order. A tuple property matches when it contains the value. An
  unknown property raises `AttributeError`.

## Caveats

- A property whose name matches an attribute of `str` or `Enum`, such as `name` or
  `upper`, is shadowed on the member. Read it through `member.spec`.
- A member's Struct must have a `value` field. Subclassing `StructEnumDef` provides one.
  A plain `msgspec.Struct` without it fails when the enum is defined.
- Requires Python 3.10 or later and `msgspec` 0.21.0 or later. msgspec 0.20 and earlier cannot encode a `StructEnum` member nested in another Struct.

## Development

```bash
uv sync
uv run pytest
```

## License

BSD 3-Clause. See [LICENSE](LICENSE).
