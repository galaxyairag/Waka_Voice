"""
Test pour voir ce que génère le template Jinja pour l'agent adrian
"""
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from jinja2 import Template
from configuration.cosmos_config import get_avatar_config

# Récupérer la config réelle d'adrian
agent_id = "7d78514a-b7ec-462d-84c5-26c6e7d2b00c"
avatar_config_db = get_avatar_config(agent_id)

print("="*70)
print("🔍 Test génération template Jinja pour adrian")
print("="*70)

# Simuler la construction de avatar_cfg_dict comme dans le backend
avatar_character = avatar_config_db.get('avatar_character') or 'lisa'
avatar_style_raw = avatar_config_db.get('avatar_style')
avatar_style = avatar_style_raw if avatar_style_raw not in [None, 'None', 'null', ''] else None

print(f"\n📥 DEPUIS DB:")
print(f"   avatar_character: {repr(avatar_config_db.get('avatar_character'))}")
print(f"   avatar_style (brut): {repr(avatar_style_raw)}")
print(f"   Clé 'avatar_style' existe: {'avatar_style' in avatar_config_db}")

print(f"\n🔄 APRÈS TRAITEMENT:")
print(f"   avatar_style: {repr(avatar_style)}")

# Construire avatar_cfg_dict
avatar_cfg_dict = {
    'character': avatar_character,
    'background_color': avatar_config_db.get('avatar_background_color') or '#FFFFFF',
    'background_image': avatar_config_db.get('avatar_background_image', '')
}

# Ajouter style conditionnellement
if avatar_style and avatar_style.strip():
    avatar_cfg_dict['style'] = avatar_style.strip()
    print(f"   ✅ Style AJOUTÉ: {repr(avatar_style.strip())}")
else:
    print(f"   ❌ Style NON AJOUTÉ")

print(f"\n📦 avatar_cfg_dict final:")
print(f"   Clés: {list(avatar_cfg_dict.keys())}")
print(f"   'style' in avatar_cfg_dict: {'style' in avatar_cfg_dict}")
if 'style' in avatar_cfg_dict:
    print(f"   style value: {repr(avatar_cfg_dict['style'])}")

# Simuler l'objet agent passé au template
agent = {
    'avatar_config': avatar_cfg_dict
}

# Template exactement comme dans avatar_voice_session.html
template_str = """
avatarConfig: {
    character: '{{ agent.avatar_config.character }}',{% if agent.avatar_config.get('style') %}
    style: '{{ agent.avatar_config.style }}',{% endif %}
    backgroundColor: '{{ agent.avatar_config.background_color or "#FFFFFF" }}',
    backgroundImage: '{{ agent.avatar_config.background_image or "" }}'
}
"""

template = Template(template_str)
result = template.render(agent=agent)

print(f"\n📤 JAVASCRIPT GÉNÉRÉ PAR JINJA:")
print(result)

# Vérifier si 'style:' apparaît
if 'style:' in result:
    print("\n⚠️  PROBLÈME: La propriété 'style:' est générée !")
    # Extraire la valeur
    import re
    match = re.search(r"style:\s*'([^']*)'", result)
    if match:
        style_value = match.group(1)
        print(f"   Valeur de style: {repr(style_value)}")
else:
    print("\n✅ OK: La propriété 'style:' n'est PAS générée")

print("\n" + "="*70)
