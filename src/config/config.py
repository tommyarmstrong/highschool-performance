"""Configuration for the project."""

import json
from pathlib import Path


def load_config(config_path: Path = Path("config.json")) -> dict:
    """Load the config file and return as a dictionary."""
    
    # Validate that the config file exists
    if not config_path.exists():
        raise FileNotFoundError(f"Config file {config_path} does not exist.")

    # Load the config file
    with open(config_path, "r") as f:
        config = json.load(f)

    # Validate that the config file is not empty
    if not config:
        raise ValueError(f"Config file {config_path} is empty.")

    return config


def main(config_path: Path = Path("config.json")) -> dict:
    return load_config(config_path)


if __name__ == "__main__":
    main()
