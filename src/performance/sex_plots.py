import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.config import get_config
from shared_funcitons import logger


config = get_config()


# Define a function to plot P8 for each schools with option to
# filter on sex and/or year

def plot_p8_sex_year(
    df: pd.DataFrame,
    sex: str | None = None,
    time_period: int | None = None,
    save_png: bool = True,
) -> None:
    """
    Plot Progress 8 with 95% confidence intervals.

    Parameters
    ----------
    result : pd.DataFrame
        DataFrame containing P8 results.

    sex : str | None
        None    = Boys and Girls combined
        "Boys"  = Boys only
        "Girls" = Girls only

    time_period : int | None
        None   = Both years
        202223 = 2022/23 only
        202324 = 2023/24 only

    Visual encoding
    ---------------
    Colour:
        2022/23 = orange
        2023/24 = blue

    Marker:
        Boys  = square
        Girls = circle
    """

    # --------------------------------------------------
    # Validate arguments
    # --------------------------------------------------

    sex =sex.title() if sex else None
    if sex not in (None, "Boys", "Girls"):
        raise ValueError(
            "sex must be None, 'Boys', or 'Girls'"
        )

    if time_period not in (None, 202223, 202324):
        raise ValueError(
            "time_period must be None, 202223, or 202324"
        )

    sexes = ["Boys", "Girls"] if sex is None else [sex]
    years = (
        [202223, 202324]
        if time_period is None
        else [time_period]
    )

    # --------------------------------------------------
    # Select columns and filter years
    # --------------------------------------------------

    cols = ["time_period", "school", "P8 Average"]

    for s in sexes:
        cols.extend([
            f"P8 {s}",
            f"P8 {s} CI Lower",
            f"P8 {s} CI Upper"
        ])

    plot_df = df.loc[:, cols].copy()

    time_period_values = pd.Series(
        pd.to_numeric(plot_df["time_period"], errors="coerce"),
        index=plot_df.index,
    )
    plot_df = plot_df.loc[time_period_values.isin(years), :].copy()
    plot_df["time_period"] = time_period_values.loc[time_period_values.isin(years)]

    numeric_cols = [
        c for c in cols
        if c not in ["time_period", "school"]
    ]

    for column in numeric_cols:
        plot_df[column] = pd.Series(
            pd.to_numeric(plot_df[column], errors="coerce"),
            index=plot_df.index,
        )

    # Keep rows with data for at least one selected sex
    value_cols = [f"P8 {s}" for s in sexes]

    plot_df = plot_df.dropna(
        subset=value_cols,
        how="all"
    )

    if plot_df.empty:
        raise ValueError("No P8 data found for the selected filters.")

    # --------------------------------------------------
    # Sort schools by selected year's P8
    # --------------------------------------------------

    # When plotting both years, sort by 2023/24.
    # Otherwise sort by the selected year.
    sort_year = 202324 if time_period is None else time_period

    sort_df = plot_df.loc[plot_df["time_period"] == sort_year, :].copy()

    if sex is None:
        band_means = sort_df.loc[:, value_cols].mean(axis=1)
        sort_df["sort_p8"] = sort_df["P8 Average"].fillna(band_means)
    else:
        sort_df["sort_p8"] = sort_df[f"P8 {sex}"]

    sort_order = (
        sort_df
        .sort_values("sort_p8")["school"]
        .tolist()
    )

    # Include schools present only in the other year
    other_schools = sorted(
        set(plot_df["school"]) - set(sort_order)
    )

    sort_order = other_schools + sort_order

    school_y = {
        school: i
        for i, school in enumerate(sort_order)
    }

    # --------------------------------------------------
    # Colours, markers and offsets
    # --------------------------------------------------

    colours = {
        202223: "tab:orange",
        202324: "tab:blue"
    }

    markers = {
        "Boys": "s",
        "Girls": "o"
    }

    year_labels = {
        202223: "2022/23",
        202324: "2023/24"
    }

    # Automatically space out the selected series
    combinations = [
        (year, s)
        for year in years
        for s in sexes
    ]

    offsets_array = np.linspace(
        -0.30 if len(combinations) == 4 else -0.12,
        +0.30 if len(combinations) == 4 else +0.12,
        len(combinations)
    ) if len(combinations) > 1 else [0.0]

    offsets = dict(zip(combinations, offsets_array))

    # --------------------------------------------------
    # Create plot
    # --------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, max(7, len(sort_order) * 0.65))
    )

    for year, s in combinations:

        value_col = f"P8 {s}"
        lower_col = f"P8 {s} CI Lower"
        upper_col = f"P8 {s} CI Upper"

        d = plot_df.loc[plot_df["time_period"] == year, :].dropna(
            subset=[value_col, lower_col, upper_col]
        ).copy()

        if d.empty:
            continue

        values = d[value_col].to_numpy()
        lower = d[lower_col].to_numpy()
        upper = d[upper_col].to_numpy()

        xerr = np.array([
            values - lower,
            upper - values
        ])

        y_pos = np.array([
            school_y[school]
            for school in d["school"]
        ]) + offsets[(year, s)]

        # Legend labels
        if sex is None and time_period is None:
            label = f"{s} {year_labels[year]}"
        elif sex is None:
            label = s
        else:
            label = year_labels[year]

        ax.errorbar(
            values,
            y_pos,
            xerr=xerr,
            fmt=markers[s],
            color=colours[year],
            markersize=8,
            capsize=4,
            elinewidth=1.5,
            linewidth=0,
            label=label,
            zorder=3
        )

    # --------------------------------------------------
    # Reference lines
    # --------------------------------------------------

    ax.axvline(
        0,
        linestyle="--",
        linewidth=1.2,
        color="grey",
        label="_nolegend_"
    )

    for x in [-0.5, 0.5]:
        ax.axvline(
            x,
            linestyle=":",
            linewidth=1,
            color="grey",
            label="_nolegend_"
        )

    # --------------------------------------------------
    # Labels and formatting
    # --------------------------------------------------

    y = np.arange(len(sort_order))

    ax.set_yticks(y)
    ax.set_yticklabels(sort_order)

    ax.set_xlabel("Progress 8")
    ax.set_ylabel("")

    title = (
        "Progress 8 by Sex"
        if sex is None
        else f"{sex} Progress 8"
    )

    period_label = (
        "2022/23 and 2023/24"
        if time_period is None
        else year_labels[time_period]
    )

    ax.set_title(
        f"{title}, {period_label}\n"
        "95% Confidence Intervals",
        fontsize=14,
        pad=15
    )

    ax.legend(
        title=(
            "Sex and GCSE Year"
            if sex is None and time_period is None
            else "Sex"
            if sex is None
            else "GCSE Year"
        ),
        frameon=True
    )

    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.7, len(sort_order) - 0.3)

    plt.tight_layout()

    if save_png:
        file_path = config.charts_dir / f"p8_{'_'.join(sexes).lower()}.png"
        plt.savefig(file_path, dpi=300)
        logger.info(f"Saved: {file_path}")
    else:
        plt.show()

    return None

