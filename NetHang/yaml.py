"""Functions to interact with YAML files, mostly configs"""


import yaml


def load_yaml_dict(file_path):
    """Load YAML configuration files"""
    with open(file_path, "r", encoding="ascii") as file:
        parsed = yaml.safe_load(file)
    return parsed or {}
