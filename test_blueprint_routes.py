from flask import Flask
from Blueprints.agents_config_routes import agents_config_bp

app = Flask(__name__)
app.register_blueprint(agents_config_bp)

print("\n=== ROUTES ENREGISTRÉES ===")
for rule in app.url_map.iter_rules():
    if 'agents' in str(rule):
        print(f"{rule} -> {rule.endpoint} [{','.join(rule.methods - {'HEAD', 'OPTIONS'})}]")

print(f"\nTotal routes agents: {len([r for r in app.url_map.iter_rules() if 'agents' in str(r)])}")
