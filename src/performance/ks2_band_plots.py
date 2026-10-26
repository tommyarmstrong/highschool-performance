import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.config import get_config
from shared_funcitons import logger

config = get_config()


def plot_a8_p8_trends(df: pd.DataFrame, schools: list[str] | None = None, save_png: bool = True) -> None:
    """
    Plot A8 Average and P8 Average over time for selected schools.

    Parameters
    ----------
    schools : list[str] | None
        Schools to plot. None plots all schools.
    save_png : bool
        Save both charts as PNG files.
    """

    df = df.loc[:, ["time_period", "school", "A8 Average", "P8 Average"]].copy()

    # Filter schools
    if schools is not None:
        if isinstance(schools, str):
            schools = [schools]
        df = df.loc[df["school"].isin(schools), :].copy()

    if df.empty:
        raise ValueError("No data for selected schools.")

    # Convert time_period (e.g. 202324) to examination year (2024)
    df["year"] = (
        df["time_period"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str[-2:]
        .astype(int)
        + 2000
    )

    df = df.sort_values(["school", "year"])

    # Check for duplicate school-year records
    if df.duplicated(["school", "year"]).any():
        raise ValueError(
            "Duplicate school/year rows found. "
            "Filter the data to one overall result per school/year."
        )

    # Consistent colours across both charts
    school_names = sorted(df["school"].unique())

    cmap = plt.get_cmap("tab20")
    school_colors = {
        school: cmap(i / max(len(school_names) - 1, 1))
        for i, school in enumerate(school_names)
    }

    metrics = [
        ("A8 Average", "Attainment 8", "Average Attainment 8 score", "attainment8_trends.png"),
        ("P8 Average", "Progress 8", "Average Progress 8 score", "progress8_trends.png"),
    ]

    for column, title, ylabel, filename in metrics:
        file_path = config.charts_dir / filename

        fig, ax = plt.subplots(figsize=(12, 6))

        for school in school_names:
            school_df = df[df["school"] == school]

            ax.plot(
                school_df["year"],
                school_df[column],
                marker="o",
                markersize=6,
                linewidth=2.3,
                color=school_colors[school],
                label=school,
            )

        # National reference for Progress 8
        if column == "P8 Average":
            ax.axhline(
                0,
                color="black",
                linestyle="--",
                linewidth=1.2,
                alpha=0.6,
                label="National reference",
            )

        ax.set_title(
            f"{title} by School",
            fontsize=16,
            fontweight="bold",
            pad=15,
        )

        ax.set_xlabel("GCSE examination year")
        ax.set_ylabel(ylabel)

        years = sorted(df["year"].unique())
        ax.set_xticks(years)

        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)

        ax.legend(
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        plt.tight_layout()

        if save_png:
            fig.savefig(
                file_path,
                dpi=300,
                bbox_inches="tight",
            )
            logger.info(f"Saved: {file_path}")
            plt.close(fig)
        else:
            plt.show()

    return None


def plot_a8_ks2_scatter(df: pd.DataFrame, save_png: bool = True) -> None:
    """ Scatter plot of A8 vs KS2 """

    file_path = config.charts_dir / "a8_ks2_scatter.png"

    # Ensure numeric
    for col in ["KS2 Avg", "A8 Average"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove rows missing either variable
    df = df.dropna(
        subset=["KS2 Avg", "A8 Average"]
    )

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Scatter points
    ax.scatter(
        df["KS2 Avg"],
        df["A8 Average"],
        s=80
    )

    # School labels
    for _, row in df.iterrows():
        ax.annotate(
            str(row["school"]),
            (float(str(row["KS2 Avg"])), float(str(row["A8 Average"]))),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9
        )

    # ---------------------------------------------------------
    # Linear regression
    # ---------------------------------------------------------

    x = df["KS2 Avg"].to_numpy(dtype=float)
    y = df["A8 Average"].to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)

    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    ax.plot(
        x_line,
        y_line,
        linestyle="--",
        linewidth=2,
        label="Linear regression"
    )

    # ---------------------------------------------------------
    # Pearson r and R²
    # ---------------------------------------------------------

    # Pearson correlation coefficient
    r = np.corrcoef(x, y)[0, 1]

    # Predicted values
    y_pred = slope * x + intercept

    # R²
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)

    r_squared = 1 - ss_res / ss_tot

    # Display statistics
    ax.text(
        0.03,
        0.97,
        f"Pearson r = {r:.3f}\nR² = {r_squared:.3f}",
        transform=ax.transAxes,
        va="top",
        fontsize=11
    )

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------

    ax.set_xlabel("Average KS2 scaled score")
    ax.set_ylabel("Attainment 8")
    ax.set_title("Attainment 8 (2024) against KS2 Prior Attainment (2019)")

    ax.grid(alpha=0.25)

    ax.legend()

    plt.tight_layout()

    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_p8_ks2_scatter(df: pd.DataFrame, save_png: bool = True) -> None:
    """ Scatter plot of P8 vs KS2 """

    file_path = config.charts_dir / "p8_ks2_scatter.png"

    # Ensure numeric
    for col in ["KS2 Avg", "P8 Average", "P8 CI Lower", "P8 CI Upper"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove rows missing required variables
    plot_df = df.dropna(
        subset=["KS2 Avg", "P8 Average", "P8 CI Lower", "P8 CI Upper"]
    )

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # ---------------------------------------------------------
    # Scatter points + 95% confidence intervals
    # ---------------------------------------------------------

    yerr = np.array([
        plot_df["P8 Average"] - plot_df["P8 CI Lower"],
        plot_df["P8 CI Upper"] - plot_df["P8 Average"]
    ])

    ax.errorbar(
        plot_df["KS2 Avg"],
        plot_df["P8 Average"],
        yerr=yerr,
        fmt="o",
        markersize=8,
        capsize=4,
        elinewidth=1.5,
        label="_nolegend_"
    )

    # School labels
    for _, row in plot_df.iterrows():
        ax.annotate(
            str(row["school"]),
            (float(str(row["KS2 Avg"])), float(str(row["P8 Average"]))),
            xytext=(7, 5),
            textcoords="offset points",
            fontsize=9
        )

    # ---------------------------------------------------------
    # Linear regression
    # ---------------------------------------------------------

    x = plot_df["KS2 Avg"].to_numpy(dtype=float)
    y = plot_df["P8 Average"].to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)

    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    ax.plot(
        x_line,
        y_line,
        linestyle="--",
        linewidth=2,
        label="Linear regression"
    )

    # ---------------------------------------------------------
    # Pearson r and R²
    # ---------------------------------------------------------

    r = np.corrcoef(x, y)[0, 1]

    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)

    r_squared = 1 - ss_res / ss_tot

    ax.text(
        0.03,
        0.97,
        f"Pearson r = {r:.3f}\nR² = {r_squared:.3f}",
        transform=ax.transAxes,
        va="top",
        fontsize=11
    )

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------

    ax.axhline(
        0,
        linestyle=":",
        linewidth=1,
        label="_nolegend_"
    )

    ax.axhline(
        0.5,
        linestyle=":",
        linewidth=1,
        label="_nolegend_"
    )

    ax.set_xlabel("Average KS2 scaled score")
    ax.set_ylabel("Progress 8")
    ax.set_title("Progress 8 (2024) against KS2 Prior Attainment (2019)")

    ax.grid(alpha=0.25)

    ax.legend()

    plt.tight_layout()

    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()
    return None


