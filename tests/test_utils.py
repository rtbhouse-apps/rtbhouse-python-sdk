"""Tests for utilities"""

import pytest

from rtbhouse_sdk._utils import camelize, underscore


@pytest.mark.parametrize(
    ["input_string", "uppercase_first_letter", "expected_result"],
    [
        ("FooBar", True, "FooBar"),
        ("FooBar", False, "fooBar"),
        ("foo_bar", True, "FooBar"),
        ("foo_bar", False, "fooBar"),
        ("foo bar", True, "Foo bar"),
        ("foo bar", False, "foo bar"),
        ("a1b2", True, "A1b2"),
        ("FOOBAR", True, "FOOBAR"),
        ("foobar", False, "foobar"),
        ("FOOBAR", False, "fOOBAR"),
        ("_foo_bar_", True, "_fooBar_"),
        ("_foo_bar_", False, "_fooBar_"),
        ("___foo___bar___", True, "__foo_Bar__"),
        ("___foo___bar___", False, "__foo_Bar__"),
        ("_", True, "_"),
        ("_", False, "_"),
        ("", True, ""),
        ("", False, ""),
        ("ab_12_c2__d", True, "Ab12C2_d"),
        (
            "ThisIsOne___messed up string. Can we Really camel-case It ?##",
            True,
            "ThisIsOne_Messed up string. Can we Really camel-case It ?##",
        ),
        (
            "ThisIsOne___messed up string. Can we Really camel-case It ?##",
            False,
            "thisIsOne_Messed up string. Can we Really camel-case It ?##",
        ),
    ],
)
def test_camelize(input_string: str, uppercase_first_letter: bool, expected_result: str) -> None:
    assert camelize(input_string, uppercase_first_letter=uppercase_first_letter) == expected_result


@pytest.mark.parametrize(
    ["input_string", "expected_result"],
    [
        ("FooBar", "foo_bar"),
        ("foo_bar", "foo_bar"),
        ("Foo bar", "foo bar"),
    ],
)
def test_underscore(input_string: str, expected_result: str) -> None:
    assert underscore(input_string) == expected_result
