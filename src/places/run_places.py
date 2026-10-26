from places.process_data import get_places_data
from places.plot_data import plot_places_data

def main() -> None:
    """Run the places data pipeline."""
    get_places_data()
    plot_places_data()

if __name__ == "__main__":
    main()