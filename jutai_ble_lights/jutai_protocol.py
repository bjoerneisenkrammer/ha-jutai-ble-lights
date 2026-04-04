WRITE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

def _prefix():
    return "574C54"

def build_on_cmd():
    return f"{_prefix()}021101"

def build_off_cmd():
    return f"{_prefix()}021102"

def build_brightness_cmd(value: int):
    value = max(0, min(value, 100))
    return f"{_prefix()}0209{value:02X}00"

def build_mode_cmd(mode: int):
    return f"{_prefix()}02{mode:02X}00"
