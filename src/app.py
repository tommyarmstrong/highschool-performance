"""Run the performance and places pipelines."""

import argparse

from performance.run_performance import PerformancePipeline
from places.run_places import PlacesPipeline


def main(
    *,
    performance: bool | None = None,
    places: bool | None = None,
    get_data: bool | None = None,
    plot_data: bool | None = None,
) -> None:
    """Run the selected pipelines.

    With no flags, both pipelines get and plot their data. Set ``performance``
    or ``places`` to run only that pipeline. Set ``get_data`` or ``plot_data``
    to run only that step.
    """
    run_performance, run_places = _selected(performance, places)
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


def _selected(first: bool | None, second: bool | None) -> tuple[bool, bool]:
    """Return which of a pair of flags to run.

    When neither flag is set, both run. Otherwise each flag is used as given.
    """
    if first is None and second is None:
        return True, True
    return bool(first), bool(second)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse pipeline and step flags."""
    parser = argparse.ArgumentParser(
        description="Run the performance and places pipelines."
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run the performance pipeline. Omit both pipeline flags to run both.",
    )
    parser.add_argument(
        "--places",
        action="store_true",
        help="Run the places pipeline. Omit both pipeline flags to run both.",
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
        get_data=args.get_data or None,
        plot_data=args.plot_data or None,
    )
