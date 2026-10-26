from performance.process_data import get_performance_data as _get_performance_data
from performance.plot_data import plot_performance_data as _plot_performance_data


class PerformancePipeline:
    """A pipeline for processing and plotting performance data."""

    def run(self) -> None:
        """Run the performance data pipeline."""
        self.get_performance_data()
        self.plot_performance_data()

    def get_performance_data(self) -> None:
        """Get the performance data."""
        _get_performance_data()

    def plot_performance_data(self) -> None:
        """Plot the performance data."""
        _plot_performance_data()


def main() -> None:
    """Run the performance data pipeline."""
    performance = PerformancePipeline()
    performance.run()

if __name__ == "__main__":
    main()