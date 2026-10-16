"""Configuration for the project."""

import json
from pathlib import Path

from data_models.config_models import ConfigModel
from shared_funcitons import logger

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def validate_config(config: dict) -> None:
    """Validate the config file."""

    # Validate that the schools are a dictionary
    if not isinstance(config["schools"], dict):
        raise ValueError("Schools must be a dictionary.")

    # Validate that the schools are not empty
    if not config["schools"]:
        raise ValueError("Schools must not be empty.")

    # Validate that the years are a list of integers
    years = config["years"]
    if not isinstance(years, list) or not all(isinstance(year, int) for year in years):
        raise ValueError("Years must be a list of integers.")


def _load_config(config_path: Path = CONFIG_PATH) -> dict:
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

    # Convert the URNs and years to integers
    config["schools"] = {int(urn): name for urn, name in config["schools"].items()}
    config["years"] = [int(year) for year in config["years"]]

    # Validate the config
    validate_config(config)

    logger.info(f"Config loaded from {config_path}")
    return config


def _dfe_institution_url(institution_level_data: dict) -> str:
    """Build the DfE institution-level data URL."""
    base_url: str = institution_level_data["url-base"].rstrip("/")
    url_path: str = institution_level_data["url-path"].strip("/")
    url_file: str = institution_level_data["url-file"].lstrip("/")
    return f"{base_url}/{url_path}/{url_file}"


def _dfe_urls(dfe_data: dict) -> dict[str, str]:
    """Map each dataset file name to its download URL."""
    return {
        entry["data-set"]: _dfe_institution_url(entry)
        for entry in dfe_data.values()
    }


def get_config(config_path: Path = CONFIG_PATH) -> ConfigModel:
    """Load the config once and return it as a ConfigModel."""
    config = _load_config(config_path)

    schools: dict[int, str] = config["schools"]
    project_root = Path(__file__).resolve().parents[2]

    return ConfigModel(
        schools_urns=schools,
        schools_names=list[str](schools.values()),
        years=config["years"],
        dfe_urls=_dfe_urls(config["data"]["dfe"]),
        project_root=project_root,
        raw_data_dir=project_root / "data" / "raw",
        processed_data_dir=project_root / "data" / "processed",
    )


def main(config_path: Path = CONFIG_PATH) -> ConfigModel:
    return get_config(config_path)


if __name__ == "__main__":
    main()
