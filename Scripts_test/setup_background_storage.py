"""
Script pour initialiser le container Blob Storage pour les images de fond des avatars
"""
import os
import sys
from azure.storage.blob import BlobServiceClient, ContainerClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def setup_background_container():
    """
    Crée le container 'background' dans Azure Blob Storage
    pour stocker les images de fond des avatars
    """
    try:
        # Récupérer la connection string
        connection_string = os.getenv('BLOB_CONNECTION_STRING')
        
        if not connection_string:
            print("❌ BLOB_CONNECTION_STRING non trouvée dans .env")
            return False
        
        # Créer le client Blob Service
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Nom du container pour les backgrounds
        container_name = "background"
        
        # Vérifier si le container existe déjà
        try:
            container_client = blob_service_client.get_container_client(container_name)
            container_properties = container_client.get_container_properties()
            print(f"✅ Container '{container_name}' existe déjà")
            print(f"   Créé le: {container_properties.get('last_modified')}")
            return True
            
        except Exception:
            # Container n'existe pas, on le crée
            print(f"📦 Création du container '{container_name}'...")
            
            container_client = blob_service_client.create_container(
                name=container_name,
                public_access='blob'  # Accès public en lecture pour les images
            )
            
            print(f"✅ Container '{container_name}' créé avec succès")
            print(f"   Accès public: blob (lecture seule)")
            print(f"   URL de base: {container_client.url}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du container: {str(e)}")
        return False

def upload_test_image():
    """
    Upload une image de test (optionnel)
    """
    try:
        connection_string = os.getenv('BLOB_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client("background")
        
        # Créer une image de test simple (1x1 pixel transparent PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        blob_name = "test-background.png"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload avec content type pour que le navigateur affiche l'image
        blob_client.upload_blob(
            test_image_data,
            overwrite=True,
            content_settings={
                'content_type': 'image/png',
                'cache_control': 'public, max-age=3600'
            }
        )
        
        blob_url = blob_client.url
        print(f"✅ Image de test uploadée: {blob_url}")
        
        return blob_url
        
    except Exception as e:
        print(f"⚠️ Impossible d'uploader l'image de test: {str(e)}")
        return None

def list_backgrounds():
    """
    Liste tous les backgrounds disponibles
    """
    try:
        connection_string = os.getenv('BLOB_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client("background")
        
        print("\n📋 Images de fond disponibles:")
        blob_list = container_client.list_blobs()
        
        count = 0
        for blob in blob_list:
            count += 1
            blob_client = container_client.get_blob_client(blob.name)
            print(f"   {count}. {blob.name}")
            print(f"      URL: {blob_client.url}")
            print(f"      Taille: {blob.size} bytes")
            print(f"      Modifié: {blob.last_modified}")
            print()
        
        if count == 0:
            print("   Aucune image trouvée")
        else:
            print(f"✅ Total: {count} image(s)")
            
    except Exception as e:
        print(f"⚠️ Impossible de lister les images: {str(e)}")

if __name__ == "__main__":
    print("=" * 70)
    print("🎨 Configuration du Blob Storage pour les backgrounds d'avatars")
    print("=" * 70)
    print()
    
    # Créer le container
    if setup_background_container():
        print()
        
        # Upload une image de test
        print("📸 Upload d'une image de test...")
        upload_test_image()
        print()
        
        # Lister les images disponibles
        list_backgrounds()
        
        print()
        print("=" * 70)
        print("✅ Configuration terminée avec succès")
        print("=" * 70)
        print()
        print("💡 Pour uploader vos propres images:")
        print("   1. Utilisez Azure Storage Explorer")
        print("   2. Ou utilisez le script upload_background.py")
        print("   3. Ou utilisez l'interface web (à implémenter)")
        print()
    else:
        print()
        print("❌ Échec de la configuration")
        sys.exit(1)
