# src/config_loader.py

import yaml
import os


def load_config():
    root_path = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(root_path, "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError("config.yaml not found in project root.")

    with open(config_path, "r") as file:
        return yaml.safe_load(file)