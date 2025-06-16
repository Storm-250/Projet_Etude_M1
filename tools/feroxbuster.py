import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: feroxbuster.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"feroxbuster_{date}.html")
    
    print(f"🔍 Scan Feroxbuster en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Utiliser common.txt depuis le répertoire courant
    selected_wordlist = "common.txt"
    wordlist_info = ""
    
    if os.path.exists(selected_wordlist):
        # Compter les lignes pour info
        try:
            with open(selected_wordlist, 'r') as f:
                line_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
            wordlist_info = f"common.txt ({line_count} entrées)"
            print(f"📋 Wordlist trouvée: {wordlist_info}")
        except:
            wordlist_info = "common.txt"
            print(f"📋 Wordlist trouvée: {wordlist_info}")
    else:
        print(f"❌ Fichier common.txt non trouvé dans le répertoire courant")
        print("📥 Veuillez télécharger common.txt depuis :")
        print("   https://github.com/danielmiessler/SecLists/raw/master/Discovery/Web-Content/common.txt")
        sys.exit(1)

    # URLs à tester
    base_urls = [f"http://{target}", f"https://{target}"]
    ferox_results = {}
    
    for base_url in base_urls:
        print(f"🔍 Test de {base_url}...")
        
        try:
            # Feroxbuster avec options optimisées pour common.txt
            ferox_cmd = [
                "feroxbuster",
                "-u", base_url,
                "-w", selected_wordlist,
                "-t", "100",             # 100 threads (ferox est plus efficace avec plus de threads)
                "-d", "3",               # Profondeur 3 (bon compromis)
                "--timeout", "15",       # Timeout 15s
                "-x", "php,html,txt,js,css,xml,json,bak,old,tmp,asp,aspx,jsp",  # Extensions
                "-s", "200,204,301,302,307,308,401,403,405,500",  # Status codes intéressants
                "--auto-tune",           # Auto-tune pour optimiser les performances
                "-q",                    # Mode silencieux
                "-k",                    # Ignorer les certificats SSL
                "--no-recursion"         # Pas de récursion automatique pour contrôler le scan
            ]
            
            print(f"🚀 Commande: {' '.join(ferox_cmd)}")
            
            ferox_result = subprocess.run(
                ferox_cmd, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10 minutes max pour common.txt
            )
            
            output = ferox_result.stdout
            errors = ferox_result.stderr
            
            # Analyser les résultats
            found_urls = []
            status_codes = {}
            
            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    # Feroxbuster format: 200 GET 1234c http://example.com/path
                    # Ou: 200     GET       1234l      567w     8901c http://example.com/path
                    if any(code in line for code in ['200', '301', '302', '401', '403', '405', '500']):
                        parts = line.split()
                        if len(parts) >= 4:
                            # Trouver l'URL (commence par http)
                            url = None
                            status_code = None
                            for i, part in enumerate(parts):
                                if part.startswith('http'):
                                    url = part
                                    # Le code de statut est généralement le premier élément
                                    if parts[0].isdigit():
                                        status_code = parts[0]
                                    break
                            
                            if url and status_code:
                                found_urls.append({'url': url, 'status': status_code, 'raw': line.strip()})
                                status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            if ferox_result.returncode == 0:
                status = f"✅ Terminé ({len(found_urls)} URLs trouvées)"
            else:
                status = f"⚠️ Terminé avec erreurs (code {ferox_result.returncode})"
            
            ferox_results[base_url] = {
                'status': status,
                'found_urls': found_urls,
                'status_codes': status_codes,
                'output': output,
                'errors': errors,
                'returncode': ferox_result.returncode
            }
            
            print(f"   {status}")
            if status_codes:
                status_summary = ", ".join([f"{code}: {count}" for code, count in sorted(status_codes.items())])
                print(f"   📊 Codes de statut: {status_summary}")
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout pour {base_url}")
            ferox_results[base_url] = {
                'status': '⏰ Timeout (> 10 min)',
                'found_urls': [],
                'status_codes': {},
                'output': 'Scan interrompu par timeout',
                'errors': '',
                'returncode': -1
            }
        except FileNotFoundError:
            print(f"   ❌ Feroxbuster non trouvé")
            ferox_results[base_url] = {
                'status': '❌ Outil manquant',
                'found_urls': [],
                'status_codes': {},
                'output': 'Feroxbuster non installé',
                'errors': '',
                'returncode': -2
            }
            break
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            ferox_results[base_url] = {
                'status': f'❌ Erreur: {e}',
                'found_urls': [],
                'status_codes': {},
                'output': str(e),
                'errors': '',
                'returncode': -3
            }

    # Générer le rapport HTML
    try:
        total_urls = sum(len(r['found_urls']) for r in ferox_results.values())
        
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Feroxbuster - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .url-scan {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #6c757d; }}
        .url-result {{ background-color: white; padding: 10px; margin: 5px 0; border-radius: 3px; font-family: monospace; font-size: 12px; display: flex; align-items: center; }}
        .status-200 {{ border-left: 3px solid #28a745; }}
        .status-301, .status-302, .status-307, .status-308 {{ border-left: 3px solid #17a2b8; }}
        .status-401 {{ border-left: 3px solid #fd7e14; }}
        .status-403 {{ border-left: 3px solid #ffc107; }}
        .status-404 {{ border-left: 3px solid #6c757d; }}
        .status-405 {{ border-left: 3px solid #e83e8c; }}
        .status-500 {{ border-left: 3px solid #dc3545; }}
        .status-code {{ padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold; margin-right: 12px; min-width: 35px; text-align: center; }}
        .code-200 {{ background-color: #28a745; }}
        .code-301, .code-302, .code-307, .code-308 {{ background-color: #17a2b8; }}
        .code-401 {{ background-color: #fd7e14; }}
        .code-403 {{ background-color: #ffc107; color: black; }}
        .code-404 {{ background-color: #6c757d; }}
        .code-405 {{ background-color: #e83e8c; }}
        .code-500 {{ background-color: #dc3545; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .critical-findings {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .wordlist-info {{ background-color: #e7f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 15px 0; border-radius: 0 3px 3px 0; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
        .url-text {{ word-break: break-all; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Rapport Feroxbuster - Énumération Web Rapide</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Feroxbuster Fast Directory Enumeration<br>
            <strong>🔍 URLs de base testées:</strong> {len(base_urls)}
        </div>
        
        <div class="wordlist-info">
            <strong>📋 Wordlist utilisée:</strong> {wordlist_info}<br>
            <strong>⚡ Stratégie:</strong> Scan rapide et récursif avec common.txt local optimisé pour Feroxbuster<br>
            <strong>🎯 Profondeur:</strong> 3 niveaux | <strong>🔗 Threads:</strong> 100 | <strong>⏱️ Timeout:</strong> 15s
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{total_urls}</h3>
                <p>URLs trouvées</p>
            </div>""")

            # Statistiques des codes de statut
            all_status_codes = {}
            for result in ferox_results.values():
                for code, count in result['status_codes'].items():
                    all_status_codes[code] = all_status_codes.get(code, 0) + count

            for code, count in sorted(all_status_codes.items()):
                f.write(f"""
            <div class="stat">
                <h3>{count}</h3>
                <p>Code {code}</p>
            </div>""")

            f.write('</div>')

            if total_urls > 0:
                f.write(f'<div class="success"><strong>✅ {total_urls} URLs découvertes</strong> avec common.txt local et récursion intelligente.</div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucune URL découverte</strong> avec common.txt local. Le site pourrait avoir une structure non-standard ou être bien protégé.</div>')

            # Identifier les découvertes critiques (optimisé pour common.txt)
            critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'debug', 'phpmyadmin', 'mysql']
            interesting_keywords = ['upload', 'api', 'panel', 'dashboard', 'test', 'dev', 'staging', 'auth']
            info_keywords = ['robots.txt', 'sitemap.xml', 'phpinfo', 'info.php', '.htaccess']
            
            critical_findings = []
            interesting_findings = []
            info_findings = []
            
            for url, result in ferox_results.items():
                for url_data in result['found_urls']:
                    url_path = url_data['url'].lower()
                    if any(keyword in url_path for keyword in critical_keywords):
                        critical_findings.append(url_data)
                    elif any(keyword in url_path for keyword in interesting_keywords):
                        interesting_findings.append(url_data)
                    elif any(keyword in url_path for keyword in info_keywords):
                        info_findings.append(url_data)

            if critical_findings:
                f.write('<div class="critical-findings">')
                f.write('<h3>🚨 Découvertes Critiques</h3>')
                f.write('<p>URLs potentiellement sensibles détectées :</p>')
                for finding in critical_findings:
                    status_class = f"status-{finding['status']}"
                    code_class = f"code-{finding['status']}"
                    f.write(f'''
                    <div class="url-result {status_class}">
                        <span class="status-code {code_class}">{finding['status']}</span>
                        <span class="url-text">🔴 {finding['url']}</span>
                    </div>''')
                f.write('</div>')

            if interesting_findings:
                f.write('<div class="warning">')
                f.write('<h3>⚠️ Découvertes Intéressantes</h3>')
                f.write('<p>URLs méritant une investigation :</p>')
                for finding in interesting_findings:
                    status_class = f"status-{finding['status']}"
                    code_class = f"code-{finding['status']}"
                    f.write(f'''
                    <div class="url-result {status_class}">
                        <span class="status-code {code_class}">{finding['status']}</span>
                        <span class="url-text">🟡 {finding['url']}</span>
                    </div>''')
                f.write('</div>')

            if info_findings:
                f.write('<div class="info">')
                f.write('<h3>ℹ️ Fichiers d\'Information</h3>')
                f.write('<p>Fichiers informatifs standard découverts :</p>')
                for finding in info_findings:
                    status_class = f"status-{finding['status']}"
                    code_class = f"code-{finding['status']}"
                    f.write(f'''
                    <div class="url-result {status_class}">
                        <span class="status-code {code_class}">{finding['status']}</span>
                        <span class="url-text">🔵 {finding['url']}</span>
                    </div>''')
                f.write('</div>')

            f.write('<h2>📊 Résultats par URL de Base</h2>')
            
            for base_url, result in ferox_results.items():
                f.write(f"""
        <div class="url-scan">
            <h3>🌐 URL: {base_url}</h3>
            <p><strong>Statut:</strong> {result['status']}</p>
            <p><strong>URLs trouvées:</strong> {len(result['found_urls'])}</p>""")

                if result['status_codes']:
                    f.write('<p><strong>Répartition des codes de statut:</strong> ')
                    status_summary = []
                    for code, count in sorted(result['status_codes'].items()):
                        status_summary.append(f"{code}: {count}")
                    f.write(' | '.join(status_summary))
                    f.write('</p>')
                
                if result['found_urls']:
                    f.write('<h4>🔍 URLs découvertes:</h4>')
                    
                    # Grouper par code de statut
                    urls_by_status = {}
                    for url_data in result['found_urls']:
                        status = url_data['status']
                        if status not in urls_by_status:
                            urls_by_status[status] = []
                        urls_by_status[status].append(url_data)
                    
                    for status_code in sorted(urls_by_status.keys()):
                        urls = urls_by_status[status_code]
                        f.write(f'<h5>Code {status_code} ({len(urls)} URLs)</h5>')
                        
                        for url_data in urls:
                            status_class = f"status-{url_data['status']}"
                            code_class = f"code-{url_data['status']}"
                            f.write(f'''
                            <div class="url-result {status_class}">
                                <span class="status-code {code_class}">{url_data['status']}</span>
                                <span class="url-text">{url_data['url']}</span>
                            </div>''')
                
                if result['errors']:
                    f.write(f'<details><summary>Erreurs/Avertissements</summary><pre>{result["errors"]}</pre></details>')
                
                f.write('</div>')

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Recommandées pour common.txt</h3>
            <ul>
                <li><strong>Code 200 (Succès):</strong> Examinez le contenu pour des informations sensibles</li>
                <li><strong>Code 301/302 (Redirections):</strong> Vérifiez les destinations des redirections</li>
                <li><strong>Code 401 (Non autorisé):</strong> Ressources protégées - testez l'authentification</li>
                <li><strong>Code 403 (Interdit):</strong> Répertoires existants mais protégés - vérifiez la configuration</li>
                <li><strong>Code 405 (Méthode non autorisée):</strong> Endpoint existe - testez d'autres méthodes HTTP</li>
                <li><strong>Code 500 (Erreur serveur):</strong> Erreurs pouvant révéler des informations système</li>
                <li><strong>Panels d'admin:</strong> Sécurisez les interfaces d'administration découvertes</li>
                <li><strong>APIs découvertes:</strong> Testez l'authentification et les permissions</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>⚡ À propos de Feroxbuster + common.txt</h3>
            <p><strong>Feroxbuster</strong> avec <strong>common.txt</strong> offre un équilibre optimal entre vitesse et couverture :</p>
            <ul>
                <li><strong>Récursion intelligente:</strong> Explore automatiquement les sous-répertoires découverts</li>
                <li><strong>Multi-threading:</strong> 100 threads simultanés pour une vitesse maximale</li>
                <li><strong>Auto-tuning:</strong> Ajuste automatiquement les performances selon la cible</li>
                <li><strong>Gestion d'état:</strong> Analyse différents codes de statut HTTP</li>
                <li><strong>Extensions multiples:</strong> Teste automatiquement plusieurs extensions de fichiers</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Note importante:</strong> Ce scan utilise common.txt local avec récursion limitée (profondeur 3). 
            Feroxbuster peut découvrir plus de contenu avec des wordlists spécialisées et une profondeur augmentée.
        </div>
        
        <div class="info">
            <h3>🔍 Analyse Manuelle Recommandée</h3>
            <ul>
                <li>Visitez chaque URL découverte dans un navigateur</li>
                <li>Testez l'authentification sur les endpoints protégés (401/403)</li>
                <li>Analysez les redirections pour comprendre la structure du site</li>
                <li>Testez différentes méthodes HTTP sur les endpoints 405</li>
                <li>Examinez les erreurs 500 pour des fuites d'informations</li>
                <li>Vérifiez les permissions sur les APIs découvertes</li>
                <li>Analysez le contenu des fichiers informatifs (robots.txt, etc.)</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>📊 Guide des Codes de Statut HTTP</h3>
            <ul>
                <li><strong>200 (OK):</strong> Contenu accessible - À examiner en priorité</li>
                <li><strong>301/302 (Redirection):</strong> Suivre la destination pour analyse</li>
                <li><strong>401 (Non autorisé):</strong> Authentification requise - tester credentials</li>
                <li><strong>403 (Interdit):</strong> Ressource existe mais accès refusé</li>
                <li><strong>405 (Méthode non autorisée):</strong> Endpoint valide, tester GET/POST/PUT</li>
                <li><strong>500 (Erreur serveur):</strong> Peut révéler des informations sur l'infrastructure</li>
            </ul>
        </div>
        
        <div class="success">
            <h3>🚀 Optimisations Feroxbuster Appliquées</h3>
            <ul>
                <li><strong>Auto-tune activé:</strong> Optimisation automatique selon la réactivité du serveur</li>
                <li><strong>Filtrage intelligent:</strong> Focus sur les codes de statut pertinents</li>
                <li><strong>Extensions ciblées:</strong> Test des extensions les plus courantes</li>
                <li><strong>Récursion contrôlée:</strong> Exploration des sous-répertoires sans spirale infinie</li>
                <li><strong>Timeouts optimisés:</strong> Équilibre entre vitesse et fiabilité</li>
            </ul>
        </div>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport généré: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return

    # Nettoyage - pas de wordlist temporaire à supprimer
    # (common.txt est permanent dans le répertoire)

    # Chiffrement
    try:
        if not os.path.exists(html_path) or os.path.getsize(html_path) == 0:
            print(f"❌ Fichier {html_path} invalide pour chiffrement")
            return
            
        print("🔒 Chiffrement en cours...")
        encrypt_file(html_path)
        
        encrypted_path = html_path + ".aes"
        if os.path.exists(encrypted_path):
            encrypted_size = os.path.getsize(encrypted_path)
            print(f"✅ Fichier chiffré: {encrypted_path} ({encrypted_size} bytes)")
        else:
            print("❌ Le fichier chiffré n'a pas été créé")
        
    except Exception as e:
        print(f"❌ Erreur lors du chiffrement: {e}")

if __name__ == "__main__":
    main()