"""
Routes pour le dashboard production et financier
Fournit les endpoints d'API pour les graphiques et analyses
"""

from flask import Blueprint, jsonify, request, render_template
from datetime import datetime, timedelta
from configuration.cosmos_config import get_call_history_container
import statistics

production_bp = Blueprint('production', __name__, url_prefix='/api/production')
production_pages_bp = Blueprint('production_pages', __name__, url_prefix='/production')

@production_pages_bp.route('/')
def production_dashboard_page():
    """Affiche la page du dashboard production"""
    return render_template('production_dashboard.html')

@production_pages_bp.route('/report')
def production_report_page():
    """Affiche la page de génération de rapport production"""
    return render_template('production_report.html')


def get_period_filter(period_days):
    """Génère la date de début pour filtrer les conversations"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    return start_date


def query_conversations_by_period(period_days):
    """
    Récupère toutes les conversations terminées sur la période donnée
    """
    container = get_call_history_container()
    start_date = get_period_filter(period_days)
    start_timestamp = start_date.isoformat() + "Z"
    
    query = """
    SELECT c.call_id, c.agent_id, c.model, c.model_family, c.status,
           c.duration_minutes, c.cost, c.tokens, c.interaction_count,
           c.start_time, c.end_time, c.ended_at, c._ts
    FROM c
    WHERE c.status = 'completed'
          AND c.ended_at >= @start_timestamp
    ORDER BY c.ended_at DESC
    """
    
    parameters = [{"name": "@start_timestamp", "value": start_timestamp}]
    
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    return items


@production_bp.route('/conversations-by-day', methods=['GET'])
def conversations_by_day():
    """
    Retourne l'évolution du nombre de conversations par jour
    """
    try:
        period = int(request.args.get('period', 30))
        conversations = query_conversations_by_period(period)
        
        # Grouper par jour
        days = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            if ended_at_str:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days:
                    days[date] = 0
                days[date] += 1
        
        # Formater pour Chart.js
        sorted_days = sorted(days.items())
        labels = [day[0] for day in sorted_days]
        data = [day[1] for day in sorted_days]
        
        # Calculer tendance linéaire et indice d'évolution
        n = len(data)
        if n >= 2:
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = sum(data) / n
            numerator = sum((x_vals[i] - x_mean) * (data[i] - y_mean) for i in range(n))
            denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean
            trend = [round(slope * i + intercept, 2) for i in x_vals]
            
            # Indice d'évolution: comparer première et dernière semaine
            first_week_avg = sum(data[:min(7, n)]) / min(7, n)
            last_week_avg = sum(data[-min(7, n):]) / min(7, n)
            evolution_index = round(((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0, 2)
            evolution_status = "hausse" if evolution_index > 5 else ("baisse" if evolution_index < -5 else "stable")
        else:
            trend = data
            evolution_index = 0
            evolution_status = "insufficient_data"
        
        return jsonify({
            'labels': labels,
            'data': data,
            'trend': trend,
            'evolution_index': evolution_index,
            'evolution_status': evolution_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/duration-stats-by-day', methods=['GET'])
def duration_stats_by_day():
    """
    Retourne l'évolution de la durée moyenne, max et min par jour
    """
    try:
        period = int(request.args.get('period', 30))
        conversations = query_conversations_by_period(period)
        
        # Grouper par jour
        days = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            duration = conv.get('duration_minutes', 0)
            
            if ended_at_str:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days:
                    days[date] = []
                days[date].append(duration)
        
        # Calculer stats par jour
        sorted_days = sorted(days.items())
        labels = []
        avg_data = []
        max_data = []
        min_data = []
        
        for date, durations in sorted_days:
            if durations:
                labels.append(date)
                avg_data.append(round(statistics.mean(durations), 2))
                max_data.append(round(max(durations), 2))
                min_data.append(round(min(durations), 2))
        
        # Calculer tendance linéaire sur durée moyenne
        n = len(avg_data)
        if n >= 2:
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = sum(avg_data) / n
            numerator = sum((x_vals[i] - x_mean) * (avg_data[i] - y_mean) for i in range(n))
            denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean
            trend = [round(slope * i + intercept, 2) for i in x_vals]
            
            # Indice d'évolution durée moyenne
            first_week_avg = sum(avg_data[:min(7, n)]) / min(7, n)
            last_week_avg = sum(avg_data[-min(7, n):]) / min(7, n)
            evolution_index = round(((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0, 2)
            evolution_status = "hausse" if evolution_index > 5 else ("baisse" if evolution_index < -5 else "stable")
        else:
            trend = avg_data
            evolution_index = 0
            evolution_status = "insufficient_data"
        
        return jsonify({
            'labels': labels,
            'avg': avg_data,
            'max': max_data,
            'min': min_data,
            'trend': trend,
            'evolution_index': evolution_index,
            'evolution_status': evolution_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/interactions-stats', methods=['GET'])
def interactions_stats():
    """
    Retourne l'évolution quotidienne du nombre d'interactions moyen et durée moyenne d'interaction
    """
    try:
        period = int(request.args.get('period', 30))
        conversations = query_conversations_by_period(period)
        
        # Grouper par jour
        days = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            interaction_count = conv.get('interaction_count', 0)
            duration = conv.get('duration_minutes', 0)
            
            if ended_at_str and interaction_count and duration:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days:
                    days[date] = {
                        'interactions': [],
                        'interaction_durations': []  # durée par interaction
                    }
                
                days[date]['interactions'].append(interaction_count)
                # Durée moyenne d'une interaction = durée totale / nombre d'interactions
                days[date]['interaction_durations'].append(duration / interaction_count)
        
        # Calculer moyennes par jour
        sorted_days = sorted(days.items())
        labels = []
        avg_interaction_count = []  # Nombre moyen d'interactions par conversation
        avg_interaction_duration = []  # Durée moyenne d'une interaction
        
        for date, data in sorted_days:
            if data['interactions']:
                labels.append(date)
                avg_interaction_count.append(round(statistics.mean(data['interactions']), 2))
                avg_interaction_duration.append(round(statistics.mean(data['interaction_durations']), 2))
        
        return jsonify({
            'labels': labels,
            'avg_interaction_count': avg_interaction_count,
            'avg_interaction_duration': avg_interaction_duration
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/cost-breakdown-by-type', methods=['GET'])
def cost_breakdown_by_type():
    """
    Retourne la répartition détaillée des coûts par type
    (inputs_text, inputs_cached, inputs_audio, outputs_text, outputs_audio)
    """
    try:
        period = int(request.args.get('period', 30))
        conversations = query_conversations_by_period(period)
        
        # Agréger les coûts par type
        cost_types = {
            'inputs_text': 0,
            'inputs_cached': 0,
            'inputs_audio': 0,
            'outputs_text': 0,
            'outputs_audio': 0
        }
        
        for conv in conversations:
            cost_obj = conv.get('cost', {})
            if isinstance(cost_obj, dict):
                cost_types['inputs_text'] += cost_obj.get('inputs_text_cost', 0)
                cost_types['inputs_cached'] += cost_obj.get('inputs_cached_cost', 0)
                cost_types['inputs_audio'] += cost_obj.get('inputs_audio_cost', 0)
                cost_types['outputs_text'] += cost_obj.get('outputs_text_cost', 0)
                cost_types['outputs_audio'] += cost_obj.get('outputs_audio_cost', 0)
        
        # Formater pour camembert
        labels = [
            'Inputs Text',
            'Inputs Cached',
            'Inputs Audio',
            'Outputs Text',
            'Outputs Audio'
        ]
        data = [
            round(cost_types['inputs_text'], 4),
            round(cost_types['inputs_cached'], 4),
            round(cost_types['inputs_audio'], 4),
            round(cost_types['outputs_text'], 4),
            round(cost_types['outputs_audio'], 4)
        ]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/cost-distribution', methods=['GET'])
def cost_distribution():
    """
    Retourne la répartition des coûts par famille de modèle (camembert)
    """
    try:
        period = int(request.args.get('period', 30))
        conversations = query_conversations_by_period(period)
        
        # Grouper par famille/modèle
        cost_by_family = {}
        for conv in conversations:
            family = conv.get('model_family') or conv.get('model') or 'Unknown'
            cost_obj = conv.get('cost', {})
            cost = cost_obj.get('total_cost', 0) if isinstance(cost_obj, dict) else 0
            
            if family not in cost_by_family:
                cost_by_family[family] = 0
            cost_by_family[family] += cost
        
        # Formater pour camembert
        labels = list(cost_by_family.keys())
        data = [round(cost, 4) for cost in cost_by_family.values()]

        # Toujours renvoyer des tableaux, même vides, pour éviter les erreurs JS
        return jsonify({
            'labels': labels,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/financial-evolution', methods=['GET'])
def financial_evolution():
    """
    Retourne l'évolution des coûts vs CA par jour
    """
    try:
        period = int(request.args.get('period', 30))
        price_per_minute = float(request.args.get('price', 0.1))
        conversations = query_conversations_by_period(period)
        
        # Grouper par jour
        days = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            cost_obj = conv.get('cost', {})
            cost = cost_obj.get('total_cost', 0) if isinstance(cost_obj, dict) else 0
            duration = conv.get('duration_minutes', 0) or 0
            
            if ended_at_str:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days:
                    days[date] = {'cost': 0, 'revenue': 0}
                
                days[date]['cost'] += cost
                days[date]['revenue'] += duration * price_per_minute
        
        # Formater les données
        sorted_days = sorted(days.items())
        labels = [day[0] for day in sorted_days]
        costs = [round(day[1]['cost'], 2) for day in sorted_days]
        revenues = [round(day[1]['revenue'], 2) for day in sorted_days]

        return jsonify({
            'labels': labels,
            'costs': costs,
            'revenues': revenues
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/margin-evolution', methods=['GET'])
def margin_evolution():
    """
    Retourne l'évolution de la marge brute et marge en %
    """
    try:
        period = int(request.args.get('period', 30))
        price_per_minute = float(request.args.get('price', 0.1))
        conversations = query_conversations_by_period(period)
        
        # Grouper par jour
        days = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            cost_obj = conv.get('cost', {})
            cost = cost_obj.get('total_cost', 0) if isinstance(cost_obj, dict) else 0
            duration = conv.get('duration_minutes', 0) or 0
            
            if ended_at_str:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days:
                    days[date] = {'cost': 0, 'revenue': 0}
                
                days[date]['cost'] += cost
                days[date]['revenue'] += duration * price_per_minute
        
        # Calculer marges
        sorted_days = sorted(days.items())
        labels = [day[0] for day in sorted_days]
        gross_margins = [round(day[1]['revenue'] - day[1]['cost'], 2) for day in sorted_days]
        margin_percentages = [
            round((day[1]['revenue'] - day[1]['cost']) / day[1]['revenue'] * 100, 2) 
            if day[1]['revenue'] > 0 else 0
            for day in sorted_days
        ]
        
        return jsonify({
            'labels': labels,
            'gross_margin': gross_margins,
            'margin_percentage': margin_percentages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@production_bp.route('/generate-report', methods=['GET'])
def generate_production_report():
    """
    Génère un rapport d'analyse production/financier avec GPT-5-mini
    """
    try:
        import os
        from openai import AzureOpenAI
        
        period = int(request.args.get('period', 30))
        price_per_minute = float(request.args.get('price', 0.1))
        conversations = query_conversations_by_period(period)
        
        # Calculer statistiques globales
        total_conversations = len(conversations)
        total_duration = sum(conv.get('duration_minutes', 0) or 0 for conv in conversations)
        total_cost = sum(
            (conv.get('cost', {}).get('total_cost', 0) if isinstance(conv.get('cost', {}), dict) else 0)
            for conv in conversations
        )
        total_revenue = total_duration * price_per_minute
        total_margin = total_revenue - total_cost
        margin_percentage = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        avg_duration = total_duration / total_conversations if total_conversations > 0 else 0
        avg_cost = total_cost / total_conversations if total_conversations > 0 else 0
        
        # Stats par jour
        days_stats = {}
        for conv in conversations:
            ended_at_str = conv.get('ended_at', '')
            if ended_at_str:
                date = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date not in days_stats:
                    days_stats[date] = {
                        'conversations': 0,
                        'duration': 0,
                        'cost': 0,
                        'revenue': 0
                    }
                
                days_stats[date]['conversations'] += 1
                days_stats[date]['duration'] += conv.get('duration_minutes', 0) or 0
                cost_obj = conv.get('cost', {})
                days_stats[date]['cost'] += cost_obj.get('total_cost', 0) if isinstance(cost_obj, dict) else 0
                days_stats[date]['revenue'] += (conv.get('duration_minutes', 0) or 0) * price_per_minute
        
        # Coûts par famille
        cost_by_family = {}
        for conv in conversations:
            family = conv.get('model_family') or conv.get('model') or 'Unknown'
            cost_obj = conv.get('cost', {})
            cost = cost_obj.get('total_cost', 0) if isinstance(cost_obj, dict) else 0
            if family not in cost_by_family:
                cost_by_family[family] = 0
            cost_by_family[family] += cost
        
        # Construire le prompt
        prompt = f"""Tu es un analyste financier et opérationnel spécialisé dans l'analyse de centres de contact IA.

