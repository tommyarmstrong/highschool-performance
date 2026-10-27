import shutil
import tempfile
import time
from pathlib import Path

import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from shared_funcitons import logger

_MAC_CHROME_PATHS = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium",
)


def _find_chrome() -> str | None:
    """Return a Chrome or Chromium binary on PATH or in a macOS app bundle."""
    for name in ("chromium", "chromium-browser", "google-chrome"):
        path = shutil.which(name)
        if path:
            return path
    for path in _MAC_CHROME_PATHS:
        if path.is_file():
            return str(path)
    return None


def save_folium_png(m: folium.Map, filepath: Path = Path("catchment_map.png")) -> None:
    """Save a Folium map to PNG using headless Chrome."""

    chrome_path = _find_chrome()

    if not chrome_path:
        raise RuntimeError(
            "Chrome/Chromium not found. Install Google Chrome or Chromium first."
        )

    options = Options()
    options.binary_location = chrome_path

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--remote-debugging-port=0")

    with tempfile.TemporaryDirectory() as temp_dir:
        html_path = Path(temp_dir) / "map.html"
        m.save(str(html_path))

        options.add_argument(
            f"--user-data-dir={temp_dir}/chrome-profile"
        )

        service = Service(
            log_output=str(Path(temp_dir) / "chromedriver.log")
        )

        try:
            driver = webdriver.Chrome(
                service=service,
                options=options
            )
        except Exception:
            log_path = Path(temp_dir) / "chromedriver.log"
            if log_path.exists():
                print(log_path.read_text()[-4000:])
            raise

        try:
            driver.set_window_size(1400, 1000)
            driver.get(html_path.as_uri())

            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script(
                    "return typeof L !== 'undefined' && "
                    "document.querySelector('.leaflet-container') !== null"
                )
            )

            # Give map tiles time to load and save a screenshot of the map
            time.sleep(5)

            driver.save_screenshot(filepath)
            logger.info(f"Saved screenshot of map to {filepath}")

        finally:
            driver.quit()

