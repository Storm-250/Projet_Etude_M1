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

    # Wordlists à essayer
    wordlists = [
        "/usr/share/seclists/Discovery/Web-Content/common.txt",
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt"
    ]
    
    # Trouver une wordlist disponible
    selected_wordlist = None
    for wordlist in wordlists:
        if os.path.exists(wordlist):
            selected_wordlist = wordlist
            break
    
    if not selected_wordlist:
        # Créer une wordlist basique
        selected_wordlist = "ferox_wordlist.txt"
        basic_paths = [
            "admin", "administrator", "login", "signin", "panel", "dashboard",
            "wp-admin", "phpmyadmin", "mysql", "database", "db",
            "backup", "backups", "bak", "old", "tmp", "temp", "test",
            "upload", "uploads", "files", "downloads", "assets",
            "api", "rest", "webservice", "ajax", "json", "xml",
            "config", "configuration", "settings", "env", ".env",
            "logs", "log", "debug", "error", "stats", "status",
            "private", "secret", "hidden", "internal", "dev"
        ]
        
        with open(selected_wordlist, "w") as f:
            f.write("\n".join(basic_paths))
        print(f"📝 Wordlist créée: {selected_wordlist}")

    # URLs à tester
    base_urls = [f"http://{target}", f"https://{target}"]
    ferox_results = {}
    
    for base_url in base_urls:
        print(f"🔍 Test de {base_url}...")
        
        try:
            # Feroxbuster avec options optimisées
            ferox_cmd = [
                "feroxbuster",
                "-u", base_url,
                "-w", selected_wordlist,
                "-t", "50",              # 50 threads
                "-d", "2",               # Profondeur 2
                "--timeout", "10",       # Timeout 10s
                "-x", "php,html,txt,js,css,xml,json,bak,old,tmp",  # Extensions
                "--no-recursion",        # Pas de récursion pour limiter le temps
                "-q",                    # Mode silencieux
                "-k"                     # Ignorer les certificats SSL
            ]
            
            print(f"🚀 Commande: {' '.join(ferox_cmd)}")
            
            ferox_result = subprocess.run(
                ferox_cmd, 
                capture_output=True, 
                text=True, 
                timeout=400  # 7 minutes max
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
                    if any(code in line for code in ['200', '301', '302', '403', '500']):
                        parts = line.split()
                        if len(parts) >= 4 and parts[3].startswith('http'):
                            status_code = parts[0]
                            url = parts[3]
                            found_urls.append({'url': url, 'status': status_code, 'raw': line})
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
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout pour {base_url}")
            ferox_results[base_url] = {
                'status': '⏰ Timeout',
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
        .url-result {{ background-color: white; padding: 8px; margin: 5px 0; border-radius: 3px; font-family: monospace; font-size: 12px; display: flex; align-items: center; }}
        .status-200 {{ border-left: 3px solid #28a745; }}
        .status-301, .status-302 {{ border-left: 3px solid #17a2b8; }}
        .status-403 {{ border-left: 3px solid #ffc107; }}
        .status-404 {{ border-left: 3px solid #6c757d; }}
        .status-500 {{ border-left: 3px solid #dc3545; }}
        .status-code {{ padding: 2px 6px; border-radius: 3px; color: white; font-weight: bold; margin-right: 10px; min-width: 30px; text-align: center; }}
        .code-200 {{ background-color: #28a745; }}
        .code-301, .code-302 {{ background-color: #17a2b8; }}
        .code-403 {{ background-color: #ffc107; color: black; }}
        .code-404 {{ background-color: #6c757d; }}
        .code-500 {{ background-color: #dc3545; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .critical-findings {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Rapport Feroxbuster - Énumération Web Rapide</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Feroxbuster Fast Directory Enumeration<br>
            <strong>📋 Wordlist:</strong> {os.path.basename(selected_wordlist)}<br>
            <strong>🔍 URLs de base testées:</strong> {len(base_urls)}
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
                f.write(f'<div class="success"><strong>✅ {total_urls} URLs découvertes</strong> avec différents codes de statut.</div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucune URL découverte</strong> avec la wordlist utilisée.</div>')

            # Identifier les découvertes critiques
            critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'debug', 'phpmyadmin']
            interesting_findings = []
            
            for url, result in ferox_results.items():
                for url_data in result['found_urls']:
                    url_path = url_data['url']
                    if any(keyword in url_path.lower() for keyword in critical_keywords):
                        interesting_findings.append(url_data)

            if interesting_findings:
                f.write('<div class="critical-findings">')
                f.write('<h3>🚨 Découvertes Critiques</h3>')
                f.write('<p>URLs potentiellement sensibles détectées :</p>')
                for finding in interesting_findings:
                    status_class = f"status-{finding['status']}"
                    code_class = f"code-{finding['status']}"
                    f.write(f'''
                    <div class="url-result {status_class}">
                        <span class="status-code {code_class}">{finding['status']}</span>
                        <span>🔴 {finding['url']}</span>
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
                                <span>{url_data['url']}</span>
                            </div>''')
                
                if result['errors']:
                    f.write(f'<details><summary>Erreurs</summary><pre>{result["errors"]}</pre></details>')
                
                f.write('</div>')

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Recommandées</h3>
            <ul>
                <li><strong>Code 200 (Succès):</strong> Examinez le contenu pour des informations sensibles</li>
                <li><strong>Code 301/302 (Redirections):</strong> Vérifiez les destinations des redirections</li>
                <li><strong>Code 403 (Interdit):</strong> Répertoires existants mais protégés - vérifiez la sécurité</li>
                <li><strong>Code 500 (Erreur serveur):</strong> Erreurs potentielles révélant des informations</li>
                <li><strong>Panels d'admin:</strong> Sécurisez les interfaces d'administration découvertes</li>
                <li><strong>Fichiers de backup:</strong> Supprimez ou protégez les fichiers de sauvegarde exposés</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Note importante:</strong> Feroxbuster est optimisé pour la rapidité. 
            Un scan plus approfondi avec des wordlists étendues pourrait révéler davantage de contenu.
        </div>
        
        <div class="info">
            <h3>🔍 Analyse Manuelle Recommandée</h3>
            <ul>
                <li>Visitez manuellement chaque URL découverte</li>
                <li>Testez l'authentification sur les panels d'administration</li>
                <li>Vérifiez les permissions d'accès aux répertoires</li>
                <li>Recherchez des fuites d'informations dans les erreurs</li>
                <li>Analysez le contenu des fichiers accessibles</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>📊 Codes de Statut HTTP</h3>
            <ul>
                <li><strong>200:</strong> Contenu accessible - À examiner</li>
                <li><strong>301/302:</strong> Redirection - Suivre la destination</li>
                <li><strong>403:</strong> Accès interdit - Répertoire existe mais protégé</li>
                <li><strong>404:</strong> Non trouvé - Normal</li>
                <li><strong>500:</strong> Erreur serveur - Peut révéler des informations</li>
            </ul>
        </div>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport généré: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return

    # Nettoyage de la wordlist temporaire
    if selected_wordlist == "ferox_wordlist.txt":
        try:
            os.remove(selected_wordlist)
            print(f"🗑️ Wordlist temporaire supprimée")
        except:
            pass

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