Voici les données sur les {period} derniers jours :

STATISTIQUES GLOBALES :
- Nombre total de conversations : {total_conversations}
- Durée totale : {round(total_duration, 2)} minutes
- Durée moyenne par conversation : {round(avg_duration, 2)} minutes
- Coût total : ${round(total_cost, 4)}
- Coût moyen par conversation : ${round(avg_cost, 4)}
- Revenu total (prix: ${price_per_minute}/min) : ${round(total_revenue, 2)}
- Marge brute : ${round(total_margin, 2)}
- Marge en % : {round(margin_percentage, 2)}%

RÉPARTITION DES COÛTS PAR FAMILLE :
{chr(10).join([f"- {family} : ${round(cost, 4)} ({round(cost/total_cost*100, 1)}%)" for family, cost in sorted(cost_by_family.items(), key=lambda x: x[1], reverse=True)])}

ÉVOLUTION QUOTIDIENNE (derniers 7 jours) :
{chr(10).join([f"- {date} : {stats['conversations']} conv | Durée: {round(stats['duration'], 1)}min | Coût: ${round(stats['cost'], 3)} | CA: ${round(stats['revenue'], 2)} | Marge: ${round(stats['revenue']-stats['cost'], 2)}" for date, stats in sorted(days_stats.items())[-7:]])}

