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