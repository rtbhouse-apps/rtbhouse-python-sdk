"""Tests for schema and it's utilities."""
from itertools import chain

import pytest

from rtbhouse_sdk.schema import GroupBy, Metric, Stats, to_camel_case


def to_snake_case(word: str) -> str:
    acc = []
    for char in word:
        if char.isupper():
            acc.append("_" + char.lower())
        else:
            acc.append(char)
    return "".join(acc)


@pytest.mark.parametrize(
    "word,expected",
    [
        ("one", "one"),
        ("one_two_seven", "oneTwoSeven"),
    ],
)
def test_to_camel_case(word: str, expected: str) -> None:
    assert to_camel_case(word) == expected


def test_stats_schema_is_up_to_date() -> None:
    """In case Metric or GroupBy gets updated we need to update Stats as well."""
    metric_plus_groupby_fields = {to_snake_case(f) for f in chain(Metric, GroupBy)}
    stats_fields = set(Stats.schema(False).get("properties").keys())  # type: ignore
    assert metric_plus_groupby_fields < stats_fields, "`Stats` schema needs an update"
