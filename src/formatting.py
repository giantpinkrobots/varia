import re
from collections.abc import Callable

def escape_special_characters(string):
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', string).replace("&", "&amp;")

def format_percentage(value, translate: Callable[[str], str] = str):
    return translate("{number}%").replace("{number}", str(round(float(value))))

def format_speed(bytes_per_second, translate: Callable[[str], str] = str):
    value = float(bytes_per_second)
    if value == 0:
        return f"0{translate(' B/s')}"
    if value < 1024:
        return f"{round(value, 2)}{translate(' B/s')}"
    if value < 1024 * 1024:
        return f"{round(value / 1024, 2)}{translate(' KB/s')}"
    if value < 1024 * 1024 * 1024:
        return f"{round(value / (1024 * 1024), 2)}{translate(' MB/s')}"
    return f"{round(value / (1024 * 1024 * 1024), 2)}{translate(' GB/s')}"

def format_binary_size(size):
    value = float(size)
    for divisor, unit in (
        (1024 ** 3, "GiB"),
        (1024 ** 2, "MiB"),
        (1024, "KiB"),
    ):
        if value >= divisor:
            return f"{round(value / divisor, 2)} {unit}"
    return f"{int(value) if value.is_integer() else value} B"

def format_eta(seconds, unknown="∞"):
    try:
        total_seconds = abs(int(seconds))
    except (TypeError, ValueError, OverflowError):
        return unknown

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def parse_ytdlp_percentage(value):
    cleaned = escape_special_characters(str(value)).replace(" ", "").replace("%", "")
    return float(cleaned)

def parse_ytdlp_speed(value):
    cleaned = escape_special_characters(str(value)).replace("i", "").strip()
    match = re.fullmatch(r"([\d.]+)\s*([KMGT]?B)/s", cleaned, re.IGNORECASE)
    if match is None:
        return None

    amount = float(match.group(1))
    unit = match.group(2).upper()
    multiplier = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }[unit]
    return amount * multiplier

def format_filesize(filesize):
    try:
        if filesize is None:
            filesize = 0

        if isinstance(filesize, str):
            filesize = float(filesize) if filesize.strip() != "" else 0
        filesize = float(filesize)

    except Exception:
        filesize = 0

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if filesize < 1024.0:
            return f"{filesize:.2f} {unit}"
        filesize /= 1024.0

    return f"{filesize:.2f} TB"

def format_bitrate(bitrate):
    try:
        if bitrate is None:
            return None

        if isinstance(bitrate, str):
            if bitrate.strip() == "":
                return None
            bitrate = float(bitrate)

        bitrate = float(bitrate)

        # Assume kbps for bitrate
        if bitrate >= 1000:
            return f"{bitrate/1000:.2f} Mbps"
        else:
            return f"{int(round(bitrate))} kbps"

    except Exception:
        return None