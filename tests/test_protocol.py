"""Tests for the JuTai command builders.

These need no Home Assistant, so they run even when the harness is absent.
"""

import pytest

from custom_components.jutai_ble_lights.jutai_protocol import (
    build_brightness_cmd,
    build_off_cmd,
    build_on_cmd,
)


def test_on_command():
    assert build_on_cmd() == "574C54021101"


def test_off_command():
    assert build_off_cmd() == "574C54021102"


@pytest.mark.parametrize(
    ("percent", "expected"),
    [
        (0, "574C5402090000"),
        (50, "574C5402093200"),
        (100, "574C5402096400"),
    ],
)
def test_brightness_command(percent, expected):
    assert build_brightness_cmd(percent) == expected


@pytest.mark.parametrize(
    ("percent", "expected"),
    [
        (-5, "574C5402090000"),
        (150, "574C5402096400"),
    ],
)
def test_brightness_command_clamps_out_of_range(percent, expected):
    assert build_brightness_cmd(percent) == expected
