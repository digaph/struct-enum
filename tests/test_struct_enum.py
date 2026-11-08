import msgspec
from typing import Optional
import pytest

from struct_enum import StructEnum, StructEnumDef


class CurrencyDef(msgspec.Struct, frozen=True):
    symbol: str
    decimals: int
    value: Optional[str] = None


class Currency(StructEnum):
    EUR = CurrencyDef(symbol="€", decimals=2)
    JPY = CurrencyDef(symbol="¥", decimals=0, value="yen")


def test_value_defaults_to_member_name():
    assert Currency.EUR == "EUR"
    assert Currency.EUR.value == "EUR"


def test_value_override_is_used():
    assert Currency.JPY == "yen"
    assert Currency.JPY.value == "yen"


def test_spec_attributes():
    assert Currency.EUR.spec.symbol == "€"
    assert Currency.EUR.spec.decimals == 2
    assert Currency.JPY.spec.value == "yen"


def test_lookup_by_value():
    assert Currency("EUR") is Currency.EUR
    assert Currency("yen") is Currency.JPY


def test_iteration_order():
    assert list(Currency) == [Currency.EUR, Currency.JPY]


def test_missing_struct_field_is_rejected():
    # The Struct rejects the missing field when the member is defined.
    with pytest.raises(TypeError):
        CurrencyDef(symbol="$")


def test_spec_fields_are_reachable_directly_on_member():
    assert Currency.EUR.symbol == "€"
    assert Currency.EUR.decimals == 2
    assert Currency.JPY.decimals == 0


def test_unknown_attribute_still_raises():
    with pytest.raises(AttributeError):
        Currency.EUR.no_such_field


class CountryDef(msgspec.Struct, frozen=True):
    code: str
    currency: Currency
    value: Optional[str] = None


class Country(StructEnum):
    NL = CountryDef(code="NL", currency=Currency.EUR)
    JP = CountryDef(code="JP", currency=Currency.JPY)


def test_spec_can_hold_another_struct_enum():
    assert Country.NL.spec.currency is Currency.EUR
    assert Country.JP.spec.currency is Currency.JPY


def test_nested_struct_enum_is_reachable_directly_on_member():
    assert Country.NL.currency is Currency.EUR
    assert Country.NL.currency.symbol == "€"


def test_nested_struct_enum_round_trips_through_msgspec():
    encoded = msgspec.json.encode(Country.JP.spec)
    decoded = msgspec.json.decode(encoded, type=CountryDef)
    assert decoded.currency is Currency.JPY


class ListingDef(msgspec.Struct, frozen=True):
    size: str
    regions: tuple[str, ...] = ()
    value: Optional[str] = None


class Listing(StructEnum):
    ALPHA = ListingDef(size="large", regions=("EU", "US"))
    BETA = ListingDef(size="small", regions=("EU",))
    GAMMA = ListingDef(size="large", regions=("ASIA",))


def test_filter_by_scalar_property():
    assert Listing.filter(size="large") == [Listing.ALPHA, Listing.GAMMA]


def test_filter_matches_when_a_tuple_property_contains_the_value():
    assert Listing.filter(regions="EU") == [Listing.ALPHA, Listing.BETA]


def test_filter_combines_properties_with_and():
    assert Listing.filter(size="large", regions="EU") == [Listing.ALPHA]


def test_filter_with_no_match_is_empty():
    assert Listing.filter(size="huge") == []


def test_filter_unknown_property_raises():
    with pytest.raises(AttributeError):
        Listing.filter(colour="red")


class PlanDef(StructEnumDef, frozen=True):
    symbol: str


class Plan(StructEnum):
    BASIC = PlanDef(symbol="b")
    PRO = PlanDef(symbol="p", value="professional")


def test_struct_enum_def_value_defaults_to_none():
    assert StructEnumDef().value is None


def test_subclass_with_required_fields_gets_value_by_default():
    assert PlanDef(symbol="x").value is None


def test_member_without_value_uses_member_name():
    assert Plan.BASIC == "BASIC"
    assert Plan.PRO == "professional"
    assert Plan.PRO.symbol == "p"
