import os
import base64
import json
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from openai import OpenAI
from dotenv import load_dotenv
import io
from PIL import Image

# Charger les variables d'environnement
load_dotenv()

image_analysis_bp = Blueprint('image_analysis', __name__)

# Initialiser le client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-test-key'))

def analyze_image_with_gpt4_vision(image_data):
    """
    Analyse une image avec GPT-4 Vision pour détecter un commerce/lieu
    """
    try:
        # Préparer le prompt pour l'analyse
        prompt = """
        Analysez cette image et identifiez le commerce, lieu ou service visible.
        
        Répondez UNIQUEMENT avec un objet JSON valide contenant :
        {
            "businessName": "Nom du commerce/lieu détecté",
            "businessType": "Type (Restaurant, Café, Magasin, Cinéma, etc.)",
            "address": "Adresse estimée ou zone géographique",
            "category": "Catégorie détaillée",
            "icon": "Emoji représentatif",
            "suggestedRating": 4,
            "suggestedReview": "Avis suggéré basé sur ce que vous voyez",
            "quickSuggestions": ["suggestion1", "suggestion2", "suggestion3", "suggestion4"],
            "confidence": 0.85
        }
        
        Instructions spéciales :
        - Si c'est un SMS/message d'arnaque : businessName="Arnaque détectée", icon="⚠️", suggestedRating=1
        - Si c'est un restaurant : icon="🍽️" ou "⭐" pour les restaurants étoilés
        - Si c'est un cinéma/événement : icon="🎬"
        - Si c'est du tourisme : icon="🏛️" ou "🚣" ou "🗼"
        - Les suggestions doivent être courtes (2-3 mots max)
        - L'avis doit être naturel et contextuel
        - La note doit être entre 1 et 5
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        # Extraire la réponse JSON
        response_text = response.choices[0].message.content.strip()
        
        # Nettoyer la réponse pour extraire le JSON
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        # Parser le JSON
        result = json.loads(response_text)
        
        # Validation et valeurs par défaut
        result.setdefault('businessName', 'Commerce détecté')
        result.setdefault('businessType', 'Commerce')
        result.setdefault('address', 'Adresse détectée par IA')
        result.setdefault('category', 'Commerce/Service')
        result.setdefault('icon', '🏪')
        result.setdefault('suggestedRating', 4)
        result.setdefault('suggestedReview', 'Expérience analysée par IA')
        result.setdefault('quickSuggestions', ['expérience unique', 'recommandé', 'service correct', 'à découvrir'])
        result.setdefault('confidence', 0.8)
        
        return result
        
    except Exception as e:
        print(f"Erreur GPT-4 Vision: {e}")
        # Fallback en cas d'erreur
        return {
            "businessName": "Commerce détecté",
            "businessType": "Commerce",
            "address": "Lieu analysé par IA",
            "category": "Commerce/Service",
            "icon": "🏪",
            "suggestedRating": 4,
            "suggestedReview": "Lieu intéressant détecté par notre IA. N'hésitez pas à partager votre expérience !",
            "quickSuggestions": ["expérience unique", "recommandé", "service correct", "à découvrir"],
            "confidence": 0.5,
            "error": str(e)
        }

@image_analysis_bp.route('/analyze-image', methods=['POST'])
@cross_origin()
def analyze_image():
    """
    Endpoint pour analyser une image avec GPT-4 Vision
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'Image data required'}), 400
        
        # Extraire les données de l'image (base64)
        image_data = data['image']
        
        # Supprimer le préfixe data:image/...;base64, si présent
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Analyser l'image avec GPT-4 Vision
        result = analyze_image_with_gpt4_vision(image_data)
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        print(f"Erreur dans analyze_image: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@image_analysis_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Endpoint de vérification de santé
    """
    return jsonify({
        'status': 'healthy',
        'service': 'R8it Image Analysis API',
        'version': '1.0.0'
    })

