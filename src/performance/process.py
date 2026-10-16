"""Process the Attainment and Progress performance data."""

from pathlib import Path

import pandas as pd

from config.config import get_config
from data_models.config_models import ConfigModel
from shared_funcitons import download_file, logger, read_dataframe





class DfEInstitutionLevelData:
    """Class to compile the DfE institution level data."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.processed_data_path = config.processed_data_dir / "dfe_institution_level_data_proc.pkl"
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
        """Format and save the raw data."""
        
        try:
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
        except Exception as e:
            logger.error(f"Error saving raw DfE institution level data: {e}")
            raise e


    def _load_processed_data(self) -> pd.DataFrame | None:
        """Load the processed data."""
        try:
            df = read_dataframe(self.processed_data_path)
            logger.info(f"Loaded processed DfE institution level data: {self.processed_data_path.parents[2]}")
            return df
        except FileNotFoundError:
            logger.info(f"No processed DfE institution level data file: {self.processed_data_path.parents[2]}")
            return None
        except Exception as e:
            logger.error(f"Error loading processed DfE institution level data: {e}")
            raise e

 
    def _load_raw_data(self) -> pd.DataFrame | None:
        """Load the raw data."""
        # Define a DataFrame
        concat_df = pd.DataFrame()

        # Load the raw data for each data set
        for data_set in self.config.dfe_urls.items():
            data_set_name: str = data_set[0]
            url: str = data_set[1]
            raw_data_path: Path = self.config.raw_data_dir / f"{data_set_name}_raw.pkl"
            try:
                df = read_dataframe(raw_data_path)
                logger.info(f"Loaded raw {data_set_name}: {raw_data_path.parents[2]}")
            except FileNotFoundError:
                logger.info(f"No raw {data_set_name} file: {raw_data_path.parents[2]}")
                df = self._download_raw_data(data_set_name, url)

                # Save the data to file
                self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)
                df.to_pickle(raw_data_path)
                logger.info(f"Saved raw {data_set_name} to {raw_data_path.parents[2]}")
            except Exception as e:
                logger.error(f"Error loading {data_set_name}: {e}")
                raise e

            # Concatenate the data and de-dupe 
            concat_df = pd.concat([concat_df, df], ignore_index=True)
            concat_df = concat_df.drop_duplicates(
                subset=["time_period", "school_urn", "breakdown"],
                keep="first",
            )

            # Save the data
            concat_df.to_pickle(self.combined_raw_data_path)
            logger.info(f"Saved combined raw data to {self.combined_raw_data_path.parents[2]}")

        return concat_df


    def _download_raw_data(self, data_set_name: str, url: str) -> pd.DataFrame:
        """Download the raw data."""
        logger.info(f"Downloading {data_set_name} from {url}")
        csv_path = self.config.raw_data_dir / f"{data_set_name}.csv"
        try:
            download_file(url, csv_path, retries=3)
            df: pd.DataFrame = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Downloaded {data_set_name} from {url}")

            # Format the data
            formatted_df = self._format_raw_data(df)

            # Save the data
            self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)
            raw_data_path: Path = self.config.raw_data_dir / f"{data_set_name}_raw.pkl"
            formatted_df.to_pickle(raw_data_path)
            
            logger.info(f"Saved formatted {data_set_name} to {raw_data_path.parents[2]}")
            return formatted_df
        except Exception as e:
            logger.error(f"Error downloading {data_set_name}: {e}")
            logger.error(f"URL {url}")
            raise e
        finally:
            csv_path.unlink(missing_ok=True)
            

    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process the data."""

        # TODO: This needs to call the processor when it is available
        return df


    def load_data(self) -> pd.DataFrame | None:
        """Load the data."""

        # 1. Attempt to load processed data
        processed_df = self._load_processed_data()
        if processed_df is not None:
            return processed_df

        # 2. Attempt to load the raw data
        raw_df = self._load_raw_data()
        if raw_df is not None:
            return self._process_data(raw_df)



class DfEInstitutionLevelProcessor:
    """Class to process the DfE institution level data."""

    def __init__(self, config: ConfigModel, df: pd.DataFrame):
        self.config = config
        self.processed_data_path = config.processed_data_dir / "dfe_institution_level_data_proc.pkl"


    def _filter_schools_and_years(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter the data for the years and schools."""

        # Filter for configured years
        df = df.loc[df["time_period"].isin(self.config.years), :]

        # Filter for configured schools and add school name as a column
        df = df.loc[df["school_urn"].isin(self.config.schools_urns), :].copy()
        df["school"] = df["school_urn"].map(self.config.schools_urns.get)

        # Log the number of schools and cohorts
        cohorts = df.time_period.unique().tolist()
        msg = (
            f"Filtered to {df.school.nunique()} schools "
            f"and {df.time_period.nunique()} cohorts: {cohorts} "
        )
        logger.info(msg)

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
        logger.info(f"Saved processed data to {self.processed_data_path.parents[2]}")

        return result


    def _check_processed_data(self) -> pd.DataFrame | None:
        """Check if the processed data already exists."""
        if self.processed_data_path.exists():
            logger.info(f"Processed data already exists: {self.processed_data_path.parents[2]}")
            return read_dataframe(self.processed_data_path)
        else:
            logger.info(f"Processed data does not exist: {self.processed_data_path.parents[2]}")
            return None


    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process the data."""

        # 1. Check if the processed data already exists
        result = self._check_processed_data()
        if result is not None:
            return result

        # 2. Filter the data for the years and schools
        schools_df = self._filter_schools_and_years(df)

        # 3. Cut a dataframe with the overall A8 and P8 scores
        self._cut_a8_and_p8_scores(schools_df)

        # 4. Process and pivot the prior data
        self._pivot_prior_metrics(self._build_prior_data(schools_df))

        # 5. Process and pivot the sex data
        self._pivot_sex_metrics(self._build_sex_data(schools_df))

        # 6. Compile the final data
        return self._compile_final_data()


def run_performance() -> None:
    """Process the performance data."""

    config = get_config()
    dfe_institutional = DfEInstitutionLevelData(config)

    # 1. Load the DfE institution level data
    df = dfe_institutional.load_data()


    # 2. Process the DfE institution level data
    if df is not None:
        processor = DfEInstitutionLevelProcessor(config, df)
        result = processor.process_data(df)
        if result is not None:
            logger.info(f"DfE institution level processed data shape: {result.shape}")    
    
    else:
        logger.error("No DfE institution level data found")
    
    return None


def main() -> None:
    """Main function to run the performance analysis."""
    run_performance()
    return None


if __name__ == "__main__":
    main()