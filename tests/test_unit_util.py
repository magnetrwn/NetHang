"""Tests for the util.py module."""

from os import path

import NetHang


def test_json_file_loading():
    """Does load_json_dict() work as expected?"""
    sample_path = path.join(path.dirname(path.abspath(__file__)), "sample.json")
    correct_dict = {
        "key1": "value1",
        "key2": "value2",
        "key3": [{"key311": "value311"}, {"key321": "value321", "key322": "value322"}],
    }
    test_dict = None
    try:
        test_dict = NetHang.util.load_json_dict("")
    except FileNotFoundError:
        pass
    assert test_dict is None
    assert NetHang.util.load_json_dict(sample_path) == correct_dict


def test_pretty_time():
    """Does prettify_time() generate correct time strings?"""
    assert NetHang.util.prettify_time(1) == "1 second"
    assert NetHang.util.prettify_time(59) == "59 seconds"
    assert NetHang.util.prettify_time(60) == "1 minute"
    assert NetHang.util.prettify_time(3540) == "59 minutes"
    assert NetHang.util.prettify_time(3600) == "1 hour"
    assert NetHang.util.prettify_time(86400) == "24 hours"
    assert NetHang.util.prettify_time(3661) == "1 hour, 1 minute, 1 second"
    assert NetHang.util.prettify_time(215999) == "59 hours, 59 minutes, 59 seconds"
