"""
Module d'extraction GPS à partir des métadonnées EXIF des images
"""
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import logging

logger = logging.getLogger(__name__)

def extract_gps_from_image(image_data):
    """
    Extrait les coordonnées GPS d'une image à partir des métadonnées EXIF
    
    Args:
        image_data: Données binaires de l'image
        
    Returns:
        dict: {
            'latitude': float,
            'longitude': float,
            'has_gps': bool,
            'error': str (si erreur)
        }
    """
    try:
        # Méthode 1: Utiliser PIL pour extraire les données EXIF
        image = Image.open(io.BytesIO(image_data))
        exif_data = image._getexif()
        
        if exif_data is not None:
            gps_info = {}
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for gps_tag in value:
                        sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                        gps_info[sub_decoded] = value[gps_tag]
            
            if gps_info:
                lat, lon = _convert_gps_to_decimal(gps_info)
                if lat is not None and lon is not None:
                    return {
                        'latitude': lat,
                        'longitude': lon,
                        'has_gps': True
                    }
        
        # Méthode 2: Utiliser exifread comme fallback
        image_data_io = io.BytesIO(image_data)
        tags = exifread.process_file(image_data_io)
        
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')
        
        if all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
            lat = _convert_to_degrees(gps_latitude, gps_latitude_ref)
            lon = _convert_to_degrees(gps_longitude, gps_longitude_ref)
            
            return {
                'latitude': lat,
                'longitude': lon,
                'has_gps': True
            }
        
        return {
            'has_gps': False,
            'error': 'Aucune donnée GPS trouvée dans l\'image'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction GPS: {str(e)}")
        return {
            'has_gps': False,
            'error': f'Erreur lors de l\'extraction GPS: {str(e)}'
        }

def _convert_gps_to_decimal(gps_info):
    """
    Convertit les coordonnées GPS du format EXIF en décimal
    """
    try:
        lat = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')
        
        if lat and lon and lat_ref and lon_ref:
            latitude = _dms_to_decimal(lat, lat_ref)
            longitude = _dms_to_decimal(lon, lon_ref)
            return latitude, longitude
            
    except Exception as e:
        logger.error(f"Erreur conversion GPS: {str(e)}")
        
    return None, None

def _dms_to_decimal(dms, ref):
    """
    Convertit les coordonnées DMS (Degrees, Minutes, Seconds) en décimal
    """
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        if ref in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    except:
        return None

def _convert_to_degrees(value, ref):
    """
    Convertit les coordonnées GPS exifread en degrés décimaux
    """
    try:
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        
        decimal = d + (m / 60.0) + (s / 3600.0)
        
        if ref.values[0] in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    except:
        return None

