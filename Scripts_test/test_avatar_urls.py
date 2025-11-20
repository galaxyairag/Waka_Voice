"""
Test des URLs d'images d'avatars Azure
Vérifie si les URLs sont accessibles et retournent bien des images
"""
import requests
import json

def test_avatar_urls():
    """Tester toutes les URLs d'images d'avatars"""
    
    # URLs depuis la documentation Microsoft
    avatar_urls = {
        'lisa': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/lisa-casual-sitting.png',
        'harry': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/harry-business.png',
        'jeff': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/jeff-business.png',
        'lori': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/lori-formal.png',
        'max': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/max-business.png',
        'meg': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/meg-formal.png'
    }
    
    print("🧪 Test des URLs d'images d'avatars Azure\n")
    print("=" * 80)
    
    results = []
    
    for avatar_name, url in avatar_urls.items():
        print(f"\n📸 Test: {avatar_name}")
        print(f"URL: {url}")
        
        try:
            response = requests.head(url, timeout=10)
            status = response.status_code
            content_type = response.headers.get('Content-Type', 'N/A')
            content_length = response.headers.get('Content-Length', 'N/A')
            
            if status == 200:
                print(f"✅ Status: {status}")
                print(f"   Type: {content_type}")
                print(f"   Taille: {content_length} bytes")
                results.append({
                    'avatar': avatar_name,
                    'url': url,
                    'status': 'OK',
                    'http_code': status,
                    'content_type': content_type,
                    'size': content_length
                })
            else:
                print(f"❌ Status: {status}")
                results.append({
                    'avatar': avatar_name,
                    'url': url,
                    'status': 'ERROR',
                    'http_code': status
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            results.append({
                'avatar': avatar_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            })
    
    print("\n" + "=" * 80)
    print("\n📊 Résumé des résultats:\n")
    
    success_count = sum(1 for r in results if r['status'] == 'OK')
    error_count = len(results) - success_count
    
    print(f"✅ Succès: {success_count}/{len(results)}")
    print(f"❌ Erreurs: {error_count}/{len(results)}")
    
    print("\n" + json.dumps(results, indent=2, ensure_ascii=False))
    
    return results

if __name__ == '__main__':
    test_avatar_urls()
