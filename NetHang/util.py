"""Utility functions"""


import sys
import signal
import json


def load_json_dict(file_path):
    """Load JSON configuration or data files, crash on error."""
    with open(file_path, "r", encoding="ascii") as file:
        try:
            parsed = json.load(file)
        except json.decoder.JSONDecodeError as error:
            sys.exit(error.args[1])
    return parsed or {}


def first_not_none(*args):
    """Returns the first non-None argument found"""
    for arg in args:
        if arg is not None:
            return arg
    return None


def timeout_handler(signum, frame):
    """Function to call on timeout signal."""
    raise TimeoutError("Timeout occurred")


def timeout_in(seconds):
    """Raise timeout signal in seconds."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)


def timeout_kill():
    """Kill timeout timer."""
    signal.alarm(0)


def run_with_timeout(seconds, code_block):
    """Run function, but raise on timeout."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        code_block()
    except TimeoutError:
        pass
    finally:
        signal.alarm(0)


def prettify_time(seconds):
    """Make time durations prettier."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        time_parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
    if seconds > 0:
        time_parts.append(f"{seconds} {'second' if seconds == 1 else 'seconds'}")
    return ", ".join(time_parts)
