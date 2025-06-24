"""
Route API pour l'extraction GPS et la géolocalisation
"""
from flask import Blueprint, request, jsonify
import logging
import base64
import io
from ..utils.gps_extractor import extract_gps_from_image
from ..utils.location_service import location_service

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création du blueprint
location_bp = Blueprint('location', __name__)

@location_bp.route('/extract-location', methods=['POST'])
def extract_location():
    """
    Extrait la localisation GPS d'une image et retourne l'adresse
    
    Expected JSON:
    {
        "image": "base64_encoded_image_data"
    }
    
    Returns:
    {
        "success": bool,
        "has_gps": bool,
        "location": {
            "latitude": float,
            "longitude": float,
            "address": str,
            "city": str,
            "country": str,
            "place_name": str,
            "place_type": str
        },
        "error": str (si erreur)
    }
    """
    try:
        # Vérifier que la requête contient des données JSON
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400
        
        data = request.get_json()
        
        # Vérifier que l'image est présente
        if 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'Champ "image" manquant dans la requête'
            }), 400
        
        image_data_b64 = data['image']
        
        # Décoder l'image base64
        try:
            # Supprimer le préfixe data:image/... si présent
            if ',' in image_data_b64:
                image_data_b64 = image_data_b64.split(',')[1]
            
            image_data = base64.b64decode(image_data_b64)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Erreur lors du décodage de l\'image: {str(e)}'
            }), 400
        
        # Extraire les coordonnées GPS
        logger.info("Extraction des coordonnées GPS...")
        gps_result = extract_gps_from_image(image_data)
        
        if not gps_result.get('has_gps', False):
            return jsonify({
                'success': True,
                'has_gps': False,
                'message': 'Aucune donnée GPS trouvée dans cette image',
                'error': gps_result.get('error', 'Pas de données GPS')
            })
        
        # Obtenir l'adresse à partir des coordonnées
        latitude = gps_result['latitude']
        longitude = gps_result['longitude']
        
        logger.info(f"Géocodage inverse pour: {latitude}, {longitude}")
        location_result = location_service.get_address_from_coordinates(latitude, longitude)
        
        if not location_result.get('success', False):
            return jsonify({
                'success': True,
                'has_gps': True,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'location': None,
                'error': f'Impossible de déterminer l\'adresse: {location_result.get("error", "Erreur inconnue")}'
            })
        
        # Construire la réponse complète
        response = {
            'success': True,
            'has_gps': True,
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            },
            'location': {
                'full_address': location_result.get('full_address', ''),
                'street_number': location_result.get('street_number', ''),
                'street_name': location_result.get('street_name', ''),
                'neighborhood': location_result.get('neighborhood', ''),
                'city': location_result.get('city', ''),
                'postal_code': location_result.get('postal_code', ''),
                'state': location_result.get('state', ''),
                'country': location_result.get('country', ''),
                'country_code': location_result.get('country_code', ''),
                'place_name': location_result.get('place_name', ''),
                'place_type': location_result.get('place_type', 'unknown'),
                'osm_type': location_result.get('osm_type', ''),
                'osm_class': location_result.get('osm_class', '')
            }
        }
        
        logger.info(f"Localisation trouvée: {location_result.get('place_name', 'Lieu inconnu')} à {location_result.get('city', 'Ville inconnue')}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de localisation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@location_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de vérification de santé pour le service de géolocalisation
    """
    return jsonify({
        'status': 'healthy',
        'service': 'location-extraction',
        'version': '1.0.0'
    })

# Endpoint pour tester avec des coordonnées directes
@location_bp.route('/geocode', methods=['POST'])
def geocode_coordinates():
    """
    Teste le géocodage inverse avec des coordonnées directes
    
    Expected JSON:
    {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({
                'success': False,
                'error': 'Latitude et longitude requises'
            }), 400
        
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        
        location_result = location_service.get_address_from_coordinates(latitude, longitude)
        
        return jsonify(location_result)
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Latitude et longitude doivent être des nombres'
        }), 400
    except Exception as e:
        logger.error(f"Erreur géocodage: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

