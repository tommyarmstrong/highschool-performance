import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from pathlib import Path

from config.config import get_config
from shared_funcitons import logger, read_dataframe


config = get_config()


def _finish_plot(fig: Figure, file_name: str, save_png: bool) -> None:
    """Save the figure, or show it when saving is turned off."""
    if save_png:
        file_path = config.charts_dir / file_name
        fig.savefig(file_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved plot to {file_path}")
        plt.close(fig)
        return
    plt.show()


processed_data_path = config.processed_data_dir / "places_data_merged.pkl"

def plot_applications(
    df: pd.DataFrame,
    metric: str = "First Choice Applications",
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """
    Plot school applications or offers over time.

    metric:
        "First Choice Applications"
        "Total Applications"
        "First Choice Offers"
        "Total Offers"
        "First Choice Offer Rate (%)"
        "First Choice Share (%)"

    schools:
        None = all schools
        list of school names = selected schools

    save_png:
        True = save the plot to a file
        False = do not save the plot to a file
    """

    def _plot_filename(metric: str) -> Path:
        """Get the filename for the plot."""
        return config.charts_dir / f"{metric.replace(' ', '_').lower()}.png"

    plot_df = df.copy()

    if metric not in plot_df.columns:
        raise ValueError(f"Column not found: {metric}")

    if schools is not None:
        plot_df = plot_df.loc[plot_df["school"].isin(schools)]

    if plot_df.empty:
        raise ValueError("No data to plot.")

    plot_df["time_period"] = pd.to_numeric(
        plot_df["time_period"], errors="coerce"
    )

    plot_df[metric] = pd.to_numeric(
        plot_df[metric], errors="coerce"
    )

    plot_df = plot_df.sort_values(["school", "time_period"])

    # Convert 202324 -> 2023 (admission starting year)
    plot_df["year"] = (
        plot_df["time_period"] // 100
    )

    fig, ax = plt.subplots(figsize=(13, 7))

    for school, data in plot_df.groupby("school", sort=True):
        ax.plot(
            data["year"],
            data[metric],
            marker="o",
            markersize=5,
            linewidth=2,
            label=school
        )

    ax.set_title(
        f"{metric} by School",
        fontsize=15,
        pad=15
    )

    ax.set_xlabel("Admissions year")
    ax.set_ylabel(metric)

    years = sorted(plot_df["year"].dropna().unique())

    ax.set_xticks(years)
    ax.set_xticklabels(
        [f"{year}/{str(year + 1)[-2:]}" for year in years],
        rotation=45,
        ha="right"
    )

    if "(%)" in metric:
        ax.set_ylim(bottom=0)
    else:
        ax.set_ylim(bottom=0)

    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)

    ax.legend(
        title="School",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    plt.tight_layout()
    _finish_plot(fig, _plot_filename(metric).name, save_png)


def _filter_schools(df: pd.DataFrame, schools: list[str] | None = None) -> pd.DataFrame:
    """Return data for selected schools."""
    if schools is None:
        return df.copy()

    return df.loc[df["school"].isin(schools)].copy()


def _school_colors(df: pd.DataFrame) -> dict[str, tuple[float, ...]]:
    """Assign a stable colour to each school."""
    school_names = sorted(str(school) for school in df["school"].dropna().unique())
    cmap = plt.get_cmap("tab20")
    return {
        school: tuple(cmap(i / max(len(school_names) - 1, 1)))
        for i, school in enumerate(school_names)
    }


def format_year_axis(ax, data):
    """Format academic years on the x-axis."""
    years = sorted(data["year"].dropna().unique())

    ax.set_xticks(years)
    ax.set_xticklabels(
        [f"{int(y)}/{str(int(y) + 1)[-2:]}" for y in years],
        rotation=45,
        ha="right"
    )


def plot_applications_and_rolls(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    file_name: str = "applications_and_rolls.png",
    save_png: bool = True,
) -> None:
    """Plot applications, offers, and Year 7 rolls over time."""

    data = _filter_schools(df, schools)
    selected = sorted(data["school"].unique())

    if not selected:
        raise ValueError("No data for selected schools.")

    fig, axes = plt.subplots(
        len(selected),
        1,
        figsize=(12, 3.2 * len(selected)),
        sharex=True,
        squeeze=False
    )

    metrics = {
        "First Choice Applications": {
            "color": "tab:blue",
            "linestyle": "-"
        },
        "Second Choice Applications": {
            "color": "tab:orange",
            "linestyle": "-"
        },
        "Third Choice Applications": {
            "color": "tab:purple",
            "linestyle": "-"
        },
        "Total Offers": {
            "color": "black",
            "linestyle": "--"
        },
        "Year 7 Roll": {
            "color": "tab:green",
            "linestyle": "-"
        }
    }

    for ax, school in zip(axes.flat, selected):

        d = data.loc[data["school"] == school].sort_values("year")

        for metric, style in metrics.items():
            ax.plot(
                d["year"],
                d[metric],
                marker="o",
                markersize=5,
                linewidth=2,
                color=style["color"],
                linestyle=style["linestyle"],
                label=metric
            )

        ax.set_title(school, loc="left", fontweight="bold")
        ax.set_ylabel("Applications / pupils")
        ax.grid(alpha=0.2)
        ax.set_axisbelow(True)

        # Automatically scale each school's y-axis
        values = d[list(metrics)].to_numpy(dtype=float)
        values = values[np.isfinite(values)]

        if len(values):
            y_min = values.min()
            y_max = values.max()
            padding = max((y_max - y_min) * 0.08, 5)

            ax.set_ylim(y_min - padding, y_max + padding)

    format_year_axis(axes.flat[-1], data)

    # One legend for the entire figure, on the right
    handles, labels = axes.flat[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="center left",
        bbox_to_anchor=(0.82, 0.5),
        frameon=False
    )

    fig.suptitle(
        "Secondary School Applications, Offers and Year 7 Rolls",
        fontsize=16,
        y=0.995
    )

    plt.tight_layout(rect=(0, 0, 0.81, 0.98))
    _finish_plot(fig, file_name, save_png)


def plot_stacked_applications(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot applications stacked by preference rank."""

    data = _filter_schools(df, schools)

    selected = sorted(data["school"].unique())

    fig, axes = plt.subplots(
        len(selected),
        1,
        figsize=(12, 3.2 * len(selected)),
        sharex=True,
        squeeze=False
    )

    for ax, school in zip(axes.flat, selected):

        d = data.loc[data["school"] == school].sort_values("year")

        first = d["First Choice Applications"]
        second = d["Second Choice Applications"]
        third = d["Third Choice Applications"]

        # Applications ranked fourth or lower
        other = (
            d["Total Applications"]
            - first
            - second
            - third
        ).clip(lower=0)

        ax.stackplot(
            d["year"],
            first,
            second,
            third,
            other,
            labels=[
                "1st choice",
                "2nd choice",
                "3rd choice",
                "4th or lower"
            ],
            colors=[
                "tab:blue",
                "tab:orange",
                "tab:green",
                "tab:gray"
            ],
            alpha=0.85
        )

        ax.set_title(school, loc="left", fontweight="bold")
        ax.set_ylabel("Applications")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.15)

    format_year_axis(axes.flat[-1], data)

    axes.flat[0].legend(
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.35)
    )

    fig.suptitle(
        "Applications by Preference Rank",
        fontsize=16,
        y=1.01
    )

    plt.tight_layout()
    _finish_plot(fig, "stacked_applications.png", save_png)


def plot_applications_vs_offers(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    year: int | None = None,
    save_png: bool = True,
) -> None:
    """Plot applications against offers by preference rank."""

    data = _filter_schools(df, schools)

    if year is None:
        years = [int(value) for value in data["year"].dropna().unique()]
        if not years:
            raise ValueError("No year values to plot.")
        year = max(years)

    data = data.loc[data["year"] == year].sort_values("school")

    selected = data["school"].tolist()

    fig, axes = plt.subplots(
        1, 3,
        figsize=(17, max(5, len(selected) * 0.55)),
        sharey=True
    )

    ranks = [
        ("First Choice", "tab:blue"),
        ("Second Choice", "tab:orange"),
        ("Third Choice", "tab:green")
    ]

    y = np.arange(len(selected))

    for ax, (rank, color) in zip(axes, ranks):

        applications = data[f"{rank} Applications"]
        offers = data[f"{rank} Offers"]

        ax.barh(
            y - 0.18,
            applications,
            height=0.35,
            label="Applications",
            color=color,
            alpha=0.85
        )

        ax.barh(
            y + 0.18,
            offers,
            height=0.35,
            label="Offers",
            color="gray",
            alpha=0.75
        )

        ax.set_title(rank)
        ax.set_xlabel("Pupils / applications")
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(selected)
    axes[0].invert_yaxis()

    axes[0].legend()

    fig.suptitle(
        f"Applications vs Offers by Preference Rank — "
        f"{year}/{str(year + 1)[-2:]}",
        fontsize=16
    )

    plt.tight_layout()
    _finish_plot(fig, f"applications_vs_offers_{year}.png", save_png)


def plot_first_choice_demand(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot first-choice demand per 100 offers."""

    data = _filter_schools(df, schools)
    school_colors = _school_colors(df)

    fig, ax = plt.subplots(figsize=(13, 7))

    for school, d in data.groupby("school"):
        if not isinstance(school, str):
            continue

        ax.plot(
            d["year"],
            d["First Choices per 100 Offers"],
            marker="o",
            linewidth=2,
            label=school,
            color=school_colors[school]
        )

    ax.axhline(
        100,
        color="black",
        linestyle="--",
        alpha=0.6
    )

    ax.set_title("First-Choice Applications per 100 Offers")
    ax.set_ylabel("First choices per 100 offers")
    ax.set_xlabel("Admissions year")
    ax.set_ylim(bottom=0)

    format_year_axis(ax, data)

    ax.grid(alpha=0.2)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    _finish_plot(fig, "first_choice_demand.png", save_png)


def plot_roll_vs_offers(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot the Year 7 roll against offers."""

    data = _filter_schools(df, schools)
    school_colors = _school_colors(df)

    fig, ax = plt.subplots(figsize=(13, 7))

    for school, d in data.groupby("school"):
        if not isinstance(school, str):
            continue

        ax.plot(
            d["year"],
            d["Roll vs Offers %"],
            marker="o",
            linewidth=2,
            label=school,
            color=school_colors[school]
        )

    ax.axhline(
        100,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label="Roll equals offers"
    )

    ax.set_title("Year 7 Roll as a Percentage of Offers")
    ax.set_ylabel("Year 7 roll / total offers (%)")
    ax.set_xlabel("Admissions year")

    format_year_axis(ax, data)

    ax.grid(alpha=0.2)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    _finish_plot(fig, "roll_vs_offers.png", save_png)


def plot_non_preference_allocations(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot non-preference allocations."""

    data = _filter_schools(df, schools)
    school_colors = _school_colors(df)

    fig, ax = plt.subplots(figsize=(13, 7))

    for school, d in data.groupby("school"):
        if not isinstance(school, str):
            continue

        ax.plot(
            d["year"],
            d["Non-Preference Allocations (%)"],
            marker="o",
            linewidth=2,
            label=school,
            color=school_colors[school]
        )

    ax.set_title("Offers Made Without a School Preference")
    ax.set_ylabel("Non-preference allocations (%)")
    ax.set_xlabel("Admissions year")
    ax.set_ylim(bottom=0)

    format_year_axis(ax, data)

    ax.grid(alpha=0.2)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    _finish_plot(fig, "non_preference_allocations.png", save_png)


def plot_first_choice_offer_rate(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot the first-choice offer rate."""

    data = _filter_schools(df, schools)
    school_colors = _school_colors(df)

    fig, ax = plt.subplots(figsize=(13, 7))

    for school, d in data.groupby("school"):
        if not isinstance(school, str):
            continue

        ax.plot(
            d["year"],
            d["First Choice Offer Rate (%)"],
            marker="o",
            linewidth=2,
            label=school,
            color=school_colors[school]
        )

    ax.set_title("First-Choice Applicants Receiving an Offer")
    ax.set_ylabel("First-choice offer rate (%)")
    ax.set_xlabel("Admissions year")
    ax.set_ylim(0, 105)

    format_year_axis(ax, data)

    ax.grid(alpha=0.2)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    _finish_plot(fig, "first_choice_offer_rate.png", save_png)


def plot_offers_vs_roll(
    df: pd.DataFrame,
    schools: list[str] | None = None,
    save_png: bool = True,
) -> None:
    """Plot offers, Year 7 roll and first-choice applications by school."""

    data = _filter_schools(df, schools)

    if data.empty:
        raise ValueError("No data for selected schools.")

    data["time_period"] = pd.to_numeric(
        data["time_period"], errors="coerce"
    )

    data["year"] = data["time_period"] // 100

    metrics = [
        "Total Offers",
        "Year 7 Roll",
        "First Choice Applications"
    ]

    for col in metrics:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.sort_values(["school", "year"])

    selected = sorted(str(school) for school in data["school"].dropna().unique())

    # Consistent colours across all schools
    colors = _school_colors(df)

    # Line styles distinguish metrics
    styles = {
        "Total Offers": {
            "linestyle": "-",
            "marker": "o"
        },
        "Year 7 Roll": {
            "linestyle": ":",
            "marker": "s"
        },
        "First Choice Applications": {
            "linestyle": "--",
            "marker": "^"
        }
    }

    fig, ax = plt.subplots(figsize=(14, 7))

    for school in selected:
        d = data.loc[data["school"] == school]
        color = colors[school]

        for metric in metrics:
            ax.plot(
                d["year"],
                d[metric],
                color=color,
                linestyle=styles[metric]["linestyle"],
                marker=styles[metric]["marker"],
                linewidth=2.2,
                markersize=5,
                label=f"{school} — {metric}"
            )

    # Academic year labels
    years = sorted(data["year"].dropna().unique())

    ax.set_xticks(years)
    ax.set_xticklabels(
        [f"{int(y)}/{str(int(y) + 1)[-2:]}" for y in years],
        rotation=45,
        ha="right"
    )

    ax.set_title(
        "Secondary School Applications, Offers and Year 7 Roll",
        fontsize=15,
        pad=15
    )

    ax.set_xlabel("Admissions year")
    ax.set_ylabel("Number of pupils / applications")

    # Automatically scale y-axis to the plotted values
    values = data[metrics].to_numpy(dtype=float)
    values = values[np.isfinite(values)]

    if len(values):
        y_min = values.min()
        y_max = values.max()
        padding = max((y_max - y_min) * 0.08, 5)

        ax.set_ylim(
            y_min - padding,
            y_max + padding
        )

    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9,
        ncol=1,
        frameon=False
    )

    plt.tight_layout()
    _finish_plot(fig, "offers_vs_roll.png", save_png)


def plot_places_data(save_png: bool = True) -> None:
    """Plot the places data."""

    # 1. Load data
    df: pd.DataFrame = read_dataframe(processed_data_path)

    # 2. Plot applications data
    plot_applications(df, metric="First Choice Applications")
    plot_applications(df, metric="Total Applications")
    plot_applications(df, metric="First Choice Offers")
    plot_applications(df, metric="Total Offers")
    plot_applications(df, metric="First Choice Offer Rate (%)")
    plot_applications(df, metric="First Choice Share (%)")
    plot_applications(df, metric="Non-Preference Allocations")
    plot_applications(df, metric="Non-Preference Allocations (%)")
    plot_stacked_applications(df)
    plot_applications_vs_offers(df)
    plot_first_choice_demand(df)
    plot_non_preference_allocations(df)
    plot_first_choice_offer_rate(df)

    # 3. Plot census data
    # Three school panels fit on a slide, so split the full list into groups.
    applications_and_rolls_groups: dict[str, list[str]] = {
        "applications_and_rolls_AP-F-G.png": [
            "Alexandra Park",
            "Fortismere",
            "Gladesmore",
        ],
        "applications_and_rolls_G-H-HW.png": [
            "Greig",
            "Heartlands",
            "Highgate Wood",
        ],
        "applications_and_rolls_Ho-PV-S.png": [
            "Hornsey",
            "Park View",
            "Skinners'",
        ],
        "applications_and_rolls_STM.png": [
            "St Thomas More",
        ],
    }
    for file_name, schools in applications_and_rolls_groups.items():
        plot_applications_and_rolls(df, schools=schools, file_name=file_name)

    plot_roll_vs_offers(df)
    plot_offers_vs_roll(df)

    schools = ["Greig", "Heartlands", "Highgate Wood", "Park View"]
    plot_roll_vs_offers(df, schools=schools)
    plot_offers_vs_roll(df, schools=schools)
