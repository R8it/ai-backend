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
    Analyse une image avec GPT-4 Vision pour détecter un commerce/lieu pour R8it
    """
    try:
        # Préparer le prompt spécialisé pour R8it
        prompt = """
        Tu es un assistant IA spécialisé dans l'analyse d'expériences pour l'application R8it.
        
        R8it permet aux utilisateurs de noter et commenter leurs expériences en prenant simplement une photo.
        
        Analyse cette image et identifie PRÉCISÉMENT ce que tu vois :
        
        TYPES D'EXPÉRIENCES À DÉTECTER :
        🍽️ RESTAURANTS/CAFÉS : Plats, menus, devantures, intérieurs de restaurants
        🎬 CINÉMAS/SPECTACLES : Affiches de films, salles de cinéma, théâtres, événements
        🏛️ LIEUX TOURISTIQUES : Monuments, musées, sites historiques, attractions
        🏪 COMMERCES : Magasins, boutiques, enseignes, produits
        🏢 SERVICES : Administrations, banques, services publics
        ⚠️ ARNAQUES : SMS frauduleux, emails suspects, faux sites web
        🏠 PRODUITS : Articles achetés, emballages, étiquettes de marques
        
        INSTRUCTIONS SPÉCIFIQUES :
        - Lis TOUS les textes visibles (enseignes, menus, étiquettes, noms de marques)
        - Identifie le lieu/produit/service EXACT si possible
        - Pour les restaurants : mentionne le nom exact, le type de cuisine
        - Pour les produits : mentionne la marque et le type de produit
        - Pour les lieux : donne le nom précis si visible
        - Pour les arnaques : détecte les signes suspects (fautes, urgence, liens douteux)
        
        Réponds UNIQUEMENT avec un objet JSON valide :
        {
            "businessName": "NOM EXACT du lieu/produit/service détecté",
            "businessType": "Type précis (Restaurant Italien, Cinéma, Huile d'olive, etc.)",
            "address": "Adresse/localisation si visible, sinon 'Localisation détectée'",
            "category": "Catégorie détaillée basée sur ce que tu vois",
            "icon": "Emoji le plus approprié",
            "suggestedRating": 4,
            "suggestedReview": "Avis naturel basé sur l'apparence/contexte de l'image",
            "quickSuggestions": ["mot-clé1", "mot-clé2", "mot-clé3", "mot-clé4"],
            "confidence": 0.95
        }
        
        EXEMPLES DE BONNES RÉPONSES :
        - Huile d'olive Terra Delyssa → "Terra Delyssa", "Huile d'olive bio", "🫒"
        - Restaurant avec enseigne → "Le Petit Bistrot", "Restaurant français", "🍽️"
        - Affiche de cinéma → "Cinéma Grand Rex", "Salle de cinéma", "🎬"
        - SMS suspect → "Arnaque SMS détectée", "Tentative de fraude", "⚠️"
        
        RÈGLES IMPORTANTES :
        - Si tu vois du texte, utilise-le pour identifier précisément
        - Les suggestions doivent être des mots-clés courts et pertinents
        - L'avis doit être naturel et contextuel
        - La note doit refléter l'apparence/qualité visible (1-5)
        - Pour les arnaques : note=1, avis d'alerte
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
            max_tokens=600,
            temperature=0.2  # Réduire la température pour plus de précision
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
        
        # Validation et valeurs par défaut améliorées
        result.setdefault('businessName', 'Lieu détecté')
        result.setdefault('businessType', 'Expérience')
        result.setdefault('address', 'Localisation détectée')
        result.setdefault('category', 'Expérience/Service')
        result.setdefault('icon', '📍')
        result.setdefault('suggestedRating', 4)
        result.setdefault('suggestedReview', 'Expérience intéressante détectée par R8it.')
        result.setdefault('quickSuggestions', ['intéressant', 'à tester', 'sympa', 'recommandé'])
        result.setdefault('confidence', 0.8)
        
        return result
        
    except Exception as e:
        print(f"Erreur GPT-4 Vision: {e}")
        # Fallback amélioré en cas d'erreur
        return {
            "businessName": "Lieu détecté",
            "businessType": "Expérience",
            "address": "Localisation analysée par IA",
            "category": "Expérience/Service",
            "icon": "📍",
            "suggestedRating": 4,
            "suggestedReview": "Lieu intéressant détecté par R8it. Partagez votre expérience !",
            "quickSuggestions": ["expérience unique", "à découvrir", "intéressant", "recommandé"],
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

