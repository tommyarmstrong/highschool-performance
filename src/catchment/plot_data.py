import math
import re

import folium
import matplotlib.pyplot as plt

from catchment.catchment_helpers import save_folium_png
from config.config import CatchmentDistances, SchoolCoords, get_config
from shared_funcitons import logger

config = get_config()


def _filename_stem(name: str) -> str:
    """Return a filename-safe school name."""
    return re.sub(r"[^A-Za-z0-9_-]", "", name.replace(" ", "_"))


def compare_school_catchments(
    school: str,
    cutoffs: CatchmentDistances,
    school_coords: SchoolCoords,
    save_png: bool = True,
) -> folium.Map:
    """
    Compare a school's admissions cut-off distances across years.

    Parameters
    ----------
    school : str
        School name, e.g. "Highgate Wood".
    cutoffs : dict
        {year: {school: distance_in_miles}}
    school_coords : dict
        {school: (latitude, longitude)}
    """

    if school not in school_coords:
        raise ValueError(f"No coordinates found for {school}")

    data: dict[int, float] = {}
    for year, distances in sorted(cutoffs.items()):
        miles = distances.get(school)
        if miles is not None:
            data[year] = miles

    if not data:
        raise ValueError(f"No published cut-off distances for {school}")

    lat, lon = school_coords[school]

    colors = [
        "blue", "red", "green", "purple",
        "orange", "darkred"
    ]

    # Interactive map
    m = folium.Map(
        location=[lat, lon],
        zoom_start=13,
        tiles=None
    )

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Street_Map/MapServer/tile/"
            "{z}/{y}/{x}"
        ),
        attr="Tiles © Esri",
        name="Street map"
    ).add_to(m)

    for i, (year, miles) in enumerate(data.items()):
        color = colors[i % len(colors)]

        layer = folium.FeatureGroup(
            name=f"{year}: {miles:.3f} miles",
            show=True
        )

        folium.Circle(
            location=[lat, lon],
            radius=miles * 1609.344,
            color=color,
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.08,
            tooltip=f"{year}: {miles:.3f} miles"
        ).add_to(layer)

        layer.add_to(m)

    folium.Marker(
        location=[lat, lon],
        tooltip=school,
        popup=school,
        icon=folium.Icon(color="black", icon="info-sign")
    ).add_to(m)

    # Fit map to largest circle
    max_miles = max(data.values())
    radius_km = max_miles * 1.609344

    lat_delta = radius_km / 111
    lon_delta = radius_km / (
        111 * abs(math.cos(math.radians(lat)))
    )

    m.fit_bounds([
        [lat - lat_delta, lon - lon_delta],
        [lat + lat_delta, lon + lon_delta]
    ])

    folium.LayerControl(collapsed=False).add_to(m)

    # Line chart
    fig, ax = plt.subplots(figsize=(9, 4))

    ax.plot(
        list(data.keys()),
        list(data.values()),
        marker="o",
        linewidth=2.5,
        markersize=8
    )

    for year, miles in data.items():
        ax.annotate(
            f"{miles:.3f}",
            (year, miles),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center"
        )

    ax.set_title(f"{school} — Admissions Cut-off Distance")
    ax.set_xlabel("Admissions year")
    ax.set_ylabel("Distance (miles)")
    ax.set_xticks(list(data.keys()))
    ax.grid(alpha=0.2)

    plt.tight_layout()

    stem = _filename_stem(school)
    if save_png:
        chart_path = config.charts_dir / f"{stem}_catchment_distance.png"
        fig.savefig(chart_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved plot to {chart_path}")
        plt.close(fig)
        save_folium_png(m, config.charts_dir / f"{stem}_catchments.png")
    else:
        plt.show()

    return m


def plot_catchments(
    cutoffs: CatchmentDistances,
    school_coords: SchoolCoords,
    year: int = 2026,
    schools: list[str] | str | None = None,
    save_png: bool = True,
    padding: int = 30,
) -> folium.Map:
    """
    Plot historical school admissions cut-off circles.

    Parameters
    ----------
    cutoffs : dict
        {year: {school: distance_in_miles}}
    school_coords : dict
        {school: (latitude, longitude)}
    year : int
        Admissions year (2024, 2025 or 2026).
    schools : list[str] | str | None
        Schools to display. None displays all schools
        with available cut-off distances.
    save_png : bool
        Whether to automatically save the map as a PNG.
    padding : int
        Extra map padding in pixels around the outermost circles.
    """

    if year not in cutoffs:
        raise ValueError(
            f"No cut-off data for {year}. "
            f"Available years: {sorted(cutoffs)}"
        )

    if isinstance(schools, str):
        schools = [schools]

    # Filter schools with available cut-off distances
    distances: dict[str, float] = {}
    for school, miles in cutoffs[year].items():
        if miles is None or miles <= 0:
            continue
        if schools is not None and school not in schools:
            continue
        distances[school] = miles

    if not distances:
        raise ValueError(
            f"No available cut-off distances for "
            f"the selected schools in {year}."
        )

    # Check that coordinates are available
    missing = [
        school
        for school in distances
        if school not in school_coords
    ]

    if missing:
        raise ValueError(
            f"Missing coordinates for: {missing}. "
            "Rerun the school geocoding code."
        )

    # Consistent colours for schools
    colors = [
        "blue",
        "red",
        "green",
        "purple",
        "orange",
        "darkred",
        "cadetblue",
        "darkgreen",
        "pink",
    ]

    all_schools = sorted({
        school
        for year_data in cutoffs.values()
        for school in year_data
    })

    school_colors = {
        school: colors[i % len(colors)]
        for i, school in enumerate(all_schools)
    }

    # Centre map on the average school location
    centre_lat = sum(
        school_coords[s][0] for s in distances
    ) / len(distances)

    centre_lon = sum(
        school_coords[s][1] for s in distances
    ) / len(distances)

    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=11,
        width=1400,
        height=1000,
        tiles=None,
        control_scale=True,
    )

    # Esri tiles (avoids OpenStreetMap tile restrictions)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Street_Map/MapServer/tile/"
            "{z}/{y}/{x}"
        ),
        attr="Tiles © Esri",
        name="Street map",
        overlay=False,
    ).add_to(m)

    circle_bounds = []

    for school, miles in distances.items():

        lat, lon = school_coords[school]
        color = school_colors[school]
        radius_m = miles * 1609.344

        # Create a separate toggleable layer for each school
        layer = folium.FeatureGroup(
            name=f"{school}: {miles:.3f} miles",
            show=True,
        )

        folium.Circle(
            location=[lat, lon],
            radius=radius_m,
            color=color,
            weight=3,
            opacity=0.9,
            fill=True,
            fill_color=color,
            fill_opacity=0.10,
            tooltip=f"{school} ({year}): {miles:.3f} miles",
            popup=(
                f"<b>{school}</b><br>"
                f"Admissions year: {year}<br>"
                f"Cut-off distance: {miles:.4f} miles"
            ),
        ).add_to(layer)

        folium.Marker(
            location=[lat, lon],
            tooltip=school,
            popup=f"<b>{school}</b>",
            icon=folium.Icon(
                color=color,
                icon="education",
                prefix="glyphicon",
            ),
        ).add_to(layer)

        layer.add_to(m)

        # Calculate bounds of the entire circle,
        # not just the school centre
        radius_km = radius_m / 1000

        lat_delta = radius_km / 111.32
        lon_delta = radius_km / (
            111.32 * math.cos(math.radians(lat))
        )

        circle_bounds.extend([
            [lat - lat_delta, lon - lon_delta],
            [lat + lat_delta, lon + lon_delta],
        ])

    # Fit to the full extent of all catchment circles
    m.fit_bounds(
        circle_bounds,
        padding=(padding, padding),
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(m)

    # Save PNG automatically
    if save_png:
        if schools is None:
            filename = f"all_schools_catchments_{year}.png"
        else:
            school_names = "_".join(
                _filename_stem(s) for s in sorted(distances)
            )
            filename = f"{school_names}_catchments_{year}.png"

        save_folium_png(m, config.charts_dir / filename)

    return m


def plot_catchment_data(
    school_coords: SchoolCoords | None,
    catchment_distances: CatchmentDistances | None,
    save_png: bool = True
) -> None:
    """Plot catchment maps and per-school cut-off charts."""
    if not school_coords:
        logger.error("No school coordinates were found")
        return
    if not catchment_distances:
        logger.error("No catchment distances were found")
        return

    for year in sorted(catchment_distances):
        has_distance = any(
            miles is not None and miles > 0
            for miles in catchment_distances[year].values()
        )
        if has_distance:
            plot_catchments(
                catchment_distances,
                school_coords,
                year=year,
                save_png=save_png,
            )

    schools = sorted({
        school
        for distances in catchment_distances.values()
        for school, miles in distances.items()
        if miles is not None and school in school_coords
    })
    for school in schools:
        compare_school_catchments(
            school,
            catchment_distances,
            school_coords,
            save_png=save_png,
        )
