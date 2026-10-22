"""Process the Attainment and Progress performance data."""

import pandas as pd

from config.config import get_config, PERFORMANCE_DATA_COLUMNS
from data_models.config_models import ConfigModel
from shared_funcitons import check_processed_data, load_or_download_raw_data, logger


""" Helper Functions """

def _filter_schools_and_years(
    schools_urns: dict[int, str], 
    years: list[int], 
    df: pd.DataFrame) -> pd.DataFrame:
    """Filter the data for the years and schools."""

    # Make URN numeric and cut a DF on the schools of interest
    df["school_urn"] = pd.to_numeric(
        df["school_urn"],
        errors="coerce"
    )

    # Filter for configured years
    df = df.loc[df["time_period"].isin(years), :]

    # Filter for configured schools and add school name as a column
    df = df.loc[df["school_urn"].isin(schools_urns), :].copy()
    df["school"] = df["school_urn"].map(schools_urns.get)

    # Log the number of schools and cohorts
    cohorts = df.time_period.unique().tolist()
    msg = (
        f"Filtered to {df.school.nunique()} schools "
        f"and {df.time_period.nunique()} cohorts: {cohorts} "
    )
    logger.info(msg)

    return df


""" Processor Classes """

class Ks2InformationProcessor:
    """Class to process Schools Information Data."""

    def __init__(self, config: ConfigModel):
        self.config = config

        self.data_set_name: str = self.config.ks2_information_urls["data_set_name"]
        self.url: str = self.config.ks2_information_urls["url"]
        self.raw_data_path = config.raw_data_dir / f"{self.data_set_name}_raw.pkl"
        self.processed_data_path = config.processed_data_dir / f"{self.data_set_name}_proc.pkl"
        

    def _select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select the columns of interest."""

        # Rename the column to be more descriptive
        df = df.rename(
            columns={
                "avg_ks2_scaledscore": "KS2 Avg"
            }
        )

        # Keep the school name so this table can join the institution data
        cols = ["time_period", "school", "KS2 Avg"]

        # Return the selected columns
        return df.loc[:, cols]


    def _make_columns_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Make the columns numeric."""
        for column in ("time_period", "school_urn", "avg_ks2_scaledscore"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        return df


    def process_data(self) -> pd.DataFrame | None:
        """Return the saved table, or build it from the raw data."""

        # 1. Check if the processed data already exists
        result = check_processed_data(self.processed_data_path)
        if result is not None:
            return result

        # 2. Load the raw data, then filter for the years and schools
        raw_df = load_or_download_raw_data(self.data_set_name, self.url, self.config.raw_data_dir)
        if raw_df is None:
            return None
        
        # 3. Make columns numeric, filter, select, and save
        try:
            ks2_df = self._make_columns_numeric(raw_df)
            ks2_df = _filter_schools_and_years(
                self.config.schools_urns,
                self.config.years,
                ks2_df,
            )
            ks2_df = self._select_columns(ks2_df)
            ks2_df.to_pickle(self.processed_data_path)
        except (KeyError, ValueError, TypeError, OSError) as e:
            logger.error(f"Error processing KS2 information data: {e}")
            raise

        logger.info(f"Saved processed data to {self.processed_data_path}")
        return ks2_df


class DfEInstitutionLevelData:
    """Class to compile the DfE institution level data."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.combined_raw_data_path = config.raw_data_dir / "dfe_institution_level_combined_raw.pkl"

    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate the data."""
        required_cols = [
            "school_urn",
            "pupil_count",
            "attainment8_average",
            "progress8_average",
            "progress8_lower_95_ci",
            "progress8_upper_95_ci"
        ]
        if not all(col in df.columns for col in required_cols):
            raise ValueError("The data does not have the correct columns.")
        return None


    def _format_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the raw data."""

        # Ensure URN and other values are numeric
        numeric_cols = [
            "school_urn",
            "pupil_count",
            "attainment8_average",
            "progress8_average",
            "progress8_lower_95_ci",
            "progress8_upper_95_ci"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        # Validate the data
        self._validate_data(df)

        return df


    def _load_raw_data(self) -> pd.DataFrame | None:
        """Load the raw data."""
        # Define a DataFrame
        concat_df = pd.DataFrame()

        # Load the raw data for each data set
        for data_set_name, url in self.config.institutional_urls.items():
            # Load or download the raw data
            raw_df = load_or_download_raw_data(data_set_name, url, self.config.raw_data_dir)

            # Concatenate the formatted raw data and de-dupe
            try:
                concat_df = pd.concat(
                    [concat_df, self._format_raw_data(raw_df)],
                    ignore_index=True,
                )
                concat_df = concat_df.drop_duplicates(
                    subset=["time_period", "school_urn", "breakdown"],
                    keep="first",
                )
            except (KeyError, ValueError, TypeError) as e:
                logger.error(
                    f"Error preparing DfE institution level data '{data_set_name}': {e}"
                )
                raise

        # Save the data
        try:
            concat_df.to_pickle(self.combined_raw_data_path)
        except OSError as e:
            logger.error(
                f"Error saving combined raw data to {self.combined_raw_data_path}: {e}"
            )
            raise
        logger.info(f"Saved formatte and combined raw data to {self.combined_raw_data_path}")

        return concat_df


    def load_data(self) -> pd.DataFrame | None:
        """Load the raw institution-level data."""
        raw_df = self._load_raw_data()
        if raw_df is not None:
            return raw_df
        return None


class DfEInstitutionLevelProcessor:
    """Class to process the DfE institution level data."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.processed_data_path = config.processed_data_dir / "dfe_institution_level_data_proc.pkl"

    def _make_columns_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Make the columns numeric."""
        for column in (
            "time_period",
            "school_urn",
            "pupil_count",
            "attainment8_average",
            "progress8_average",
            "progress8_lower_95_ci",
            "progress8_upper_95_ci",
        ):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        return df

    def _cut_a8_and_p8_scores(self, schools_df: pd.DataFrame) -> None:
        """Cut a dataframe with the overall A8 and P8 scores"""

        # Get the overall P8 and A8, with confidence intervals
        total_rows = (
            (schools_df["prior_attainment"] == "Total")
            & (schools_df["breakdown_topic"] == "Total")
            & (schools_df["breakdown"] == "Total")
        )
        overall_a8_p8 = schools_df.loc[
            total_rows,
            [
                "time_period",
                "school",
                "attainment8_average",
                "progress8_average",
                "progress8_lower_95_ci",
                "progress8_upper_95_ci",
            ],
        ].sort_values(by=["time_period", "school"]).copy()

        # Set the index to the time period and school
        self.overall_a8_p8 = overall_a8_p8.set_index(["time_period", "school"])

        # Return the dataframe
        return None


    def _build_prior_data(self, schools_df: pd.DataFrame) -> pd.DataFrame:
        """Build the prior data based on KS2 performance."""

        prior_rows = schools_df["prior_attainment"].isin(
            [
                "Low prior attainment",
                "Mid prior attainment",
                "High prior attainment",
            ]
        )
        prior: pd.DataFrame = schools_df.loc[prior_rows, :].copy()

        # Use better names
        group_map = {
            "Low prior attainment": "Low",
            "Mid prior attainment": "Middle",
            "High prior attainment": "High",
        }
        prior["group"] = prior["prior_attainment"].map(group_map.get)


        # Calculate percentages
        prior["prior_total"] = (
            prior
            .groupby(["time_period", "school"])["pupil_count"]
            .transform("sum")
        )

        prior["pct"] = (
            prior["pupil_count"]
            / prior["prior_total"]
            * 100
        )

        return prior


    def _pivot_prior_metrics(self, prior: pd.DataFrame) -> None:
        """Pivot the prior metrics."""

        self.n = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="pupil_count"
        )

        self.pct = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="pct"
        )

        self.a8 = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="attainment8_average"
        )

        self.p8 = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="progress8_average"
        )

        self.p8_ci_low = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="progress8_lower_95_ci"
        )

        self.p8_ci_upp = prior.pivot(
            index=["time_period", "school"],
            columns="group",
            values="progress8_upper_95_ci"
        )

    
    def _build_sex_data(self, schools_df: pd.DataFrame) -> pd.DataFrame:
        """Process the sex data."""
        # Cut the DF on boys and girls
        sex_rows = (
            (schools_df["breakdown_topic"] == "Sex")
            & (schools_df["breakdown"].isin(["Boys", "Girls"]))
            & (schools_df["prior_attainment"] == "Total")
        )
        sex: pd.DataFrame = schools_df.loc[sex_rows, :].copy()

        # Create a percent of girls and boys at each school
        sex["sex_total"] = (
            sex.groupby(["time_period", "school"])["pupil_count"]
            .transform("sum")
        )

        sex["sex_pct"] = (
            sex["pupil_count"] / sex["sex_total"] * 100
        )

        return sex


    def _pivot_sex_metrics(self, sex: pd.DataFrame) -> None:
        """Pivot the sex metrics."""

        self.sex_pct = sex.pivot(
            index=["time_period", "school"],
            columns="breakdown",
            values="sex_pct"
        )

        self.sex_a8 = sex.pivot(
            index=["time_period", "school"],
            columns="breakdown",
            values="attainment8_average"
        )

        self.sex_p8 = sex.pivot(
            index=["time_period", "school"],
            columns="breakdown",
            values="progress8_average"
        )

        self.p8_sex_ci_low = sex.pivot(
            index=["time_period", "school"],
            columns="sex",
            values="progress8_lower_95_ci"
        )

        self.p8_sex_ci_upp = sex.pivot(
            index=["time_period", "school"],
            columns="sex",
            values="progress8_upper_95_ci"
        )

        self.sex_n = sex.pivot(
            index=["time_period", "school"],
            columns="sex",
            values="pupil_count"
        )

        return None


    def _compile_final_data(self) -> pd.DataFrame:
        """Compile the final data table."""

        result = pd.DataFrame(index=self.overall_a8_p8.index)

        # Overall average A8 and P8
        result["A8 Average"] = self.overall_a8_p8["attainment8_average"]
        result["P8 Average"] = self.overall_a8_p8["progress8_average"]
        result["P8 CI Lower"] = self.overall_a8_p8["progress8_lower_95_ci"]
        result["P8 CI Upper"] = self.overall_a8_p8["progress8_upper_95_ci"]

        # Proportion of boys and girls
        result["Boys %"] = self.sex_pct["Boys"]
        result["Girls %"] = self.sex_pct["Girls"]

        # Number of boys and girls
        result["Boys N"] = self.sex_n["Boys"]
        result["Girls N"] = self.sex_n["Girls"]

        # Breakdon A8 and P8 on boys and girls
        result["A8 Boys"] = self.sex_a8["Boys"]
        result["A8 Girls"] = self.sex_a8["Girls"]
        result["P8 Boys"] = self.sex_p8["Boys"]
        result["P8 Girls"] = self.sex_p8["Girls"]

        # Confidence intervals for boys and girls P8
        result["P8 Boys CI Lower"] = self.p8_sex_ci_low["Boys"]
        result["P8 Boys CI Upper"] = self.p8_sex_ci_upp["Boys"]
        result["P8 Girls CI Lower"] = self.p8_sex_ci_low["Girls"]
        result["P8 Girls CI Upper"] = self.p8_sex_ci_upp["Girls"]

        # Number of pupils in KS2 band
        result["KS2 Low N"] = self.n["Low"]
        result["KS2 Middle N"] = self.n["Middle"]
        result["KS2 High N"] = self.n["High"]

        # Percent of pupils in KS2 band
        result["KS2 Low"] = self.pct["Low"]
        result["KS2 Middle"] = self.pct["Middle"]
        result["KS2 High"] = self.pct["High"]

        # A8 and P8 for KS2 bands
        result["A8 Low"] = self.a8["Low"]
        result["A8 Middle"] = self.a8["Middle"]
        result["A8 High"] = self.a8["High"]
        result["P8 Low"] = self.p8["Low"]
        result["P8 Middle"] = self.p8["Middle"]
        result["P8 High"] = self.p8["High"]

        # Confidence intervals for KS2 banded P8
        result["P8 Low CI Lower"] = self.p8_ci_low["Low"]
        result["P8 Low CI Upper"] = self.p8_ci_upp["Low"]
        result["P8 Middle CI Lower"] = self.p8_ci_low["Middle"]
        result["P8 Middle CI Upper"] = self.p8_ci_upp["Middle"]
        result["P8 High CI Lower"] = self.p8_ci_low["High"]
        result["P8 High CI Upper"] = self.p8_ci_upp["High"]

        result = (
            result
            .round(2)
            .reset_index()
        )

        result.to_pickle(self.processed_data_path)
        logger.info(f"Saved processed data to {self.processed_data_path}")

        return result


    def process_data(self) -> pd.DataFrame | None:
        """Return the saved table, or build it from the raw data."""

        # 1. Check if the processed data already exists
        result = check_processed_data(self.processed_data_path)
        if result is not None:
            return result

        # 2. Load the raw data, then filter for the years and schools
        raw_df = DfEInstitutionLevelData(self.config).load_data()
        if raw_df is None:
            return None

        # 3. Make columns numeric, then filter, pivot, compile, and save
        try:
            schools_df = self._make_columns_numeric(raw_df)
            schools_df = _filter_schools_and_years(
                self.config.schools_urns,
                self.config.years,
                schools_df,
            )
            self._cut_a8_and_p8_scores(schools_df)
            self._pivot_prior_metrics(self._build_prior_data(schools_df))
            self._pivot_sex_metrics(self._build_sex_data(schools_df))
            return self._compile_final_data()
        except (KeyError, ValueError, TypeError, OSError) as e:
            logger.error(f"Error processing DfE institution level data: {e}")
            raise


def get_performance_data() -> pd.DataFrame | None:
    """Process the performance data."""

    config = get_config()

    # 1. Check if the processed data already exists
    result = check_processed_data(config.processed_data_dir / "performance_data_merged.pkl")
    if result is not None:
        logger.info(f"Performance data already exists, with shape: {result.shape}")
        return result
    
    # 2. Load and Process DfE Institution Level Data
    result = DfEInstitutionLevelProcessor(config).process_data()
    if result is None:
        logger.error("No DfE institution level data was found")
        return None

    # 3. Load and Process DfE Key Stage 2 Data
    ks2 = Ks2InformationProcessor(config).process_data()
    if ks2 is None:
        logger.error("No DfE key stage 2 data found")
        return None

    # 4. Merge the tables, keep the performance columns, and save
    merged_path = config.processed_data_dir / "performance_data_merged.pkl"
    try:
        merged_df = result.merge(
            ks2,
            on=["time_period", "school"],
            how="left",
        )
        merged_df = merged_df.loc[:, PERFORMANCE_DATA_COLUMNS]
        merged_df.to_pickle(merged_path)
    except (KeyError, ValueError, OSError) as e:
        logger.error(f"Error merging performance data: {e}")
        raise

    logger.info(f"Saved merged data {merged_df.shape} to {merged_path}")

    return result


def main() -> None:
    """ Main function to run the performance analysis. """
    get_performance_data()


if __name__ == "__main__":
    main()