INSTRUCTIONS :
Génère un rapport d'analyse structuré en Markdown avec les sections suivantes :

## Rapport Production & Financier - Analyse sur {period} jours

### 1. Vue d'Ensemble Opérationnelle
Analyse DÉTAILLÉE et EXHAUSTIVE (minimum 5000 caractères) :
- Volume d'activité et tendances
- Analyse de la productivité (conversations/jour, durée moyenne)
- Patterns d'utilisation et pics d'activité
- Efficacité opérationnelle
- Suggère des graphiques : évolution du nombre de conversations, distribution des durées

### 2. Analyse de Performance par Modèle
Analyse APPROFONDIE (minimum 5000 caractères) :
- Comparaison détaillée des familles/modèles
- Analyse coût/performance de chaque modèle
- Recommandations d'optimisation
- Tendances d'utilisation par modèle
- Suggère des graphiques : camembert des coûts, barres comparatives par modèle

### 3. Analyse Financière
Analyse COMPLÈTE (minimum 5000 caractères) :
- Évolution des coûts et du chiffre d'affaires
- Analyse de rentabilité détaillée
- Calcul et évolution de la marge brute et du taux de marge
- Identification des leviers d'optimisation financière
- Projections et tendances
- Suggère des graphiques : évolution coûts vs CA, évolution des marges

