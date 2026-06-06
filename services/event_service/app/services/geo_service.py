import math


class GeoService:
    """Сервис для работы с геолокацией"""

    @staticmethod
    def haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Расстояние между двумя точками в километрах"""
        R = 6371  # Радиус Земли в км

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def get_bounding_box(
        lat: float, lon: float, radius_km: float
    ) -> tuple[float, float, float, float]:
        """Вычисляем bbox для предфильтрации на уровне БД"""
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

        return (
            lat - lat_delta,
            lat + lat_delta,
            lon - lon_delta,
            lon + lon_delta
        )
