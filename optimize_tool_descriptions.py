"""
Script pour optimiser les descriptions des tools et réduire la consommation de tokens
"""
import os
import re
import glob

def simplify_description(text):
    """Simplifie une description longue en gardant l'essentiel"""
    # Extraire juste la première phrase ou ligne significative
    lines = text.strip().split('\n')
    # Prendre la première phrase non vide
    for line in lines:
        line = line.strip()
        if line and not line.startswith('EXEMPLE') and not line.startswith('---'):
            # Nettoyer les marqueurs
            line = re.sub(r'OUTIL (PRIORITAIRE|DE DERNIER RECOURS) (pour|-)?\s*', '', line)
            line = re.sub(r'NE JAMAIS.*', '', line)
            return line[:150]  # Max 150 caractères
    return text[:150]

def optimize_tool_file(filepath):
    """Optimise un fichier de tool"""
    print(f"📝 Traitement de {os.path.basename(filepath)}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content)
    
    # Réduire les descriptions entre triple quotes
    def reduce_triple_quote(match):
        full_match = match.group(0)
        if '"description":' in full_match or "'description':" in full_match:
            # Extraire le contenu entre les quotes
            quote_content = match.group(1)
            simplified = simplify_description(quote_content)
            return f'"""{simplified}"""'
        return full_match
    
    # Pattern pour capturer les triple quotes
    content = re.sub(r'"""(.*?)"""', reduce_triple_quote, content, flags=re.DOTALL)
    
    new_size = len(content)
    reduction = original_size - new_size
    
    if reduction > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Réduit de {reduction} caractères ({reduction//4} tokens environ)")
        return reduction
    else:
        print(f"   ℹ️  Déjà optimisé")
        return 0

def main():
    tools_dir = "tools"
    tool_files = glob.glob(os.path.join(tools_dir, "tool_*.py"))
    
    print(f"🔍 Trouvé {len(tool_files)} fichiers de tools\n")
    
    total_reduction = 0
    for filepath in sorted(tool_files):
        reduction = optimize_tool_file(filepath)
        total_reduction += reduction
    
    print(f"\n✅ Optimisation terminée!")
    print(f"📊 Réduction totale: {total_reduction} caractères (~{total_reduction//4} tokens)")
    print(f"💰 Économie estimée par requête: ~{total_reduction//4} tokens")

if __name__ == "__main__":
    main()
