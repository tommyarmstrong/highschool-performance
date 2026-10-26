from places.plot_data import plot_places_data as _plot_places_data
from places.process_data import get_places_data as _get_places_data


class PlacesPipeline:
    """A pipeline for processing and plotting places data."""

    def run(self) -> None:
        """Run the places data pipeline."""
        self.get_places_data()
        self.plot_places_data()

    def get_places_data(self) -> None:
        """Get the places data."""
        _get_places_data()

    def plot_places_data(self) -> None:
        """Plot the places data."""
        _plot_places_data()
        

def main() -> None:
    """Run the places data pipeline."""
    places = PlacesPipeline()
    places.run()

if __name__ == "__main__":
    main()