"""Configuration for the project."""

import json
from pathlib import Path

from data_models.config_models import ConfigModel

CatchmentDistances = dict[int, dict[str, float | None]]
SchoolCoords = dict[str, tuple[float, float]]

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
SCHOOLS_PATH = Path(__file__).resolve().parent / "schools.json"
CATCHMENT_DISTANCES_PATH = Path(__file__).resolve().parent / "catchment_distances.json"

PERFORMANCE_DATA_COLUMNS = [
    "time_period",
    "school",
    "A8 Average",
    "P8 Average",
    "P8 CI Lower",
    "P8 CI Upper",
    "KS2 Avg",
    "KS2 Low N",
    "KS2 High N",
    "KS2 Middle N",
    "KS2 Low",
    "KS2 Middle",
    "KS2 High",
    "A8 Low",
    "A8 Middle",
    "A8 High",
    "P8 Low",
    "P8 Low CI Lower",
    "P8 Low CI Upper",
    "P8 Middle",
    "P8 Middle CI Lower",
    "P8 Middle CI Upper",
    "P8 High",
    "P8 High CI Lower",
    "P8 High CI Upper",
    "Boys N",
    "Boys %",
    "A8 Boys",
    "P8 Boys",
    "P8 Boys CI Lower",
    "P8 Boys CI Upper",
    "Girls N",
    "Girls %",
    "A8 Girls",
    "P8 Girls",
    "P8 Girls CI Lower",
    "P8 Girls CI Upper"    
]

APPLICATIONS_COLUMNS = {
    "time_period": "time_period",
    "school": "school",
    "school_name": "school_name",
    "school_urn": "school_urn",
    "total_number_places_offered": "Total Offers",
    "times_put_as_any_preferred_school": "Total Applications",
    "times_put_as_1st_preference": "First Choice Applications",
    "times_put_as_2nd_preference": "Second Choice Applications",
    "times_put_as_3rd_preference": "Third Choice Applications",
    "number_1st_preference_offers": "First Choice Offers",
    "number_2nd_preference_offers": "Second Choice Offers",
    "number_3rd_preference_offers": "Third Choice Offers",
    "number_preferred_offers": "Preferred Offers",
}


def validate_config(config: dict) -> None:
    """Validate the config file."""

    # Validate that the years are a list of integers
    years = config["years"]
    if not isinstance(years, list) or not all(isinstance(year, int) for year in years):
        raise ValueError("Years must be a list of integers.")


def _load_json_config(config_path: Path = CONFIG_PATH) -> dict:
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


def _parse_years(config: dict) -> dict:
    """Convert the years to integers."""
    config["years"] = [int(year) for year in config["years"]]
    return config


def _load_schools(schools_path: Path = SCHOOLS_PATH) -> dict[int, dict[str, str]]:
    """Load schools as URN to name and address."""
    raw_schools: dict = _load_json_config(schools_path)
    if not isinstance(raw_schools, dict) or not raw_schools:
        raise ValueError("Schools must be a non-empty dictionary.")

    schools: dict[int, dict[str, str]] = {}
    names: set[str] = set()
    for urn, school in raw_schools.items():
        if not isinstance(school, dict):
            raise ValueError(f"School {urn} must be an object with a name and address.")

        name = school.get("name")
        address = school.get("address")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"School {urn} must have a name.")
        if not isinstance(address, str) or not address.strip():
            raise ValueError(f"School {urn} must have an address.")
        if name in names:
            raise ValueError(f"Duplicate school name: {name}.")

        names.add(name)
        schools[int(urn)] = {"name": name, "address": address}

    return schools


def _build_url(url_data: dict) -> str:
    """Join the base, path, and file of a DfE download URL."""
    return "/".join(
        url_data[part].strip("/")
        for part in ("url-base", "url-path", "url-file")
    )


def _dataset_urls(*entries: dict) -> dict[str, str]:
    """Map each dataset name to its download URL."""
    return {entry["data-set"]: _build_url(entry) for entry in entries}


def get_config(
    config_path: Path = CONFIG_PATH,
    schools_path: Path = SCHOOLS_PATH,
) -> ConfigModel:
    """Load the config once and return it as a ConfigModel."""
    config: dict = _parse_years(_load_json_config(config_path))

    # Validate the config
    validate_config(config)

    schools: dict[int, dict[str, str]] = _load_schools(schools_path)
    schools_urns: dict[int, str] = {
        urn: school["name"] for urn, school in schools.items()
    }
    school_addresses: dict[str, str] = {
        school["name"]: school["address"] for school in schools.values()
    }
    project_root = Path(__file__).resolve().parents[2]
    institutional_config = config["data"]["dfe"]["institution_level"]
    ks2_information_config = config["data"]["dfe"]["ks2_information"]
    applications_config = config["data"]["dfe"]["applications_2026"]
    census_config = config["data"]["dfe"]["census_2026"]
    census_years = config["census_years"]

    return ConfigModel(
        schools_urns=schools_urns,
        schools_names=list(schools_urns.values()),
        school_addresses=school_addresses,
        years=config["years"],
        institutional_urls=_dataset_urls(*institutional_config.values()),
        ks2_information_urls=_dataset_urls(ks2_information_config),
        applications_urls=_dataset_urls(applications_config),
        census_urls=_dataset_urls(census_config),
        census_years=census_years,
        project_root=project_root,
        raw_data_dir=project_root / "data" / "raw",
        processed_data_dir=project_root / "data" / "processed",
        charts_dir=project_root / "charts",
        report_dir=project_root / "reports",
        templates_dir=project_root / "templates"
    )


def get_catchment_distances(config_path: Path = CATCHMENT_DISTANCES_PATH) -> dict:
    """Load the catchment distances and return as a dictionary."""
    catchment_distances: dict = _load_json_config(config_path)
    return catchment_distances


def main(config_path: Path = CONFIG_PATH) -> ConfigModel:
    return get_config(config_path)


if __name__ == "__main__":
    main()
