"""
Servicio de Geolocalización
Valida ubicación GPS del empleado
"""
from math import radians, cos, sin, asin, sqrt
from dataclasses import dataclass
from typing import Optional

from config import settings


@dataclass
class Coordinates:
    latitude: float
    longitude: float
    accuracy: Optional[float] = None


@dataclass
class LocationResult:
    valid: bool
    distance_meters: float
    within_range: bool
    message: str


class GeoLocationService:
    """Servicio de validación de ubicación"""
    
    def __init__(self):
        self.max_distance = settings.MAX_DISTANCE_METERS
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distancia entre dos puntos GPS en metros
        Fórmula de Haversine
        """
        R = 6371000  # Radio de la Tierra en metros
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def validate_location(
        self,
        user_coords: Coordinates,
        target_coords: Coordinates,
        allowed_radius: int = None
    ) -> LocationResult:
        """
        Valida si el usuario está dentro del rango permitido
        """
        radius = allowed_radius or self.max_distance
        
        # Validar coordenadas
        if not (-90 <= user_coords.latitude <= 90):
            return LocationResult(False, 0, False, "Latitud inválida")
        
        if not (-180 <= user_coords.longitude <= 180):
            return LocationResult(False, 0, False, "Longitud inválida")
        
        # Calcular distancia
        distance = self.haversine(
            user_coords.latitude, user_coords.longitude,
            target_coords.latitude, target_coords.longitude
        )
        
        # Considerar precisión del GPS
        if user_coords.accuracy:
            distance += user_coords.accuracy
        
        within_range = distance <= radius
        
        message = (
            f"✅ Dentro del rango ({distance:.0f}m de {radius}m)" 
            if within_range 
            else f"❌ Fuera de rango ({distance:.0f}m de {radius}m permitidos)"
        )
        
        return LocationResult(
            valid=True,
            distance_meters=round(distance, 2),
            within_range=within_range,
            message=message
        )


# Instancia global
geo_service = GeoLocationService()
