"""Check adrian config"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from configuration.cosmos_config import get_avatar_config
import json

agent_id = "7d78514a-b7ec-462d-84c5-26c6e7d2b00c"
config = get_avatar_config(agent_id)

print("Adrian config:")
print(json.dumps(config, indent=2, ensure_ascii=False, default=str))

print("\navatar_character:", repr(config.get('avatar_character')))
print("avatar_style:", repr(config.get('avatar_style')))
print("Type:", type(config.get('avatar_style')))
print("Has key 'avatar_style':", 'avatar_style' in config)

# Test si c'est la chaîne "None"
if config.get('avatar_style') == "None":
    print("\nPROBLEME: avatar_style est la CHAINE 'None' !")
elif config.get('avatar_style') is None:
    print("\nOK: avatar_style est None (Python)")
elif 'avatar_style' not in config:
    print("\nOK: avatar_style n'existe pas")
else:
    print(f"\nValeur: {repr(config.get('avatar_style'))}")
