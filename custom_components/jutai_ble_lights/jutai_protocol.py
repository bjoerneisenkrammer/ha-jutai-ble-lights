"""Proprietary BLE protocol for JuTai / Lumineo LED light strings.

All commands are ASCII-encoded hex strings written to WRITE_CHAR_UUID.
The device expects the hex string as raw ASCII bytes (not binary).

Command structure:  574C54 | 02 | <cmd> | <payload>
  574C54  — fixed manufacturer prefix ("WLT" in ASCII)
  02      — fixed command-class byte
  <cmd>   — command identifier (11 = power, 09 = brightness)
  <payload> — command-specific data

Examples:
  ON:         574C54 02 11 01
  OFF:        574C54 02 11 02
  Brightness: 574C54 02 09 {HH} 00   (HH = 0-100 as hex, e.g. 50% → 32)
"""

WRITE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"


def _prefix():
    """Return the manufacturer prefix shared by every command."""
    return "574C54"


def build_on_cmd():
    """Build the command to turn the light on."""
    return f"{_prefix()}021101"


def build_off_cmd():
    """Build the command to turn the light off."""
    return f"{_prefix()}021102"


def build_brightness_cmd(value: int):
    """Build a brightness command for the given JuTai percentage (0–100).

    The value is clamped to the valid range and encoded as a
    zero-padded two-digit hex number.
    """
    value = max(0, min(value, 100))
    return f"{_prefix()}0209{value:02X}00"


def build_mode_cmd(mode: int):
    """Build an effect/pattern mode command.

    Reserved for future use — not yet exposed by the integration.
    """
    return f"{_prefix()}02{mode:02X}00"
