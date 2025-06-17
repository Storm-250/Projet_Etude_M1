import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: sqlmap.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"sqlmap_{date}.html")
    
    print(f"🔍 Scan SQLMap en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Préparer les URLs à tester (correction de l'erreur UnboundLocalError)
    if target.startswith(('http://', 'https://')):
        test_urls = [target]
    else:
        test_urls = [f"http://{target}", f"https://{target}"]
    
    # Ajouter quelques chemins de test courants avec paramètres
    additional_paths = [
        "/index.php?id=1",
        "/login.php?user=test",
        "/search.php?q=test",
        "/product.php?id=1"
    ]
    
    # Construire la liste finale des URLs à tester (limité à 6 URLs max)
    final_test_urls = []
    for base_url in test_urls:
        final_test_urls.append(base_url)  # URL de base
        for path in additional_paths[:2]:  # Ajouter 2 chemins par protocole
            test_url = base_url + path
            final_test_urls.append(test_url)
            if len(final_test_urls) >= 6:  # Maximum 6 URLs au total
                break
        if len(final_test_urls) >= 6:
            break
    
    print(f"🎯 URLs à tester: {len(final_test_urls)} URLs")
    for url in final_test_urls:
        print(f"   - {url}")
    
    sqlmap_results = {}
    sqlmap_available = True
    
    # Vérifier si SQLMap est disponible
    try:
        version_check = subprocess.run(["sqlmap", "--version"], capture_output=True, timeout=10, text=True)
        if version_check.returncode == 0:
            print("✅ SQLMap détecté et fonctionnel")
        else:
            print("⚠️ SQLMap détecté mais problème de version")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ SQLMap non trouvé")
        sqlmap_available = False
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification SQLMap: {e}")
        sqlmap_available = False
    
    for i, test_url in enumerate(final_test_urls, 1):
        print(f"🔍 [{i}/{len(final_test_urls)}] Test SQLMap sur {test_url}...")
        
        if not sqlmap_available:
            sqlmap_results[test_url] = {
                'status': '❌ SQLMap non installé',
                'risk_level': 'UNKNOWN',
                'vulnerabilities': [],
                'output': 'SQLMap non disponible sur ce système',
                'errors': 'Outil SQLMap non trouvé ou non fonctionnel',
                'returncode': -2
            }
            continue
        
        try:
            # Commande SQLMap native optimisée
            sqlmap_cmd = [
                "sqlmap",
                "-u", test_url,
                "--batch",                     # Mode automatique, pas d'interaction
                "--random-agent",              # User-agent aléatoire
                "--timeout", "10",             # Timeout de 10 secondes par requête
                "--retries", "1",              # 1 tentative maximum
                "--level", "1",                # Niveau de test basique
                "--risk", "1",                 # Risque minimal
                "--threads", "2",              # 2 threads pour éviter la surcharge
                "--technique", "BEUST",        # Toutes les techniques de base
                "--flush-session",             # Nettoyer les sessions précédentes
                "--no-logging",                # Pas de fichiers de log
                "--answers", "quit=N,follow=N,continue=N,other=N",  # Réponses automatiques
                "--parse-errors"               # Parser les erreurs SQL
            ]
            
            print(f"🚀 Exécution SQLMap...")
            
            sqlmap_result = subprocess.run(
                sqlmap_cmd, 
                capture_output=True, 
                text=True, 
                timeout=60  # 60 secondes max par URL
            )
            
            output = sqlmap_result.stdout if sqlmap_result.stdout else ""
            errors = sqlmap_result.stderr if sqlmap_result.stderr else ""
            
            # Analyser les résultats pour détecter les vulnérabilités
            vulnerabilities_found = []
            injection_details = []
            
            if output:
                # Rechercher les indicateurs de vulnérabilités
                lines = output.split('\n')
                for line in lines:
                    line_lower = line.lower().strip()
                    
                    # Détecter les vulnérabilités confirmées
                    if any(keyword in line_lower for keyword in [
                        'is vulnerable', 'parameter', 'injectable', 
                        'blind sql injection', 'union query', 'error-based'
                    ]):
                        if line.strip() and len(line.strip()) > 10:
                            vulnerabilities_found.append(line.strip())
                    
                    # Extraire les détails d'injection
                    if any(keyword in line_lower for keyword in [
                        'type:', 'title:', 'payload:', 'vector:'
                    ]):
                        if line.strip() and len(line.strip()) > 5:
                            injection_details.append(line.strip())
            
            # Limiter le nombre de résultats pour éviter un rapport trop long
            vulnerabilities_found = list(set(vulnerabilities_found))[:8]  # Max 8, sans doublons
            injection_details = list(set(injection_details))[:10]  # Max 10, sans doublons
            
            # Déterminer le statut et le niveau de risque
            if vulnerabilities_found and any("vulnerable" in vuln.lower() for vuln in vulnerabilities_found):
                status = f"🚨 VULNÉRABLE ({len(vulnerabilities_found)} détections)"
                risk_level = "HIGH"
            elif injection_details or "might be injectable" in output.lower():
                status = f"⚠️ Potentiellement vulnérable"
                risk_level = "MEDIUM"
            elif sqlmap_result.returncode == 0:
                status = f"✅ Aucune vulnérabilité détectée"
                risk_level = "LOW"
            else:
                status = f"❌ Erreur lors du scan (code {sqlmap_result.returncode})"
                risk_level = "UNKNOWN"
            
            # Combiner vulnérabilités et détails
            all_findings = vulnerabilities_found + injection_details
            
            sqlmap_results[test_url] = {
                'status': status,
                'risk_level': risk_level,
                'vulnerabilities': all_findings,
                'output': output[:2000] if output else "",  # Limiter la sortie à 2000 caractères
                'errors': errors[:800] if errors else "",   # Limiter les erreurs à 800 caractères
                'returncode': sqlmap_result.returncode
            }
            
            print(f"   {status}")
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout pour {test_url}")
            sqlmap_results[test_url] = {
                'status': '⏰ Timeout (>60s)',
                'risk_level': 'UNKNOWN',
                'vulnerabilities': [],
                'output': 'Scan interrompu par timeout - URL trop lente à répondre',
                'errors': 'Timeout dépassé',
                'returncode': -1
            }
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"   ❌ Erreur: {error_msg}")
            sqlmap_results[test_url] = {
                'status': f'❌ Erreur: {error_msg}',
                'risk_level': 'UNKNOWN',
                'vulnerabilities': [],
                'output': f'Exception lors du scan: {error_msg}',
                'errors': str(e),
                'returncode': -3
            }

    # Analyser les résultats globaux
    total_vulns = sum(len(r['vulnerabilities']) for r in sqlmap_results.values())
    high_risk_count = len([r for r in sqlmap_results.values() if r['risk_level'] == 'HIGH'])
    medium_risk_count = len([r for r in sqlmap_results.values() if r['risk_level'] == 'MEDIUM'])
    low_risk_count = len([r for r in sqlmap_results.values() if r['risk_level'] == 'LOW'])
    unknown_count = len([r for r in sqlmap_results.values() if r['risk_level'] == 'UNKNOWN'])
    
    print(f"\n📊 Résumé du scan:")
    print(f"   🚨 Vulnérabilités critiques: {high_risk_count}")
    print(f"   ⚠️ Vulnérabilités potentielles: {medium_risk_count}")
    print(f"   ✅ URLs sûres: {low_risk_count}")
    print(f"   ❓ Erreurs/Inconnu: {unknown_count}")

    # Générer le rapport HTML
    try:
        print("📝 Génération du rapport HTML...")
        
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport SQLMap - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; margin-bottom: 30px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 20px; }}
        h3 {{ color: #2c3e50; margin-top: 25px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .critical {{ background-color: #f8d7da; color: #721c24; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; font-weight: bold; font-size: 1.1em; }}
        .url-test {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #6c757d; }}
        .vulnerability {{ background-color: #f8d7da; padding: 10px; margin: 8px 0; border-left: 3px solid #dc3545; border-radius: 0 3px 3px 0; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; }}
        .safe {{ background-color: #d4edda; padding: 10px; margin: 8px 0; border-left: 3px solid #28a745; border-radius: 0 3px 3px 0; }}
        .potential {{ background-color: #fff3cd; padding: 10px; margin: 8px 0; border-left: 3px solid #ffc107; border-radius: 0 3px 3px 0; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; max-height: 400px; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin: 25px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .stat h3 {{ margin: 0; font-size: 2em; }}
        .stat p {{ margin: 10px 0 0 0; color: #666; }}
        .stat.danger {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .stat.warning {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .stat.success {{ border-left-color: #28a745; background-color: #d4edda; }}
        .risk-high {{ color: #dc3545; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
        .risk-unknown {{ color: #6c757d; }}
        .summary {{ background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; }}
        .url-header {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-weight: bold; word-break: break-all; }}
        details {{ margin: 15px 0; }}
        summary {{ cursor: pointer; padding: 8px; background-color: #e9ecef; border-radius: 4px; font-weight: bold; }}
        summary:hover {{ background-color: #dee2e6; }}
        .tech-info {{ background-color: #f1f3f4; padding: 15px; border-radius: 5px; margin: 15px 0; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Rapport SQLMap - Test d'Injection SQL</h1>
        <div class="info">
            <strong>🎯 Cible analysée:</strong> {target}<br>
            <strong>📅 Date du scan:</strong> {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}<br>
            <strong>🔧 Outil utilisé:</strong> SQLMap (installation native dans conteneur)<br>
            <strong>🔍 URLs testées:</strong> {len(final_test_urls)}<br>
            <strong>⚙️ Configuration:</strong> Scan automatisé niveau 1, risque 1, techniques BEUST<br>
            <strong>⏱️ Durée par URL:</strong> Maximum 60 secondes
        </div>
        
        <div class="stats">
            <div class="stat {'danger' if high_risk_count > 0 else 'success'}">
                <h3>{high_risk_count}</h3>
                <p>Vulnérabilités<br>confirmées</p>
            </div>
            <div class="stat {'warning' if medium_risk_count > 0 else 'success'}">
                <h3>{medium_risk_count}</h3>
                <p>Vulnérabilités<br>potentielles</p>
            </div>
            <div class="stat success">
                <h3>{low_risk_count}</h3>
                <p>URLs<br>sécurisées</p>
            </div>
            <div class="stat">
                <h3>{total_vulns}</h3>
                <p>Détections<br>totales</p>
            </div>
        </div>""")

            # Résumé de sécurité global
            if high_risk_count > 0:
                f.write(f"""
        <div class="critical">
            🚨 <strong>ALERTE SÉCURITÉ CRITIQUE</strong><br>
            {high_risk_count} vulnérabilité(s) d'injection SQL confirmée(s) détectée(s) !<br>
            <strong>⚡ Action immédiate requise - Risque de compromission des données</strong><br>
            💡 Consultez les recommandations ci-dessous pour corriger ces failles
        </div>""")
            elif medium_risk_count > 0:
                f.write(f"""
        <div class="warning">
            ⚠️ <strong>Vulnérabilités potentielles détectées</strong><br>
            {medium_risk_count} URL(s) présentent des signes d'injection SQL possible.<br>
            Investigation manuelle recommandée pour confirmer les vulnérabilités.
        </div>""")
            else:
                f.write('<div class="success"><strong>✅ Aucune vulnérabilité SQL évidente</strong> détectée sur les URLs testées avec cette configuration de scan automatisé.</div>')

            f.write('<h2>📊 Résultats détaillés par URL</h2>')
            
            # Afficher les résultats pour chaque URL
            for url, result in sqlmap_results.items():
                risk_class = {
                    'HIGH': 'risk-high',
                    'MEDIUM': 'risk-medium', 
                    'LOW': 'risk-low',
                    'UNKNOWN': 'risk-unknown'
                }.get(result['risk_level'], 'risk-unknown')
                
                f.write(f"""
        <div class="url-test">
            <div class="url-header">🌐 {url}</div>
            <p><strong>Statut du scan:</strong> <span class="{risk_class}">{result['status']}</span></p>
            <p><strong>Niveau de risque:</strong> <span class="{risk_class}">{result['risk_level']}</span></p>""")
                
                if result['vulnerabilities']:
                    f.write('<h4>🚨 Vulnérabilités et détections:</h4>')
                    for vuln in result['vulnerabilities']:
                        if vuln.strip():  # Éviter les lignes vides
                            vuln_class = "vulnerability"
                            if "might" in vuln.lower() or "potential" in vuln.lower():
                                vuln_class = "potential"
                            f.write(f'<div class="{vuln_class}">🔴 {vuln}</div>')
                elif result['risk_level'] == 'LOW':
                    f.write('<div class="safe">✅ Aucune vulnérabilité d\'injection SQL détectée sur cette URL</div>')
                elif result['risk_level'] == 'UNKNOWN':
                    f.write('<div class="error">❓ Scan incomplet ou erreur lors de l\'analyse</div>')
                
                # Afficher la sortie SQLMap si disponible
                if result['output'] and len(result['output']) > 50:
                    f.write(f'<details><summary>📄 Sortie complète de SQLMap</summary><pre>{result["output"]}</pre></details>')
                
                # Afficher les erreurs si disponibles
                if result['errors']:
                    f.write(f'<details><summary>⚠️ Erreurs et avertissements</summary><pre>{result["errors"]}</pre></details>')
                
                f.write('</div>')

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="summary">
            <h3>💡 Actions prioritaires contre l'injection SQL</h3>
            <ul>
                <li><strong>🔒 Requêtes préparées:</strong> Remplacez immédiatement toutes les requêtes SQL dynamiques par des prepared statements</li>
                <li><strong>✅ Validation stricte:</strong> Validez, filtrez et échappez toutes les entrées utilisateur avant utilisation</li>
                <li><strong>🔐 Principe du moindre privilège:</strong> Limitez les droits d'accès de la base de données au strict minimum</li>
                <li><strong>🛡️ WAF (Web Application Firewall):</strong> Déployez une protection applicative pour filtrer les attaques</li>
                <li><strong>📊 Monitoring continu:</strong> Surveillez et loggez toutes les tentatives d'injection SQL</li>
                <li><strong>🔄 Tests réguliers:</strong> Effectuez des audits de sécurité périodiques</li>
                <li><strong>📚 Formation équipe:</strong> Sensibilisez les développeurs aux bonnes pratiques de sécurité</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🔧 Exemples de code sécurisé</h3>
            <p><strong>PHP avec PDO (Recommandé):</strong></p>
            <pre>// ❌ Code vulnérable à l'injection SQL
$sql = "SELECT * FROM users WHERE id = " . $_GET['id'];
$result = $db->query($sql);

// ✅ Code sécurisé avec requête préparée
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
$result = $stmt->fetchAll();

// ✅ Alternative avec paramètres nommés
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id AND status = :status");
$stmt->execute([':id' => $_GET['id'], ':status' => 'active']);</pre>
            
            <p><strong>Python avec SQLAlchemy:</strong></p>
            <pre>// ❌ Code vulnérable
query = f"SELECT * FROM users WHERE id = {user_id}"
result = db.execute(query)

// ✅ Code sécurisé
result = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})

// ✅ Avec ORM SQLAlchemy
user = session.query(User).filter(User.id == user_id).first()</pre>

            <p><strong>Node.js avec Sequelize:</strong></p>
            <pre>// ❌ Code vulnérable
const query = `SELECT * FROM users WHERE id = ${userId}`;
db.query(query);

// ✅ Code sécurisé
const user = await User.findOne({ where: { id: userId } });</pre>
        </div>
        
        <div class="tech-info">
            <h3>🔍 Techniques d'injection testées par SQLMap</h3>
            <ul>
                <li><strong>Boolean-based blind:</strong> Injection aveugle basée sur des conditions vraies/fausses</li>
                <li><strong>Error-based:</strong> Injection exploitant les messages d'erreur de la base de données</li>
                <li><strong>Union query:</strong> Injection utilisant l'opérateur UNION SELECT pour extraire des données</li>
                <li><strong>Stacked queries:</strong> Injection permettant l'exécution de requêtes multiples</li>
                <li><strong>Time-based blind:</strong> Injection aveugle basée sur les délais de réponse</li>
            </ul>
        </div>
        
        <div class="warning">
            <h3>⚠️ Limitations de ce scan automatisé</h3>
            <ul>
                <li><strong>Configuration conservatrice:</strong> Scan rapide avec paramètres de sécurité (niveau 1, risque 1)</li>
                <li><strong>Nombre d'URLs limité:</strong> Test sur {len(final_test_urls)} URLs pour éviter les timeouts</li>
                <li><strong>Timeout réduit:</strong> 60 secondes maximum par URL pour optimiser les performances</li>
                <li><strong>Audit complet recommandé:</strong> Ce scan ne remplace pas un test de pénétration approfondi</li>
                <li><strong>Faux négatifs possibles:</strong> Certaines vulnérabilités complexes peuvent ne pas être détectées</li>
                <li><strong>Tests manuels conseillés:</strong> Vérification manuelle recommandée pour les URLs à fort enjeu</li>
            </ul>
        </div>
        
        <div class="error">
            <h3>🚨 Plan d'action d'urgence si vulnérabilités détectées</h3>
            <ol>
                <li><strong>🔒 Isolement immédiat:</strong> Restreindre l'accès aux URLs vulnérables</li>
                <li><strong>🛠️ Correction du code:</strong> Implémenter des requêtes préparées sur les paramètres vulnérables</li>
                <li><strong>✅ Validation renforcée:</strong> Ajouter une validation stricte de toutes les entrées utilisateur</li>
                <li><strong>🧪 Tests de régression:</strong> Vérifier que les corrections éliminent les vulnérabilités</li>
                <li><strong>📋 Audit complet:</strong> Effectuer un audit de sécurité approfondi de l'application</li>
                <li><strong>📊 Monitoring:</strong> Mettre en place une surveillance continue des tentatives d'attaque</li>
                <li><strong>📚 Documentation:</strong> Documenter les corrections et former l'équipe de développement</li>
            </ol>
        </div>
        
        <div class="info">
            <h3>📞 Ressources et support</h3>
            <p>
                <strong>🌐 Documentation SQLMap:</strong> <a href="https://sqlmap.org/" target="_blank">https://sqlmap.org/</a><br>
                <strong>📚 OWASP SQL Injection:</strong> <a href="https://owasp.org/www-community/attacks/SQL_Injection" target="_blank">Guide OWASP</a><br>
                <strong>🔒 Sécurisation des applications web:</strong> Consultez un expert en cybersécurité pour un audit complet
            </p>
        </div>
        
        <div class="tech-info">
            <p><strong>📄 Rapport généré automatiquement par SQLMap</strong> - Version conteneurisée<br>
            <em>Ce rapport est confidentiel et destiné uniquement aux équipes autorisées</em></p>
        </div>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport HTML généré avec succès: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport HTML: {e}")
        import traceback
        print(f"Traceback complet: {traceback.format_exc()}")
        return

    # Chiffrement du rapport
    try:
        if not os.path.exists(html_path):
            print(f"❌ Fichier {html_path} introuvable pour le chiffrement")
            return
            
        if os.path.getsize(html_path) == 0:
            print(f"❌ Fichier {html_path} vide, impossible de chiffrer")
            return
            
        print("🔒 Chiffrement du rapport en cours...")
        encrypt_file(html_path)
        
        encrypted_path = html_path + ".aes"
        if os.path.exists(encrypted_path):
            encrypted_size = os.path.getsize(encrypted_path)
            print(f"✅ Rapport chiffré avec succès: {os.path.basename(encrypted_path)} ({encrypted_size} bytes)")
            
            # Supprimer le fichier non chiffré pour la sécurité
            try:
                os.remove(html_path)
                print(f"🗑️ Fichier non chiffré supprimé pour la sécurité")
            except Exception as cleanup_error:
                print(f"⚠️ Impossible de supprimer le fichier non chiffré: {cleanup_error}")
        else:
            print("❌ Le fichier chiffré n'a pas été créé correctement")
        
    except Exception as e:
        print(f"❌ Erreur lors du chiffrement: {e}")
        import traceback
        print(f"Traceback chiffrement: {traceback.format_exc()}")

    print(f"\n🎯 Scan SQLMap terminé pour {target}")
    print(f"📊 Résultats: {high_risk_count} critiques, {medium_risk_count} potentielles, {low_risk_count} sûres")
    if high_risk_count > 0:
        print(f"⚠️ ATTENTION: Des vulnérabilités critiques ont été détectées!")

if __name__ == "__main__":
    main()