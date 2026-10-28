"""Run the performance, places, and slide pipelines."""

import argparse

from performance.run_performance import PerformancePipeline
from places.run_places import PlacesPipeline
from report.generate_slides import generate_slides


def main(
    *,
    performance: bool | None = None,
    places: bool | None = None,
    slides: bool | None = None,
    get_data: bool | None = None,
    plot_data: bool | None = None,
) -> None:
    """Run the selected pipelines.

    With no flags, both data pipelines get and plot their data, then the slides
    are built. Set ``performance``, ``places``, or ``slides`` to run only those
    pipelines. Set ``get_data`` or ``plot_data`` to run only that step. Slides
    are skipped on a get-data-only run unless ``slides`` is set.
    """
    run_performance, run_places, run_slides = _selected(performance, places, slides)
    run_get, run_plot = _selected(get_data, plot_data)

    if run_performance:
        performance_pipeline = PerformancePipeline()
        if run_get:
            performance_pipeline.get_performance_data()
        if run_plot:
            performance_pipeline.plot_performance_data()

    if run_places:
        places_pipeline = PlacesPipeline()
        if run_get:
            places_pipeline.get_places_data()
        if run_plot:
            places_pipeline.plot_places_data()

    if run_slides and (slides is True or run_plot):
        generate_slides()


def _selected(*flags: bool | None) -> tuple[bool, ...]:
    """Return which flags to run.

    When every flag is unset, all of them run. Otherwise each flag is used as given.
    """
    if all(flag is None for flag in flags):
        return tuple(True for _ in flags)
    return tuple(bool(flag) for flag in flags)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse pipeline and step flags."""
    parser = argparse.ArgumentParser(
        description="Run the performance, places, and slide pipelines."
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run the performance pipeline. Omit the pipeline flags to run all of them.",
    )
    parser.add_argument(
        "--places",
        action="store_true",
        help="Run the places pipeline. Omit the pipeline flags to run all of them.",
    )
    parser.add_argument(
        "--slides",
        action="store_true",
        help="Build the slide deck. Omit the pipeline flags to run all of them.",
    )
    parser.add_argument(
        "--get-data",
        action="store_true",
        help="Get the data. Omit both step flags to get and plot.",
    )
    parser.add_argument(
        "--plot-data",
        action="store_true",
        help="Plot the data. Omit both step flags to get and plot.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    main(
        performance=args.performance or None,
        places=args.places or None,
        slides=args.slides or None,
        get_data=args.get_data or None,
        plot_data=args.plot_data or None,
    )
