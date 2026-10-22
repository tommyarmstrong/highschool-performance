import pandas as pd

from config.config import get_config
from performance.ks2_band_plots import (
    plot_a8_band_distribution,
    plot_a8_ks2_scatter,
    plot_a8_p8_trends,
    plot_by_prior_attainment,
    plot_ks2_band_distribution,
    plot_p8_ks2_scatter,
    tabulate_a8_band_distribution,
)
from performance.sex_plots import plot_by_sex, plot_p8_sex_year
from shared_funcitons import logger, read_dataframe


config = get_config()

def plot_performance_data() -> None:
    """Plot the performance data."""

    # Load data
    df: pd.DataFrame = read_dataframe(config.processed_data_dir / "performance_data_merged.pkl")
    logger.info(f"Plot data shape: {df.shape}")

    # Plot Attainment 8 and Progress 8 trends based on KS2 band
    plot_a8_p8_trends(df, save_png=True)
    plot_a8_ks2_scatter(df, save_png=True)
    plot_p8_ks2_scatter(df, save_png=True)
    plot_ks2_band_distribution(df, year=202324, save_png=True)
    plot_a8_band_distribution(df, year=202324, save_png=True)
    tabulate_a8_band_distribution(df, year=202324)
    plot_by_prior_attainment(df, time_period=202324)
    plot_by_prior_attainment(df, time_period=202324, metric="a8")
    plot_by_prior_attainment(df, file_name="p8_all_years_by_prior_attainment.png")


    # Plot Progress 8 by sex
    plot_p8_sex_year(df)
    plot_p8_sex_year(df, sex="Boys")
    plot_p8_sex_year(df, sex="Girls")

    # Plot all schools Performance 8 by sex for 2022/23 and 2023/24
    plot_by_sex(df, metric="p8", time_period=[202223,202324])

    # Plot all schools Attainment 8 by sex for all years 
    # Cannot fit all schools on one chart, so split into multiple charts
    schools_to_filter: dict[str, list[str]] = {
        "a8_by_sex_AP-F-G.png": ["Alexandra Park", "Fortismere", "Gladesmore"],
        "a8_by_sex_G-H-HW.png": ["Greig", "Heartlands", "Highgate Wood"],
        "a8_by_sex_PV-S-STM.png": ["Park View", "Skinners", "St Thomas More"] 
        }
    for file_name, schools in schools_to_filter.items():
        plot_by_sex(df, metric="a8", schools=schools, file_name=file_name)

    return None