def plot_ks2_band_distribution(
    df: pd.DataFrame,
    year: int,
    save_png: bool = True,
) -> None:
    """Plot percentages of each KS2 band at each school for one cohort."""

    file_path = config.charts_dir / "ks2_band_distribution.png"

    # year is the DfE time_period code, for example 202324
    plot_df = df.loc[df["time_period"] == year, :].sort_values("KS2 Avg")
    if plot_df.empty:
        raise ValueError(f"No data for time period {year}.")

    ax = plot_df.set_index("school")[
        ["KS2 Low", "KS2 Middle", "KS2 High"]
    ].plot(
        kind="barh",
        stacked=True,
        figsize=(11, 7)
    )

    ax.set_xlabel("Pupils (%)")
    ax.set_ylabel("")
    ax.set_title("Prior Attainment Profile of 2024 GCSE Cohort (2019 intake)")
    ax.legend(
        ["Low", "Middle", "High"],
        title="KS2 prior attainment"
    )

    plt.tight_layout()

    fig = ax.figure
    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()
    return None


def plot_a8_band_distribution(
    df: pd.DataFrame,
    year: int,
    save_png: bool = True,
) -> None:
    """Plot percentages of each A8 band at each school for one cohort."""

    file_path = config.charts_dir / "a8_band_distribution.png"

    plot_df = (
        df.loc[df["time_period"] == year, :]
        .sort_values("A8 Middle")
        .set_index("school")
        [["A8 Low", "A8 Middle", "A8 High"]]
        .rename(columns={
            "A8 Low": "Low prior attainment",
            "A8 Middle": "Middle prior attainment",
            "A8 High": "High prior attainment",
        })
    )

    ax = plot_df.plot(
        kind="barh",
        figsize=(11, 8)
    )

    # Zero reference line - explicitly excluded from legend
    ax.axvline(
        0,
        linestyle="--",
        linewidth=1,
        label="_nolegend_"
    )

    ax.set_xlabel("Attainment 8")
    ax.set_ylabel("")
    ax.set_title("Attainment 8 by Prior Attainment Group")

    ax.legend(title="KS2 prior attainment")

    plt.tight_layout()

    fig = ax.figure
    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()
    return None