def plot_by_sex(
    df: pd.DataFrame,
    metric: str | None = None,
    time_period: int | None | list[int] = None,
    schools: list[str] | None | str = None,
    file_name: str | None = None,
    save_png: bool = True,
) -> None:
    """
    Plot Boys vs Girls for Attainment 8 or Progress 8.

    metric:
        None or "a8" = Attainment 8 (default)
        "p8"         = Progress 8

    time_period:
        None   = all available years
        202223 = 2022/23
        202324 = 2023/24
        202425 = 2024/25
        202526 = 2025/26
        [202223, 202324] = multiple years

    Connecting lines:
        One year       = grey
        Multiple years = consistent colour per school
    """

    # Validate arguments
    metric = metric.lower() if metric else "a8"

    if metric not in ("a8", "p8"):
        raise ValueError("metric must be None, 'a8', or 'p8'")

    """
    if time_period not in (None, 202223, 202324, 202425, 202526):
        raise ValueError(
            "time_period must be None, 202223, or 202324"
        )
    """

    prefix = metric.upper()
    metric_name = "Attainment 8" if metric == "a8" else "Progress 8"

    boys_col = f"{prefix} Boys"
    girls_col = f"{prefix} Girls"

    # Prepare data
    plot_df = df.loc[
        :,
        ["time_period", "school", boys_col, girls_col],
    ].copy()

    # Filter on schools
    if schools is not None:
        if isinstance(schools, str):
            schools = [schools]
        plot_df = plot_df.loc[plot_df["school"].isin(schools), :].copy()

    # Filter on years
    time_period_values = pd.Series(
        pd.to_numeric(plot_df["time_period"], errors="coerce"),
        index=plot_df.index,
    )
    for column in (boys_col, girls_col):
        plot_df[column] = pd.Series(
            pd.to_numeric(plot_df[column], errors="coerce"),
            index=plot_df.index,
        )

    if time_period is not None:
        if isinstance(time_period, int):
            year_mask = time_period_values == time_period
        else:
            year_mask = time_period_values.isin(time_period)
        plot_df = plot_df.loc[year_mask, :].copy()
        time_period_values = time_period_values.loc[year_mask]

    plot_df["time_period"] = time_period_values

    plot_df = (
        plot_df
        .dropna(subset=[boys_col, girls_col])
        .sort_values(["school", "time_period"])
        .reset_index(drop=True)
    )

    if plot_df.empty:
        raise ValueError("No data found for the selected filters.")

    # School (2023), School (2024), etc.
    plot_df["label"] = (
        plot_df["school"]
        + " (20"
        + plot_df["time_period"].astype(int).astype(str).str[-2:]
        + ")"
    )

    # Determine whether multiple years are present
    multiple_years = plot_df["time_period"].nunique() > 1

    # Consistent colour for each school across years
    schools = sorted(plot_df["school"].unique())

    cmap = plt.get_cmap("tab20", len(schools))

    school_colours = {
        school: cmap(i)
        for i, school in enumerate(schools)
    }

    y = np.arange(len(plot_df))

    fig, ax = plt.subplots(
        figsize=(11, max(7, len(plot_df) * 0.48))
    )

    # Connecting lines
    for i, row in plot_df.iterrows():

        line_colour = (
            school_colours[row["school"]]
            if multiple_years
            else "grey"
        )

        ax.plot(
            [row[boys_col], row[girls_col]],
            [i, i],
            color=line_colour,
            linewidth=2.5,
            alpha=0.75,
            zorder=2
        )

    # Boys and girls points
    ax.scatter(
        plot_df[boys_col],
        y,
        s=85,
        marker="s",
        label="Boys",
        zorder=3
    )

    ax.scatter(
        plot_df[girls_col],
        y,
        s=85,
        marker="o",
        label="Girls",
        zorder=3
    )

    # Value labels
    for i, row in plot_df.iterrows():

        ax.annotate(
            f"{row[boys_col]:.1f}",
            (row[boys_col], i),
            xytext=(-7, 9),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

        ax.annotate(
            f"{row[girls_col]:.1f}",
            (row[girls_col], i),
            xytext=(7, 9),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

    # Axis labels
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["label"])

    # Alphabetical order, top to bottom
    ax.invert_yaxis()

    # Progress 8 national benchmark
    if metric == "p8":
        ax.axvline(
            0,
            color="grey",
            linestyle="--",
            linewidth=1.2,
            zorder=1
        )

    ax.set_xlabel(f"{metric_name} score")
    ax.set_ylabel("")

    ax.set_title(
        f"{metric_name} Gender Gap",
        fontsize=14,
        pad=15
    )

    ax.legend()
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if file_name is None:
        file_name = f"{metric}_by_sex.png"
    file_path = config.charts_dir / file_name

    if save_png:
        plt.savefig(file_path, dpi=300)
        logger.info(f"Saved: {file_path}")
    else:
        plt.show()

    return None
        

