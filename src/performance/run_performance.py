from performance.process_data import get_performance_data
from performance.plot_data import plot_performance_data

def main() -> None:
    """Run the performance data pipeline."""
    get_performance_data()
    plot_performance_data()

if __name__ == "__main__":
    main()