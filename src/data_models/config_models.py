from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConfigModel:
    schools_urns: dict[int, str]
    schools_names: list[str]
    years: list[int]
    institutional_urls: dict[str, str]
    ks2_information_urls: dict[str, str]
    project_root: Path
    raw_data_dir: Path
    processed_data_dir: Path


