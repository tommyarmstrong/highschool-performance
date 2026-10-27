from geopy.geocoders import ArcGIS
from geopy.location import Location

from config.config import CatchmentDistances, SchoolCoords, get_catchment_distances, get_school_addresses
from shared_funcitons import logger


# Get the school addresses and catchment distances
school_locations: dict = get_school_addresses()
catchment_distances: CatchmentDistances = get_catchment_distances()


class CatchmentProcessor:
    """Processor for catchment data."""
    def __init__(self):
        self.school_locations: dict[str, str] = school_locations
        self.school_coords: SchoolCoords = {}


    def _geocode_addresses(self) -> SchoolCoords:
        """Load and process the catchment data."""
        # Geocode addresses, then reuse the coordinates
        geocoder = ArcGIS()
        geocoder.timeout = 15
        school_coords = {}

        logger.info(f"Geocoding {len(self.school_locations)} school addresses")

        for school, address in self.school_locations.items():
            result = geocoder.geocode(address)

            if isinstance(result, Location):
                school_coords[school] = (
                    result.latitude,
                    result.longitude
                )
                logger.info(f"Geocoded address for {school}: {result.latitude}, {result.longitude}")

            else:
                logger.warning(f"Could not locate: {school}")

        return school_coords


    def _load_catchment_distances(self) -> CatchmentDistances:
        """Load cut-off distances with numeric year keys."""
        raw: dict[str, dict[str, float | int | None]] = get_catchment_distances()
        catchment_dists: CatchmentDistances = {}
        for year, distances in raw.items():
            parsed: dict[str, float | None] = {}
            for school, miles in distances.items():
                parsed[school] = None if miles is None else float(miles)
            catchment_dists[int(year)] = parsed
        return catchment_dists


    def process_data(self) -> tuple[SchoolCoords, CatchmentDistances]:
        """Process the school geocode data."""
        school_coords = self._geocode_addresses()
        catchment_distances = self._load_catchment_distances()
        return school_coords, catchment_distances


def get_catchment_data() -> tuple[SchoolCoords, CatchmentDistances] | None:
    """Get the catchment data."""
    school_coords, catchment_distances = CatchmentProcessor().process_data()
    if school_coords is None:
        logger.error("No catchments dataframe was returned")
        return None
    if catchment_distances is None:
        logger.error("No catchment distances were returned")
        return None

    

    return school_coords, catchment_distances