### 4. Points d'Attention et Risques
Liste DÉTAILLÉE (minimum 5000 caractères) :
- Anomalies détectées dans les données
- Tendances préoccupantes
- Risques financiers identifiés
- Opportunités d'amélioration
- Suggère des graphiques : alertes visuelles, tendances à surveiller

### 5. Recommandations et Conclusion
Synthèse COMPLÈTE (minimum 3000 caractères) :
- Recommandations actionnables prioritaires
- Plan d'action suggéré
- Objectifs d'optimisation
- Conclusion générale

IMPORTANT :
- CHAQUE SECTION DOIT CONTENIR AU MINIMUM 5000 CARACTÈRES (sauf conclusion: 3000)
- Sois TRÈS DÉTAILLÉ et EXHAUSTIF dans chaque analyse
- Utilise des données chiffrées précises
- Propose des recommandations concrètes
- Suggère des graphiques pertinents pour CHAQUE section
- Mets en gras les chiffres clés avec **
- Inclus des calculs de ROI et de rentabilité
"""
        
        # Appeler GPT-5-mini
        client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_SUMMARY_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_SUMMARY_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_SUMMARY_ENDPOINT")
        )
        
        deployment_name = os.environ.get("AZURE_OPENAI_GPT5_MINI_DEPLOYMENT", "gpt-5-mini")
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "Tu es un analyste financier et opérationnel expert en optimisation de centres de contact IA."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=32000
        )
        
        report = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        print(f"Erreur génération rapport production: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
