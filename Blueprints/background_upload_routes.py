"""
Blueprint pour l'upload et la gestion des images de fond pour avatars
"""
from flask import Blueprint, request, jsonify
import logging
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from werkzeug.utils import secure_filename
import uuid

logger = logging.getLogger(__name__)

background_bp = Blueprint('background', __name__, url_prefix='/background')

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_blob_service_client():
    """Récupère le client Blob Service"""
    connection_string = os.getenv('BLOB_CONNECTION_STRING')
    if not connection_string:
        raise ValueError("BLOB_CONNECTION_STRING non configurée")
    return BlobServiceClient.from_connection_string(connection_string)

@background_bp.route('/api/upload', methods=['POST'])
def upload_background():
    """
    Upload une image de fond vers Azure Blob Storage
    """
    try:
        # Vérifier qu'un fichier est présent
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier fourni'
            }), 400
        
        file = request.files['file']
        
        # Vérifier que le fichier a un nom
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nom de fichier vide'
            }), 400
        
        # Vérifier l'extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Extension non autorisée. Utilisez: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Sécuriser le nom de fichier et ajouter un UUID pour éviter les collisions
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Récupérer le client Blob
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client("background")
        
        # Créer le container s'il n'existe pas
        try:
            container_client.get_container_properties()
        except Exception:
            logger.info("📦 Création du container 'background'...")
            container_client = blob_service_client.create_container(
                name="background",
                public_access='blob'
            )
        
        # Upload du fichier
        blob_client = container_client.get_blob_client(unique_filename)
        
        # Déterminer le content type
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        content_settings = ContentSettings(
            content_type=content_type_map.get(file_extension, 'image/jpeg'),
            cache_control='public, max-age=31536000'  # Cache 1 an
        )
        
        blob_client.upload_blob(
            file.read(),
            overwrite=True,
            content_settings=content_settings
        )
        
        blob_url = blob_client.url
        
        logger.info(f"✅ Image uploadée: {unique_filename} -> {blob_url}")
        
        return jsonify({
            'success': True,
            'url': blob_url,
            'filename': unique_filename,
            'original_filename': original_filename
        })
        
    except Exception as e:
        logger.exception("Erreur upload image de fond")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@background_bp.route('/api/list', methods=['GET'])
def list_backgrounds():
    """
    Liste toutes les images de fond disponibles
    """
    try:
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client("background")
        
        # Vérifier si le container existe
        try:
            container_client.get_container_properties()
        except Exception:
            return jsonify({
                'success': True,
                'backgrounds': [],
                'total_count': 0
            })
        
        # Lister tous les blobs
        blob_list = container_client.list_blobs()
        
        backgrounds = []
        for blob in blob_list:
            blob_client = container_client.get_blob_client(blob.name)
            backgrounds.append({
                'filename': blob.name,
                'url': blob_client.url,
                'size': blob.size,
                'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
            })
        
        logger.info(f"📋 {len(backgrounds)} images de fond trouvées")
        
        return jsonify({
            'success': True,
            'backgrounds': backgrounds,
            'total_count': len(backgrounds)
        })
        
    except Exception as e:
        logger.exception("Erreur listage images de fond")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@background_bp.route('/api/delete/<filename>', methods=['DELETE'])
def delete_background(filename):
    """
    Supprime une image de fond
    """
    try:
        # Sécuriser le nom de fichier
        filename = secure_filename(filename)
        
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client("background")
        blob_client = container_client.get_blob_client(filename)
        
        # Supprimer le blob
        blob_client.delete_blob()
        
        logger.info(f"🗑️ Image supprimée: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Image {filename} supprimée avec succès'
        })
        
    except Exception as e:
        logger.exception(f"Erreur suppression image {filename}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

logger.info("✅ Blueprint Background Upload enregistré")
