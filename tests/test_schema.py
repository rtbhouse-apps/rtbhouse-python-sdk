"""Tests for schema and it's utilities."""
from itertools import chain

from inflection import underscore

from rtbhouse_sdk.schema import Stats, StatsGroupBy, StatsMetric


def test_stats_schema_is_up_to_date() -> None:
    """In case Metric or GroupBy gets updated we need to update Stats as well."""
    metric_plus_groupby_fields = {underscore(f) for f in chain(StatsMetric, StatsGroupBy)}
    stats_fields = set(Stats.schema(False).get("properties").keys())  # type: ignore
    assert metric_plus_groupby_fields < stats_fields, "`Stats` schema needs an update"
