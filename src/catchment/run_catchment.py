from catchment.process_data import get_catchment_data as _get_catchment_data
from catchment.plot_data import plot_catchment_data as _plot_catchment_data
from config.config import CatchmentDistances, SchoolCoords


class CatchmentPipeline:
    """A pipeline for processing and plotting catchment data."""
    def __init__(self):
        self.school_coords: SchoolCoords | None = None
        self.catchment_distances: CatchmentDistances | None = None


    def run(self) -> None:
        """Run the catchment data pipeline."""
        data = self.get_catchment_data()
        if data is None:
            return
        self.school_coords, self.catchment_distances = data
        self.plot_catchment_data()


    def get_catchment_data(self) -> tuple[SchoolCoords, CatchmentDistances] | None:
        """Get the catchment data."""
        return _get_catchment_data()


    def plot_catchment_data(self) -> None:
        """Plot the catchment data."""
        _plot_catchment_data(
            school_coords=self.school_coords,
            catchment_distances=self.catchment_distances,
        )


def main() -> None:
    """Run the catchment data pipeline."""
    catchment = CatchmentPipeline()
    catchment.run()

if __name__ == "__main__":
    main()