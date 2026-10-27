"""Process the Attainment and Progress performance data."""

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config.config import get_config, APPLICATIONS_COLUMNS
from data_models.config_models import ConfigModel
from shared_funcitons import check_processed_data, load_or_download_raw_data, logger


# Get the config
config: ConfigModel = get_config()


class DfEApplicationsProcessor:
    """Process the DfE Applications data."""

    def __init__(self, config: ConfigModel):
        self.config = config

        (self.data_set_name, self.url), = self.config.applications_urls.items()
        self.raw_data_path = config.raw_data_dir / f"{self.data_set_name}_raw.pkl"
        self.processed_data_path = config.processed_data_dir / f"{self.data_set_name}_proc.pkl"

    def _filter_schools_and_years(self, df: pd.DataFrame, schools: dict[int, str]) -> pd.DataFrame:
        # Filter on schools of interest
        haringey_applications = df.loc[
            (df["school_phase"] == "Secondary")
            & (df["school_urn"].isin(list(schools.keys())))
        ].copy()

        # Map URNs to school names
        haringey_applications["school"] = (
            haringey_applications["school_urn"]
            .map(schools)
        )
        return haringey_applications

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename the columns."""
        df = df.rename(columns=APPLICATIONS_COLUMNS)

        return df

    
    def _select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Select useful columns."""
        df = (
            df.loc[:, list(APPLICATIONS_COLUMNS)]
            .sort_values(["time_period", "school"])
            .reset_index(drop=True)
        )
    
        return df

    def _engineer_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer the columns."""
        # First-choice applicants who received an offer (%)
        df["First Choice Offer Rate (%)"] = (
            100
            * df["First Choice Offers"]
            / df["First Choice Applications"].replace(0, np.nan)
        )

        # First-choice applications as a percentage of all preferences
        df["First Choice Share (%)"] = (
            100
            * df["First Choice Applications"]
            / df["Total Applications"].replace(0, np.nan)
        )

        # Number of offers made to pupils who did not choose the school
        df["Non-Preference Allocations"] = (
            df["Total Offers"]
            - df["Preferred Offers"]
        )

        # Percentage of offers that were non-preference allocations
        df["Non-Preference Allocations (%)"] = (
            100
            * df["Non-Preference Allocations"]
            / df["Total Offers"].replace(0, np.nan)
        )
        
        return df


    def process_data(self) -> pd.DataFrame | None:
        """Process the DfE Applications data."""

        # 1. Check if the processed data already exists
        df = check_processed_data(self.processed_data_path)
        if df is not None:
            logger.info(f"Processed applications data already exists, with shape: {df.shape}")
            return df

        # 2. Load the raw data
        raw_df = load_or_download_raw_data(self.data_set_name, self.url, self.config.raw_data_dir)
        if raw_df is None:
            return None

        # 3. Process the data
        df = self._filter_schools_and_years(raw_df, self.config.schools_urns)
        df = self._select_columns(df)
        df = self._rename_columns(df)
        df = self._engineer_columns(df)

        # 4. Save the processed data
        df.to_pickle(self.processed_data_path)
        logger.info(f"Processed applications data saved to {self.processed_data_path}")
        return df


class DfECensusProcessor:
    """Process the DfE Census data."""

    def __init__(self, config: ConfigModel):
        self.config = config

        (self.data_set_name, self.url), = self.config.census_urls.items()
        self.raw_data_path = config.raw_data_dir / f"{self.data_set_name}_raw.pkl"
        self.processed_data_path = config.processed_data_dir / f"{self.data_set_name}_proc.pkl"

    def _get_census_url(self, year: str) -> str:
        """Find the school-level underlying CSV for an academic year."""

        page_url = f"{self.url}/{year}/explore"

        response = requests.get(page_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            label = " ".join(
                link.get_text(" ", strip=True).lower().split()
            )
            href = link.get("href")
            if not isinstance(href, str):
                continue

            if (
                "school level underlying data" in label
                and "class sizes" not in label
                and "download" in label
            ):
                return urljoin(page_url, href)

        raise ValueError(
            f"School-level CSV link not found for {year}: {page_url}"
        )


    def _get_column_year_map(self) -> dict[str, str]:
        """ Different census releases use different column names. """
        year7_column_map = {
            # 2020/21 to 2023/24
            "Full time boys Year group 7": "Year 7 Boys",
            "Full time girls Year group 7": "Year 7 Girls",
            "Part time boys Year group 7": "Year 7 Part-time Boys",
            "Part time girls Year group 7": "Year 7 Part-time Girls",

            # 2024/25 to 2025/26
            "full-time male Year group 7": "Year 7 Boys",
            "full-time female Year group 7": "Year 7 Girls",
            "part-time male Year group 7": "Year 7 Part-time Boys",
            "part-time female Year group 7": "Year 7 Part-time Girls",
        }
        return year7_column_map


    def _load_and_process_year7_roll(self, year: str) -> pd.DataFrame:
        """Download and extract Year 7 rolls for selected schools."""

        # 1. Load the raw data
        data_set_name = f"{self.data_set_name}_{year}"
        url = self._get_census_url(year) 

        df = load_or_download_raw_data(
            data_set_name = data_set_name, 
            url = url, 
            raw_data_dir = self.config.raw_data_dir
            )

        # 2. Find URN column
        urn_col = next(
            (
                col for col in ["urn", "school_urn", "URN"]
                if col in df.columns
            ),
            None
        )

        if urn_col is None:
            raise ValueError(f"No URN column found for {year}")

        # Filter selected schools
        schools = self.config.schools_urns
        urns = pd.to_numeric(df[urn_col], errors="coerce")
        if not isinstance(urns, pd.Series):
            raise TypeError(f"URN column {urn_col!r} did not convert to a Series")

        df = df.loc[urns.isin(list(schools.keys()))].copy()
        df["school"] = urns.loc[df.index].map(schools)

        # Standardise column names
        df = df.rename(columns=self._get_column_year_map())

        # 3. Check for required columns
        required = ["Year 7 Boys", "Year 7 Girls"]

        missing = [
            col for col in required
            if col not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing Year 7 columns for {year}: {missing}"
            )

        # 4. Include part-time pupils if available
        pupil_cols = [
            col for col in [
                "Year 7 Boys",
                "Year 7 Girls",
                "Year 7 Part-time Boys",
                "Year 7 Part-time Girls",
            ]
            if col in df.columns
        ]

        roll = df[["school"] + pupil_cols].copy()

        # 5. Convert columns to numeric
        for col in pupil_cols:
            roll[col] = pd.to_numeric(
                roll[col],
                errors="coerce"
            )

        # 6. Total Year 7 headcount
        roll["Year 7 Roll"] = roll[pupil_cols].sum(
            axis=1,
            min_count=len(pupil_cols)
        )

        # Academic year
        start_year = int(year[:4])

        roll["time_period"] = (
            start_year * 100 + (start_year + 1) % 100
        )

        # 7. Save the processed data
        processed_data_path = self.config.processed_data_dir / f"{data_set_name}_proc.pkl"
        roll.to_pickle(processed_data_path)
        logger.info(f"Processed census data for {year} saved to {processed_data_path}")

        return roll[
            [
                "time_period",
                "school",
                "Year 7 Boys",
                "Year 7 Girls",
                "Year 7 Roll",
            ]
        ]

    
    def _load_raw_data(self) -> pd.DataFrame:
        """Download and combine all years."""
    
        roll_frames: list[pd.DataFrame] = []
        failed_years: dict[str, str] = {}

        for year in self.config.census_years:
            try:
                roll_frames.append(self._load_and_process_year7_roll(year))
                logger.debug(f"Completed {year}")

            except Exception as e:
                failed_years[year] = str(e)
                logger.error(f"FAILED {year}: {e}")

        if not roll_frames:
            raise RuntimeError("No census datasets were downloaded.")

        year7_roll = (
            pd.concat(roll_frames, ignore_index=True)
            .sort_values(["time_period", "school"])
            .reset_index(drop=True)
        )

        # Check duplicates
        duplicates = year7_roll.duplicated(
            ["time_period", "school"],
            keep=False
        )

        if duplicates.any():
            raise ValueError(
                "Duplicate school/year rows found:\n"
                + year7_roll.loc[duplicates].to_string(index=False)
            )

        # 7. Save the processed data
        processed_data_path = self.config.processed_data_dir / f"{self.data_set_name}_proc.pkl"
        year7_roll.to_pickle(processed_data_path)
        logger.info(f"Processed census data for all years saved to {processed_data_path}")

        return year7_roll


    def load_data(self) -> pd.DataFrame | None:
        """Load the DfE Census data."""

        # Return the saved table when this census release has already been processed
        df = check_processed_data(self.processed_data_path)
        if df is not None:
            logger.info(f"Processed census data already exists, with shape: {df.shape}")
            return df

        return self._load_raw_data()


class PlacesProcessor:
    """Process the places data."""

    def __init__(self, config: ConfigModel):
        self.config = config

        self.applications_df = DfEApplicationsProcessor(config).process_data()
        self.census_df = DfECensusProcessor(config).load_data()


    def _merge_data(self) -> pd.DataFrame | None:
        """Merge the data."""

        applications_df = self.applications_df
        census_df = self.census_df
        if applications_df is None:
            logger.error("No DfE applications data were found")
            return None
        if census_df is None:
            logger.error("No DfE census data were found")
            return None

        df = applications_df.merge(
            census_df,
            on=["time_period", "school"],
            how="inner"
        )

        return df
    

    def _engineer_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer the columns."""
        
        # Roll minus offers
        df["Roll Minus Offers"] = (
            df["Year 7 Roll"]
            - df["Total Offers"]
        )

        # Percent of offers taken up
        df["Roll vs Offers %"] = (
            100
            * df["Year 7 Roll"]
            / df["Total Offers"].replace(0, np.nan)
        )

        # First-choice applications for every 100 offers
        df["First Choices per 100 Offers"] = (
            100
            * df["First Choice Applications"]
            / df["Total Offers"].replace(0, np.nan)
        )

        # Convert columns to numeric
        numeric_cols = [
            "time_period",
            "Total Offers",
            "Preferred Offers",
            "Total Applications",
            "First Choice Applications",
            "Second Choice Applications",
            "Third Choice Applications",
            "First Choice Offers",
            "Second Choice Offers",
            "Third Choice Offers",
            "First Choice Offer Rate (%)",
            "First Choice Share (%)",
            "Non-Preference Allocations",
            "Non-Preference Allocations (%)",
            "First Choices per 100 Offers",
            "Year 7 Boys",
            "Year 7 Girls",
            "Year 7 Roll",
            "Roll Minus Offers",
            "Roll vs Offers %"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["year"] = df["time_period"] // 100
        return df.sort_values(["school", "year"])


    def process_data(self) -> pd.DataFrame | None:
        """Process the places data."""

        df = self._merge_data()
        if df is None:
            return None
        return self._engineer_columns(df)
        

def get_applications_data() -> pd.DataFrame | None:
    """Get the processed applications data."""

    applications_df = DfEApplicationsProcessor(config).process_data()
    if applications_df is None:
        logger.error("No DfE applications data were found")
        return None


def get_census_data() -> pd.DataFrame | None:
    """Get the processed census data."""

    census_df = DfECensusProcessor(config).load_data()
    if census_df is None:
        logger.error("No DfE census data were found")
        return None


def get_places_data() -> pd.DataFrame | None:
    """Get the processed places data."""

    places_df = PlacesProcessor(config).process_data()
    if places_df is None:
        logger.error("No places data were found")
        return None

    return None


