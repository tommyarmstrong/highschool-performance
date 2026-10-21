import logging
import time
from http.client import IncompleteRead
from pathlib import Path

import pandas as pd
import requests


"""
Shared functions for the project.
"""

""" Logging """
def setup_logging() -> logging.Logger:
    """Setup logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

logger = setup_logging()


""" Data """
def check_processed_data(file_path: Path) -> pd.DataFrame | None:
    """Check if the processed data already exists."""
    if file_path.exists():
        return read_dataframe(file_path)
    else:
        return None

        
def read_dataframe(path: Path) -> pd.DataFrame:
    """Load a pickled pandas DataFrame."""
    loaded = pd.read_pickle(path)
    if not isinstance(loaded, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame in {path}")
    return loaded


def download_file(url: str, dest: Path, retries: int = 3) -> None:
    """Stream a remote file to disk, retrying if the connection drops.

    Some data are served as CSV with chunked transfer encoding and no
    content length. Reading that response directly with pandas uses urllib,
    which raises IncompleteRead when the connection closes early.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")

    for attempt in range(1, retries + 1):
        try:
            with requests.get(
                url,
                stream=True,
                timeout=(30, 120),
                headers={"User-Agent": "highschool-performance"},
            ) as response:
                response.raise_for_status()
                with partial.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file.write(chunk)
            partial.replace(dest)
            return
        except (requests.RequestException, IncompleteRead, OSError) as error:
            partial.unlink(missing_ok=True)
            logger.warning(
                f"Download attempt {attempt}/{retries} failed for {url}: {error}"
            )
            if attempt == retries:
                raise
            time.sleep(2 ** (attempt - 1))


def download_raw_data(data_set_name: str, url: str, raw_data_dir: Path) -> pd.DataFrame:
    """Download the raw data."""
    csv_path: Path = raw_data_dir / f"{data_set_name}.csv"
    raw_data_path: Path = raw_data_dir / f"{data_set_name}_raw.pkl"

    try:
        download_file(url, csv_path, retries=3)
        df: pd.DataFrame = pd.read_csv(csv_path, low_memory=False)

        # Save the data
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        df.to_pickle(raw_data_path)

        logger.info(f"Saved data to {raw_data_path}")
        return df
    except Exception as e:
        logger.error(f"Error downloading data set '{data_set_name}' from {url}: {e}")
        raise e
    finally:
        csv_path.unlink(missing_ok=True)


def load_or_download_raw_data(data_set_name: str, url: str, raw_data_dir: Path) -> pd.DataFrame:
    """Load or download the raw data."""
    raw_data_path: Path = raw_data_dir / f"{data_set_name}_raw.pkl"
    try:
        df = read_dataframe(raw_data_path)
        logger.info(f"Loaded raw data set from {raw_data_path}")
        return df
    except FileNotFoundError:
        return download_raw_data(data_set_name, url, raw_data_dir)
    except Exception as e:
        logger.error(f"Error loading data set '{data_set_name}': {e}")
        raise e
