"""
Module de géocodage inverse pour convertir les coordonnées GPS en adresses
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
import time

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="r8it-app")
        
    def get_address_from_coordinates(self, latitude, longitude):
        """
        Convertit des coordonnées GPS en adresse lisible
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude
            
        Returns:
            dict: {
                'address': str,
                'city': str,
                'country': str,
                'place_name': str,
                'place_type': str,
                'success': bool,
                'error': str (si erreur)
            }
        """
        try:
            # Géocodage inverse avec retry
            location = self._reverse_geocode_with_retry(latitude, longitude)
            
            if location:
                address_components = location.raw.get('address', {})
                
                # Extraire les informations importantes
                result = {
                    'success': True,
                    'full_address': location.address,
                    'latitude': latitude,
                    'longitude': longitude
                }
                
                # Extraire les composants d'adresse
                result.update(self._extract_address_components(address_components))
                
                # Déterminer le type de lieu
                result.update(self._determine_place_type(address_components, location.raw))
                
                return result
            else:
                return {
                    'success': False,
                    'error': 'Aucune adresse trouvée pour ces coordonnées'
                }
                
        except Exception as e:
            logger.error(f"Erreur géocodage inverse: {str(e)}")
            return {
                'success': False,
                'error': f'Erreur lors du géocodage: {str(e)}'
            }
    
    def _reverse_geocode_with_retry(self, latitude, longitude, max_retries=3):
        """
        Géocodage inverse avec retry en cas d'erreur
        """
        for attempt in range(max_retries):
            try:
                location = self.geolocator.reverse(f"{latitude}, {longitude}", timeout=10)
                return location
            except GeocoderTimedOut:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logger.error("Timeout lors du géocodage après plusieurs tentatives")
                    return None
            except GeocoderServiceError as e:
                logger.error(f"Erreur service géocodage: {str(e)}")
                return None
        return None
    
    def _extract_address_components(self, address_components):
        """
        Extrait les composants d'adresse importants
        """
        return {
            'street_number': address_components.get('house_number', ''),
            'street_name': address_components.get('road', ''),
            'neighborhood': address_components.get('neighbourhood', ''),
            'city': address_components.get('city') or address_components.get('town') or address_components.get('village', ''),
            'postal_code': address_components.get('postcode', ''),
            'state': address_components.get('state', ''),
            'country': address_components.get('country', ''),
            'country_code': address_components.get('country_code', '')
        }
    
    def _determine_place_type(self, address_components, raw_data):
        """
        Détermine le type de lieu (restaurant, hôtel, magasin, etc.)
        """
        place_type = 'unknown'
        place_name = ''
        
        # Vérifier les types de lieux dans les données OSM
        osm_type = raw_data.get('type', '')
        osm_class = raw_data.get('class', '')
        
        # Mapping des types OSM vers nos catégories
        type_mapping = {
            'restaurant': 'restaurant',
            'cafe': 'restaurant',
            'fast_food': 'restaurant',
            'hotel': 'hotel',
            'motel': 'hotel',
            'hostel': 'hotel',
            'shop': 'magasin',
            'supermarket': 'magasin',
            'mall': 'magasin',
            'tourism': 'attraction',
            'attraction': 'attraction',
            'museum': 'attraction',
            'hospital': 'service',
            'school': 'service',
            'university': 'service'
        }
        
        # Déterminer le type de lieu
        if osm_type in type_mapping:
            place_type = type_mapping[osm_type]
        elif osm_class in type_mapping:
            place_type = type_mapping[osm_class]
        
        # Extraire le nom du lieu
        display_name_parts = raw_data.get('display_name', '').split(',')
        if display_name_parts:
            place_name = display_name_parts[0].strip()
        
        # Vérifier si c'est un lieu commercial spécifique
        amenity = address_components.get('amenity', '')
        if amenity:
            if amenity in ['restaurant', 'cafe', 'fast_food']:
                place_type = 'restaurant'
            elif amenity in ['hotel', 'motel']:
                place_type = 'hotel'
            elif amenity in ['shop', 'supermarket']:
                place_type = 'magasin'
        
        return {
            'place_type': place_type,
            'place_name': place_name,
            'osm_type': osm_type,
            'osm_class': osm_class
        }
    
    def get_nearby_places(self, latitude, longitude, radius_km=1):
        """
        Trouve les lieux d'intérêt à proximité des coordonnées
        (Fonctionnalité future - pour l'instant retourne une liste vide)
        """
        # TODO: Implémenter la recherche de lieux à proximité
        # Pourrait utiliser l'API Overpass d'OpenStreetMap
        return []

# Instance globale du service
location_service = LocationService()

