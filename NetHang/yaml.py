"""Functions to interact with YAML files, mostly configs"""


import yaml


def load_yaml_dict(file_path):
    """Load YAML configuration files"""
    with open(file_path, "r", encoding="ascii") as file:
        parsed = yaml.safe_load(file)
    return parsed or {}


def first_not_none(*args):
    """Returns the first non-None argument found"""
    for arg in args:
        if arg is not None:
            return arg
    return None
