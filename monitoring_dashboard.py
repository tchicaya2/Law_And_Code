#!/usr/bin/env python3
"""
Script de monitoring pour l'application LawAndCode
Usage: python monitoring_dashboard.py
"""
import os
import json
import time
import requests
from datetime import datetime, timedelta
import argparse

class HealthMonitor:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.alerts = []
    
    def check_health(self):
        """Vérifie l'état de santé de l'application"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                return health_data
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_logs(self, log_file="logs/app.log"):
        """Analyse les logs d'application"""
        if not os.path.exists(log_file):
            return {"error": f"Log file {log_file} not found"}
        
        stats = {
            "total_requests": 0,
            "error_count": 0,
            "average_response_time": 0,
            "recent_errors": [],
            "user_actions": 0,
            "security_events": 0
        }
        
        total_time = 0
        request_count = 0
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Compter les requêtes
                        if 'Response:' in log_entry.get('message', ''):
                            stats["total_requests"] += 1
                            request_count += 1
                            if 'duration' in log_entry:
                                total_time += log_entry['duration']
                        
                        # Compter les erreurs
                        if log_entry.get('level') in ['ERROR', 'CRITICAL']:
                            stats["error_count"] += 1
                            stats["recent_errors"].append({
                                'timestamp': log_entry.get('timestamp'),
                                'message': log_entry.get('message'),
                                'user_id': log_entry.get('user_id')
                            })
                        
                        # Compter les actions utilisateur
                        if 'User action:' in log_entry.get('message', ''):
                            stats["user_actions"] += 1
                        
                        # Compter les événements de sécurité
                        if 'Security event:' in log_entry.get('message', ''):
                            stats["security_events"] += 1
                            
                    except json.JSONDecodeError:
                        continue
            
            if request_count > 0:
                stats["average_response_time"] = total_time / request_count
                
        except Exception as e:
            stats["error"] = f"Error reading log file: {e}"
        
        return stats
    
    def generate_report(self):
        """Génère un rapport de monitoring complet"""
        print("=" * 60)
        print("RAPPORT DE MONITORING - LawAndCode")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Health check
        print("🔍 ÉTAT DE SANTÉ DE L'APPLICATION")
        print("-" * 40)
        health = self.check_health()
        
        if health.get("status") == "healthy":
            print("✅ Application: Saine")
            print(f"✅ Base de données: {health.get('database', 'Unknown')}")
            print(f"🗄️ Cache: {health.get('cache', 'Unknown')}")
        else:
            print(f"❌ Application: {health.get('message', 'Erreur inconnue')}")
        
        print()
        
        # Métriques
        if 'metrics' in health:
            print("📊 MÉTRIQUES EN TEMPS RÉEL")
            print("-" * 40)
            metrics = health['metrics']
            for key, value in metrics.items():
                print(f"📈 {key}: {value}")
            print()
        
        # Analyse des logs
        print("📋 ANALYSE DES LOGS")
        print("-" * 40)
        log_stats = self.analyze_logs()
        
        if "error" not in log_stats:
            print(f"📊 Total requêtes: {log_stats['total_requests']}")
            print(f"⚠️ Erreurs: {log_stats['error_count']}")
            print(f"⚡ Temps de réponse moyen: {log_stats['average_response_time']:.3f}s")
            print(f"👤 Actions utilisateur: {log_stats['user_actions']}")
            print(f"🔒 Événements de sécurité: {log_stats['security_events']}")
            
            if log_stats['recent_errors']:
                print("\n🚨 ERREURS RÉCENTES:")
                for error in log_stats['recent_errors'][-5:]:  # 5 dernières erreurs
                    print(f"   - {error['timestamp']}: {error['message']}")
        else:
            print(f"❌ {log_stats['error']}")
        
        print()
        
        # Alertes
        self.check_alerts(health, log_stats)
        if self.alerts:
            print("🚨 ALERTES")
            print("-" * 40)
            for alert in self.alerts:
                print(f"⚠️ {alert}")
        else:
            print("✅ Aucune alerte active")
        
        print("=" * 60)
    
    def check_alerts(self, health, log_stats):
        """Vérifie les conditions d'alerte"""
        self.alerts = []
        
        # Vérifier l'état de l'application
        if health.get("status") != "healthy":
            self.alerts.append("Application non saine")
        
        # Vérifier la base de données
        if health.get("database") != "healthy":
            self.alerts.append("Problème de base de données détecté")
        
        # Vérifier le taux d'erreur
        if "error" not in log_stats:
            if log_stats['total_requests'] > 0:
                error_rate = log_stats['error_count'] / log_stats['total_requests']
                if error_rate > 0.05:  # Plus de 5% d'erreurs
                    self.alerts.append(f"Taux d'erreur élevé: {error_rate:.1%}")
            
            # Vérifier le temps de réponse
            if log_stats['average_response_time'] > 2.0:  # Plus de 2 secondes
                self.alerts.append(f"Temps de réponse lent: {log_stats['average_response_time']:.2f}s")
            
            # Vérifier les événements de sécurité
            if log_stats['security_events'] > 10:
                self.alerts.append(f"Nombreux événements de sécurité: {log_stats['security_events']}")

def main():
    parser = argparse.ArgumentParser(description='Monitoring LawAndCode')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='URL de base de l\'application')
    parser.add_argument('--watch', action='store_true',
                       help='Mode surveillance continue')
    parser.add_argument('--interval', type=int, default=60,
                       help='Intervalle de surveillance en secondes')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(args.url)
    
    if args.watch:
        print("Mode surveillance activé. Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                monitor.generate_report()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nSurveillance arrêtée.")
    else:
        monitor.generate_report()

if __name__ == "__main__":
    main()
