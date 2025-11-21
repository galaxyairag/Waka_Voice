#!/usr/bin/env python3
"""
Script de génération du PDF du Manuel Utilisateur Waka AI Voice Live
Utilise WeasyPrint pour une mise en page professionnelle
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Lire le fichier Markdown
md_path = Path(__file__).parent / "Manuel_Utilisateur_Waka_Voice.md"
md_content = md_path.read_text(encoding='utf-8')

# Convertir Markdown en HTML
md = markdown.Markdown(extensions=['tables', 'toc', 'fenced_code'])
html_content = md.convert(md_content)

# CSS Waka AI Style
css_style = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

@page {
    size: A4;
    margin: 2cm 2.5cm;

    @top-center {
        content: "Manuel Utilisateur - Waka AI Voice Live";
        font-family: 'Inter', sans-serif;
        font-size: 9pt;
        color: #7B1FA2;
    }

    @bottom-center {
        content: counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 10pt;
        color: #4A148C;
        font-weight: 600;
    }

    @bottom-right {
        content: "Waka AI";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #9E9E9E;
    }
}

@page :first {
    @top-center { content: none; }
    @bottom-center { content: none; }
    @bottom-right { content: none; }
}

:root {
    --waka-primary: #4A148C;
    --waka-primary-light: #7B1FA2;
    --waka-accent-yellow: #FFC107;
    --waka-accent-orange: #FF6F00;
    --waka-bg-light: #F3E5F5;
    --waka-text: #2C003E;
    --waka-border: #CE93D8;
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #2C003E;
    background: white;
}

/* Page de titre */
h1:first-of-type {
    font-size: 32pt;
    color: #4A148C;
    text-align: center;
    margin-top: 5cm;
    margin-bottom: 1cm;
    padding-bottom: 0.5cm;
    border-bottom: 4px solid #FFC107;
    page-break-after: always;
}

h1:first-of-type + p {
    text-align: center;
    font-size: 14pt;
    color: #7B1FA2;
    margin-bottom: 2cm;
}

/* Titres de sections (H1) */
h1 {
    font-size: 22pt;
    color: #4A148C;
    margin-top: 1.5cm;
    margin-bottom: 0.8cm;
    padding-bottom: 0.3cm;
    border-bottom: 3px solid #FFC107;
    page-break-before: always;
    page-break-after: avoid;
}

/* Ne pas sauter de page pour la table des matières */
h1:nth-of-type(2) {
    page-break-before: avoid;
}

/* Sous-sections (H2) */
h2 {
    font-size: 16pt;
    color: #7B1FA2;
    margin-top: 1cm;
    margin-bottom: 0.5cm;
    padding-left: 0.5cm;
    border-left: 4px solid #FFC107;
    page-break-after: avoid;
}

/* Sous-sous-sections (H3) */
h3 {
    font-size: 13pt;
    color: #4A148C;
    margin-top: 0.8cm;
    margin-bottom: 0.4cm;
    page-break-after: avoid;
}

/* H4 */
h4 {
    font-size: 11pt;
    color: #7B1FA2;
    margin-top: 0.6cm;
    margin-bottom: 0.3cm;
    font-weight: 600;
    page-break-after: avoid;
}

/* Paragraphes */
p {
    margin-bottom: 0.5cm;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* Listes */
ul, ol {
    margin-left: 1cm;
    margin-bottom: 0.5cm;
}

li {
    margin-bottom: 0.2cm;
}

/* Tableaux */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.5cm 0 1cm 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

thead {
    background: linear-gradient(135deg, #4A148C 0%, #7B1FA2 100%);
    color: white;
}

th {
    padding: 0.4cm 0.3cm;
    text-align: left;
    font-weight: 600;
    border: 1px solid #4A148C;
}

td {
    padding: 0.3cm;
    border: 1px solid #CE93D8;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background-color: #F3E5F5;
}

tbody tr:hover {
    background-color: #E1BEE7;
}

/* Code */
code {
    font-family: 'Consolas', 'Monaco', monospace;
    background-color: #F3E5F5;
    padding: 0.1cm 0.2cm;
    border-radius: 3px;
    font-size: 9pt;
    color: #4A148C;
}

pre {
    background: linear-gradient(135deg, #1A0033 0%, #2C003E 100%);
    color: #E1BEE7;
    padding: 0.5cm;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0.5cm 0;
    font-size: 9pt;
    border-left: 4px solid #FFC107;
    page-break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
    color: #E1BEE7;
}

/* Blockquotes */
blockquote {
    background: #F3E5F5;
    border-left: 4px solid #7B1FA2;
    margin: 0.5cm 0;
    padding: 0.5cm 1cm;
    font-style: italic;
    color: #4A148C;
    page-break-inside: avoid;
}

/* Liens */
a {
    color: #7B1FA2;
    text-decoration: none;
}

/* Emphases */
strong {
    color: #4A148C;
    font-weight: 700;
}

em {
    color: #7B1FA2;
}

/* Séparateurs */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #4A148C 0%, #FFC107 50%, #FF6F00 100%);
    margin: 1cm 0;
}

/* Notes et conseils */
p:has(strong:first-child) {
    background: #FFF8E1;
    border-left: 4px solid #FFC107;
    padding: 0.4cm;
    margin: 0.5cm 0;
    border-radius: 0 8px 8px 0;
}

/* Table des matières */
h1#table-des-matières + ol,
h1#table-des-matières + ul {
    column-count: 2;
    column-gap: 1cm;
}

/* Encadrés spéciaux pour les conseils */
li:has(strong:first-child) {
    list-style: none;
    margin-left: -1cm;
    padding: 0.2cm 0.5cm;
    background: #F3E5F5;
    border-radius: 4px;
    margin-bottom: 0.3cm;
}

/* Numérotation des sections */
body {
    counter-reset: section;
}

/* Images (si présentes) */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0.5cm auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(74, 20, 140, 0.2);
}

/* Footer de document */
.document-footer {
    text-align: center;
    margin-top: 2cm;
    padding-top: 1cm;
    border-top: 2px solid #CE93D8;
    font-size: 9pt;
    color: #7B1FA2;
}

/* Éviter les coupures inappropriées */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
}

table, pre, blockquote {
    page-break-inside: avoid;
}

/* Annexes */
h1:contains("Annexe") {
    background: #F3E5F5;
    padding: 0.5cm;
    border-radius: 8px;
}
"""

# Template HTML complet
html_template = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manuel Utilisateur - Waka AI Voice Live</title>
</head>
<body>
    {html_content}

    <div class="document-footer">
        <p><strong>Waka AI Voice Live</strong> - Manuel d'Utilisation v1.0</p>
        <p>Novembre 2025 - Tous droits réservés</p>
    </div>
</body>
</html>
"""

# Générer le PDF
output_path = Path(__file__).parent / "Manuel_Utilisateur_Waka_Voice.pdf"

print("Génération du PDF en cours...")
print(f"  Source: {md_path}")
print(f"  Destination: {output_path}")

html = HTML(string=html_template)
css = CSS(string=css_style)

html.write_pdf(output_path, stylesheets=[css])

print(f"\nPDF généré avec succès: {output_path}")
print(f"Taille: {output_path.stat().st_size / 1024:.1f} KB")