def tabulate_a8_band_distribution(
    df: pd.DataFrame,
    year: int = 202324,
    save_png: bool = True,
) -> None:
    """Tabulate the A8 band distribution for one cohort."""

    table = df.loc[
        df["time_period"] == year,
        ["school"] + [
            f"{metric} {band}{suffix}"
            for band in ["Low", "Middle", "High"]
            for metric, suffix in [
                ("P8", ""),
                ("P8", " CI Lower"),
                ("P8", " CI Upper"),
                ("KS2", " N")
            ]
        ]
    ].copy()

    # Format: P8 [CI lower, CI upper, N]
    def format_p8(row, band):
        p8 = row[f"P8 {band}"]
        lower = row[f"P8 {band} CI Lower"]
        upper = row[f"P8 {band} CI Upper"]
        n = row[f"KS2 {band} N"]

        if pd.isna(p8) or pd.isna(lower) or pd.isna(upper) or pd.isna(n):
            return "—"

        return f"{p8:+.2f} [{lower:+.2f}, {upper:+.2f}, {int(n)}]"

    formatted = pd.DataFrame({
        "School": table["school"],
        "Low": table.apply(lambda row: format_p8(row, "Low"), axis=1),
        "Middle": table.apply(lambda row: format_p8(row, "Middle"), axis=1),
        "High": table.apply(lambda row: format_p8(row, "High"), axis=1),
    })

    formatted = formatted.set_index("School").sort_index()
    if formatted.empty:
        raise ValueError(f"No data for time period {year}.")

    def ci_excludes_zero(value: str) -> bool:
        """True when the whole 95% confidence interval is above or below zero."""
        if value == "—":
            return False

        _p8, interval = value.split(" [")
        lower, upper, _n = interval.rstrip("]").split(", ")
        return float(lower) > 0 or float(upper) < 0

    caption = (
        f"Progress 8 by KS2 Prior Attainment — {str(year)[:4]}/{str(year)[-2:]}"
    )
    file_path = config.charts_dir / "p8_ks2_band_table.png"

    fig, ax = plt.subplots(figsize=(16, 4.6))
    ax.axis("off")
    ax.set_title(caption, fontsize=14, fontweight="bold", pad=10)

    cell_text = [
        [str(value) for value in row]
        for row in formatted.reset_index().itertuples(index=False, name=None)
    ]
    mpl_table = ax.table(
        cellText=cell_text,
        colLabels=["School", "Low", "Middle", "High"],
        loc="upper center",
        cellLoc="center",
        colWidths=[0.18, 0.27, 0.27, 0.28],
    )
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(10)
    mpl_table.scale(1, 1.6)

    for col in range(4):
        header = mpl_table[(0, col)]
        header.set_facecolor("#f2f2f2")
        header.get_text().set_fontweight("bold")

    for row_i, school in enumerate(formatted.index):
        for col_i, band in enumerate(("Low", "Middle", "High"), start=1):
            if ci_excludes_zero(str(formatted.loc[school, band])):
                mpl_table[(row_i + 1, col_i)].get_text().set_fontweight("bold")

    fig.canvas.draw()
    table_bbox = mpl_table.get_window_extent().transformed(fig.transFigure.inverted())
    fig.text(
        0.5,
        table_bbox.y0 - 0.03,
        "Bold values have a 95% confidence interval entirely above or below zero.",
        ha="center",
        va="top",
        fontsize=9,
    )

    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_p8_by_prior_attainment(
    result: pd.DataFrame,
    band: str | None = None,
    time_period: int | None = None,
    save_png: bool = True,
) -> None:
    """
    Plot Progress 8 by KS2 prior-attainment band
    with 95% confidence intervals.

    band:
        None, "Low", "Middle", "High" (case-insensitive)

    time_period:
        None, 202223, 202324

    Colours:
        Low    = blue
        Middle = orange
        High   = green

    Markers:
        2022/23 = circle
        2023/24 = square
    """

    # --------------------------------------------------
    # Validate arguments
    # --------------------------------------------------

    band = band.title() if band else None

    if band not in (None, "Low", "Middle", "High"):
        raise ValueError(
            "band must be None, 'Low', 'Middle', or 'High'"
        )

    if time_period not in (None, 202223, 202324):
        raise ValueError(
            "time_period must be None, 202223, or 202324"
        )

    bands = (
        ["Low", "Middle", "High"]
        if band is None
        else [band]
    )

    years = (
        [202223, 202324]
        if time_period is None
        else [time_period]
    )

    # --------------------------------------------------
    # Prepare data
    # --------------------------------------------------

    cols = ["time_period", "school", "P8 Average"]

    for b in bands:
        cols.extend([
            f"P8 {b}",
            f"P8 {b} CI Lower",
            f"P8 {b} CI Upper"
        ])

    plot_df = result.loc[:, cols].copy()

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

    # Keep rows with at least one selected band
    value_cols = [f"P8 {b}" for b in bands]

    plot_df = plot_df.dropna(
        subset=value_cols,
        how="all"
    )

    if plot_df.empty:
        raise ValueError(
            "No P8 data found for the selected filters."
        )

    # --------------------------------------------------
    # Sort schools by P8
    # --------------------------------------------------

    sort_year = 202324 if time_period is None else time_period

    sort_df = plot_df.loc[plot_df["time_period"] == sort_year, :].copy()

    if band is None:
        band_means = sort_df.loc[:, value_cols].mean(axis=1)
        sort_df["sort_p8"] = sort_df["P8 Average"].fillna(band_means)
    else:
        sort_df["sort_p8"] = sort_df[f"P8 {band}"]

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

    # --------------------------------------------------
    # Vertical positioning
    # --------------------------------------------------

    # Increase distance between schools
    school_spacing = 1.5

    school_y = {
        school: i * school_spacing
        for i, school in enumerate(sort_order)
    }

    # --------------------------------------------------
    # Visual settings
    # --------------------------------------------------

    # Colour represents prior attainment
    colours = {
        "Low": "tab:blue",
        "Middle": "tab:orange",
        "High": "tab:green"
    }

    # Marker represents GCSE year
    markers = {
        202223: "o",  # Circle
        202324: "s"   # Square
    }

    year_labels = {
        202223: "2022/23",
        202324: "2023/24"
    }

    combinations = [
        (year, b)
        for year in years
        for b in bands
    ]

    # Cluster the bands closer together within each school
    offsets_array = (
        np.linspace(-0.20, 0.20, len(combinations))
        if len(combinations) > 1
        else [0.0]
    )

    offsets = dict(zip(combinations, offsets_array))

    # --------------------------------------------------
    # Plot
    # --------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, max(7, len(sort_order) * 0.95))
    )

    for year, b in combinations:

        value_col = f"P8 {b}"
        lower_col = f"P8 {b} CI Lower"
        upper_col = f"P8 {b} CI Upper"

        d = plot_df.loc[plot_df["time_period"] == year, :].dropna(
            subset=[value_col, lower_col, upper_col]
        ).copy()

        if d.empty:
            continue

        values = d[value_col].to_numpy()
        lower = d[lower_col].to_numpy()
        upper = d[upper_col].to_numpy()

        # Convert CI bounds into asymmetric error distances
        xerr = np.array([
            values - lower,
            upper - values
        ])

        # Position observations around each school centre
        y_pos = np.array([
            school_y[school]
            for school in d["school"]
        ]) + offsets[(year, b)]

        # Legend labels
        if band is None and time_period is None:
            label = f"{b} {year_labels[year]}"
        elif band is None:
            label = b
        else:
            label = year_labels[year]

        ax.errorbar(
            values,
            y_pos,
            xerr=xerr,
            fmt=markers[year],
            color=colours[b],
            markersize=8,
            capsize=3,
            elinewidth=1.4,
            linewidth=0,
            label=label,
            zorder=3
        )

    # --------------------------------------------------
    # Reference lines
    # --------------------------------------------------

    # National P8 benchmark
    ax.axvline(
        0,
        linestyle="--",
        linewidth=1.2,
        color="grey",
        label="_nolegend_"
    )

    # +/- 0.5 reference lines
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

    y = np.arange(len(sort_order)) * school_spacing

    ax.set_yticks(y)
    ax.set_yticklabels(sort_order)

    ax.set_xlabel("Progress 8")
    ax.set_ylabel("")

    title = (
        "Progress 8 by KS2 Prior Attainment"
        if band is None
        else f"Progress 8 — {band} Prior Attainment"
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
        title="Prior Attainment / GCSE Year",
        frameon=True
    )

    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    ax.set_ylim(
        -0.7,
        (len(sort_order) - 1) * school_spacing + 0.7
    )

    plt.tight_layout()

    file_path = config.charts_dir / "p8_by_prior_attainment.png"
    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()
    return None


