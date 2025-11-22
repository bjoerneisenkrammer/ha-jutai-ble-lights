WRITE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"


def _prefix() -> str:
    """JuTai devices always have the fixed prefix 574C54."""
    return "574C54"


def build_on_cmd() -> str:
    return f"{_prefix()}021101"


def build_off_cmd() -> str:
    return f"{_prefix()}021102"


def build_brightness_cmd(value: int) -> str:
    value = max(0, min(value, 100))
    hex_val = f"{value:02X}"
    return f"{_prefix()}0209{hex_val}00"


def build_mode_cmd(mode: int) -> str:
    if not (1 <= mode <= 8):
        raise ValueError("Mode must be between 1 and 8")
    return f"{_prefix()}02{mode:02X}00"