def plot_by_prior_attainment(
    df: pd.DataFrame,
    band: str | None = None,
    time_period: int | None = None,
    metric: str | None = None,
    save_png: bool = True,
    file_name: str | None = None,
) -> None:
    """
    Plot Progress 8 or Attainment 8 by KS2 prior-attainment band.

    band: None, "Low", "Middle", "High"
    time_period: None, 202223, 202324
    metric: None or "p8" (default), "a8"
    save_png: True (default) or False

    P8 includes 95% confidence intervals.
    """

    # Validate
    band = band.title() if band else None
    metric = metric.lower() if metric else "p8"

    if band not in (None, "Low", "Middle", "High"):
        raise ValueError("band must be None, Low, Middle, or High")

    if time_period not in (None, 202223, 202324):
        raise ValueError("time_period must be None, 202223, or 202324")

    if metric not in ("p8", "a8"):
        raise ValueError("metric must be None, 'p8', or 'a8'")

    bands = ["Low", "Middle", "High"] if band is None else [band]
    years = [202223, 202324] if time_period is None else [time_period]

    prefix = metric.upper()
    metric_name = "Progress 8" if metric == "p8" else "Attainment 8"

    # Prepare data
    cols = ["time_period", "school"]
    overall_col = f"{prefix} Average"

    if overall_col in df.columns:
        cols.append(overall_col)

    for b in bands:
        cols.append(f"{prefix} {b}")

        if metric == "p8":
            cols.extend([
                f"P8 {b} CI Lower",
                f"P8 {b} CI Upper"
            ])

    plot_df = df.loc[:, cols].copy()

    time_period_values = pd.Series(
        pd.to_numeric(plot_df["time_period"], errors="coerce"),
        index=plot_df.index,
    )
    plot_df = plot_df.loc[time_period_values.isin(years), :].copy()
    plot_df["time_period"] = time_period_values.loc[time_period_values.isin(years)]

    numeric_cols = [
        c for c in cols if c not in ("time_period", "school")
    ]

    for column in numeric_cols:
        plot_df[column] = pd.Series(
            pd.to_numeric(plot_df[column], errors="coerce"),
            index=plot_df.index,
        )

    value_cols = [f"{prefix} {b}" for b in bands]

    plot_df = plot_df.dropna(subset=value_cols, how="all")

    if plot_df.empty:
        raise ValueError("No data found for the selected filters.")

    # Sort schools by selected metric, using latest year
    sort_year = 202324 if time_period is None else time_period

    sort_df = plot_df.loc[plot_df["time_period"] == sort_year, :].copy()

    if band is None:
        band_average = sort_df.loc[:, value_cols].mean(axis=1)

        if overall_col in sort_df.columns:
            sort_df["sort_value"] = (
                sort_df[overall_col].fillna(band_average)
            )
        else:
            sort_df["sort_value"] = band_average
    else:
        sort_df["sort_value"] = sort_df[f"{prefix} {band}"]

    sort_order = (
        sort_df.sort_values("sort_value")["school"].tolist()
    )

    other_schools = sorted(
        set(plot_df["school"]) - set(sort_order)
    )

    sort_order = other_schools + sort_order

    # Vertical positioning
    school_spacing = 1.5

    school_y = {
        school: i * school_spacing
        for i, school in enumerate(sort_order)
    }

    # Visual settings
    colours = {
        "Low": "tab:blue",
        "Middle": "tab:orange",
        "High": "tab:green"
    }

    markers = {
        202223: "o",
        202324: "s"
    }

    year_labels = {
        202223: "2022/23",
        202324: "2023/24"
    }

    combinations = [
        (year, b)
        for year in years
        for b in bands
    ]

    offsets_array = (
        np.linspace(-0.20, 0.20, len(combinations))
        if len(combinations) > 1
        else [0.0]
    )

    offsets = dict(zip(combinations, offsets_array))

    # Plot
    fig, ax = plt.subplots(
        figsize=(12, max(7, len(sort_order) * 0.95))
    )

    for year, b in combinations:
        value_col = f"{prefix} {b}"
        lower_col = f"P8 {b} CI Lower"
        upper_col = f"P8 {b} CI Upper"
        required_cols = [value_col]

        if metric == "p8":
            required_cols.extend([lower_col, upper_col])

        d = plot_df.loc[plot_df["time_period"] == year, :].dropna(
            subset=required_cols
        ).copy()

        if d.empty:
            continue

        values = d[value_col].to_numpy()

        y_pos = np.array([
            school_y[school] for school in d["school"]
        ]) + offsets[(year, b)]

        if band is None and time_period is None:
            label = f"{b} {year_labels[year]}"
        elif band is None:
            label = b
        else:
            label = year_labels[year]

        if metric == "p8":
            lower = d[lower_col].to_numpy()
            upper = d[upper_col].to_numpy()

            xerr = np.array([
                values - lower,
                upper - values
            ])

            ax.errorbar(
                values,
                y_pos,
                xerr=xerr,
                fmt=markers[year],
                color=colours[b],
                markersize=8,
                capsize=3,
                elinewidth=1.4,
                linewidth=0,
                label=label,
                zorder=3
            )

        else:
            ax.plot(
                values,
                y_pos,
                linestyle="None",
                marker=markers[year],
                color=colours[b],
                markersize=8,
                label=label,
                zorder=3
            )

    # P8 reference lines
    if metric == "p8":
        ax.axvline(
            0, linestyle="--", linewidth=1.2, color="grey"
        )

        for x in [-0.5, 0.5]:
            ax.axvline(
                x, linestyle=":", linewidth=1, color="grey"
            )

    # Labels
    y = np.arange(len(sort_order)) * school_spacing

    ax.set_yticks(y)
    ax.set_yticklabels(sort_order)

    ax.set_xlabel(metric_name)
    ax.set_ylabel("")

    title = (
        f"{metric_name} by KS2 Prior Attainment"
        if band is None
        else f"{metric_name} — {band} Prior Attainment"
    )

    period_label = (
        "2022/23 and 2023/24"
        if time_period is None
        else year_labels[time_period]
    )

    subtitle = (
        "\n95% Confidence Intervals"
        if metric == "p8"
        else ""
    )

    ax.set_title(
        f"{title}, {period_label}{subtitle}",
        fontsize=14,
        pad=15
    )

    ax.legend(
        title="Prior Attainment / GCSE Year",
        frameon=True
    )

    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    ax.set_ylim(
        -0.7,
        (len(sort_order) - 1) * school_spacing + 0.7
    )

    plt.tight_layout()

    # Set file name unless provided in function call
    if file_name is None:
        file_name = f"{metric}_by_prior_attainment.png"
    file_path = config.charts_dir / file_name

    if save_png:
        fig.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )
        logger.info(f"Saved: {file_path}")
        plt.close(fig)
    else:
        plt.show()
    return None

