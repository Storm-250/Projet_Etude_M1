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
    
    print(f"🔍 Scan Feroxbuster COMPLET (Directory + File) sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # FIX: Utiliser le bon chemin pour common.txt dans Docker
    wordlist_paths = [
        "tools/common.txt",
        "common.txt", 
        "/app/tools/common.txt",
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt"
    ]
    
    selected_wordlist = None
    wordlist_info = ""
    
    for wordlist_path in wordlist_paths:
        if os.path.exists(wordlist_path):
            selected_wordlist = wordlist_path
            try:
                with open(selected_wordlist, 'r') as f:
                    line_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
                wordlist_info = f"{os.path.basename(selected_wordlist)} ({line_count} entrées)"
                print(f"📋 Wordlist trouvée: {wordlist_info} à {selected_wordlist}")
            except:
                wordlist_info = os.path.basename(selected_wordlist)
                print(f"📋 Wordlist trouvée: {wordlist_info} à {selected_wordlist}")
            break
    
    if not selected_wordlist:
        print(f"❌ Aucune wordlist trouvée dans les chemins :")
        for path in wordlist_paths:
            print(f"   - {path}")
        sys.exit(1)

    # Vérifier la disponibilité de feroxbuster
    try:
        subprocess.run(["feroxbuster", "--help"], capture_output=True, text=True, timeout=5)
        print("✅ Feroxbuster disponible")
    except FileNotFoundError:
        print("❌ Feroxbuster non trouvé. Vérifiez l'installation Docker.")
        sys.exit(1)

    # URLs à tester
    base_urls = [f"http://{target}", f"https://{target}"]
    
    # Configuration des scans spécialisés
    scan_configs = {
        'directories': {
            'name': 'Répertoires',
            'extensions': [],  # Pas d'extensions = répertoires uniquement
            'depth': 3,
            'threads': 50,
            'description': 'Découverte de la structure de répertoires'
        },
        'web_files': {
            'name': 'Fichiers Web',
            'extensions': ['php', 'html', 'htm', 'js', 'css', 'xml', 'json', 'txt'],
            'depth': 2,
            'threads': 80,
            'description': 'Fichiers web courants et scripts'
        },
        'admin_files': {
            'name': 'Administration',
            'extensions': ['php', 'asp', 'aspx', 'jsp', 'do', 'action', 'cgi', 'pl', 'py', 'rb'],
            'depth': 2,
            'threads': 60,
            'description': 'Interfaces et scripts d\'administration'
        },
        'backup_files': {
            'name': 'Fichiers de Backup',
            'extensions': ['bak', 'backup', 'old', 'orig', 'save', 'tmp', 'swp', '~', 'sql', 'dump', 'zip', 'tar', 'gz'],
            'depth': 1,
            'threads': 40,
            'description': 'Sauvegardes et fichiers temporaires'
        },
        'config_files': {
            'name': 'Configuration',
            'extensions': ['conf', 'config', 'cfg', 'ini', 'env', 'properties', 'yml', 'yaml', 'json'],
            'depth': 2,
            'threads': 30,
            'description': 'Fichiers de configuration et paramètres'
        }
    }
    
    all_results = {}
    
    for base_url in base_urls:
        print(f"\n🌐 === Scan de {base_url} ===")
        all_results[base_url] = {}
        
        for scan_type, config in scan_configs.items():
            print(f"\n🔍 {config['name']}: {config['description']}...")
            
            try:
                # Construction de la commande feroxbuster
                ferox_cmd = [
                    "feroxbuster",
                    "-u", base_url,
                    "-w", selected_wordlist,
                    "-t", str(config['threads']),     # Threads spécialisés par type
                    "-d", str(config['depth']),       # Profondeur adaptée
                    "--timeout", "15",                # Timeout
                    "-s", "200,204,301,302,307,308,401,403,405,500,503",  # Status codes
                    "--auto-tune",                    # Auto-optimisation
                    "-q",                             # Mode silencieux
                    "-k",                             # Ignorer certificats SSL
                    "--collect-words",                # Collecter les mots pour améliorer la découverte
                    "--dont-filter"                   # Ne pas filtrer automatiquement
                ]
                
                # Ajouter les extensions si ce n'est pas un scan de répertoires
                if config['extensions']:
                    extensions_str = ','.join(config['extensions'])
                    ferox_cmd.extend(["-x", extensions_str])
                else:
                    # Pour les répertoires, utiliser le mode récursion sans extensions
                    ferox_cmd.append("--no-recursion")
                
                print(f"🚀 Commande: {' '.join(ferox_cmd)}")
                
                ferox_result = subprocess.run(
                    ferox_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=900  # 15 minutes max par scan
                )
                
                output = ferox_result.stdout
                errors = ferox_result.stderr
                
                # Analyser les résultats Feroxbuster
                found_urls = []
                status_codes = {}
                sizes = {}
                
                if output:
                    lines = output.strip().split('\n')
                    for line in lines:
                        # Format Feroxbuster: 200 GET 1234l 567w 8901c http://example.com/path
                        # Ou plus simple: 200     GET       1234c http://example.com/path
                        parts = line.split()
                        
                        if len(parts) >= 4:
                            # Chercher le code de statut (premier nombre de 3 chiffres)
                            status_code = None
                            url = None
                            size = None
                            
                            for i, part in enumerate(parts):
                                # Code de statut
                                if part.isdigit() and len(part) == 3:
                                    status_code = part
                                # URL (commence par http)
                                elif part.startswith('http'):
                                    url = part
                                # Taille (se termine par 'c')
                                elif part.endswith('c') and part[:-1].isdigit():
                                    size = int(part[:-1])
                            
                            if url and status_code:
                                found_urls.append({
                                    'url': url,
                                    'status': status_code,
                                    'size': size,
                                    'raw': line.strip()
                                })
                                status_codes[status_code] = status_codes.get(status_code, 0) + 1
                                if size:
                                    sizes[url] = size
                
                if ferox_result.returncode == 0:
                    status = f"✅ Terminé ({len(found_urls)} URLs trouvées)"
                else:
                    status = f"⚠️ Terminé avec erreurs (code {ferox_result.returncode})"
                
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': status,
                    'found_urls': found_urls,
                    'status_codes': status_codes,
                    'sizes': sizes,
                    'output': output,
                    'errors': errors,
                    'returncode': ferox_result.returncode
                }
                
                print(f"   {status}")
                if status_codes:
                    status_summary = ", ".join([f"{code}: {count}" for code, count in sorted(status_codes.items())])
                    print(f"   📊 Codes de statut: {status_summary}")
                
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Timeout pour {scan_type}")
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': '⏰ Timeout (> 15 min)',
                    'found_urls': [],
                    'status_codes': {},
                    'sizes': {},
                    'output': 'Scan interrompu par timeout',
                    'errors': '',
                    'returncode': -1
                }
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': f'❌ Erreur: {e}',
                    'found_urls': [],
                    'status_codes': {},
                    'sizes': {},
                    'output': str(e),
                    'errors': '',
                    'returncode': -3
                }

    # Générer le rapport HTML
    try:
        total_urls = sum(len(scan_result['found_urls']) 
                        for url_results in all_results.values() 
                        for scan_result in url_results.values())
        
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Feroxbuster Complet - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #2c3e50; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .scan-section {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #6c757d; }}
        .scan-type {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 3px solid #17a2b8; }}
        .url-result {{ background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; font-family: monospace; font-size: 12px; display: flex; align-items: center; }}
        .url-critical {{ border-left: 3px solid #dc3545; background-color: #f8d7da; }}
        .url-interesting {{ border-left: 3px solid #ffc107; background-color: #fff3cd; }}
        .url-success {{ border-left: 3px solid #28a745; background-color: #d4edda; }}
        .url-redirect {{ border-left: 3px solid #17a2b8; background-color: #d1ecf1; }}
        .status-code {{ padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold; margin-right: 12px; min-width: 35px; text-align: center; }}
        .code-200, .code-204 {{ background-color: #28a745; }}
        .code-301, .code-302, .code-307, .code-308 {{ background-color: #17a2b8; }}
        .code-401 {{ background-color: #fd7e14; }}
        .code-403 {{ background-color: #ffc107; color: black; }}
        .code-405 {{ background-color: #e83e8c; }}
        .code-500, .code-503 {{ background-color: #dc3545; }}
        .size-info {{ color: #6c757d; font-size: 11px; margin-left: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .scan-overview {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .performance-info {{ background-color: #d1f2eb; padding: 15px; border-left: 4px solid #00d084; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .url-text {{ word-break: break-all; flex-grow: 1; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Rapport Feroxbuster Complet - Directory & File Bruteforcing</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Feroxbuster Advanced Directory & File Enumeration<br>
            <strong>🔍 URLs testées:</strong> {len(base_urls)}<br>
            <strong>🎯 Types de scan:</strong> {len(scan_configs)} (Répertoires, Web, Admin, Backup, Config)<br>
            <strong>🐳 Environnement:</strong> Docker Container
        </div>
        
        <div class="scan-overview">
            <strong>📋 Wordlist utilisée:</strong> {wordlist_info}<br>
            <strong>📂 Chemin:</strong> {selected_wordlist}<br>
            <strong>⚡ Stratégie:</strong> Scan multi-passes avec optimisations spécialisées par type<br>
            <strong>🧠 Intelligence:</strong> Auto-tuning, collection de mots, récursion contrôlée
        </div>
        
        <div class="performance-info">
            <strong>🚀 Optimisations Feroxbuster Appliquées</strong><br>
            • <strong>Threads adaptatifs:</strong> 30-80 threads selon le type de contenu<br>
            • <strong>Profondeur variable:</strong> 1-3 niveaux selon la criticité<br>
            • <strong>Collection de mots:</strong> Amélioration dynamique de la découverte<br>
            • <strong>Auto-tuning:</strong> Adaptation automatique à la réactivité du serveur
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{total_urls}</h3>
                <p>URLs trouvées</p>
            </div>""")

            # Statistiques globales
            total_scans = sum(len(url_results) for url_results in all_results.values())
            successful_scans = sum(1 for url_results in all_results.values() 
                                 for scan_result in url_results.values() 
                                 if scan_result['returncode'] == 0)
            
            f.write(f"""
            <div class="stat-card">
                <h3>{total_scans}</h3>
                <p>Scans effectués</p>
            </div>
            <div class="stat-card">
                <h3>{successful_scans}</h3>
                <p>Scans réussis</p>
            </div>""")

            # Compter les codes de statut
            all_status_codes = {}
            for url_results in all_results.values():
                for scan_result in url_results.values():
                    for code, count in scan_result['status_codes'].items():
                        all_status_codes[code] = all_status_codes.get(code, 0) + count

            for code, count in sorted(all_status_codes.items()):
                f.write(f"""
            <div class="stat-card">
                <h3>{count}</h3>
                <p>Code {code}</p>
            </div>""")

            f.write('</div>')

            if total_urls > 0:
                f.write(f'<div class="success"><strong>✅ {total_urls} URLs découvertes</strong> via scan intelligent multi-passes</div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucune URL découverte</strong>. Le site pourrait être bien sécurisé ou avoir une structure non-standard.</div>')

            # Vue d'ensemble des configurations de scan
            f.write('<h2>📊 Configurations des Scans Spécialisés</h2>')
            for scan_type, config in scan_configs.items():
                ext_list = ', '.join(config['extensions'][:10]) if config['extensions'] else 'Aucune (répertoires uniquement)'
                if len(config['extensions']) > 10:
                    ext_list += f" ... (+{len(config['extensions'])-10} autres)"
                
                f.write(f"""
        <div class="scan-type">
            <h4>🔍 {config['name']}</h4>
            <p>{config['description']}</p>
            <p><strong>Extensions:</strong> {ext_list}</p>
            <p><strong>Threads:</strong> {config['threads']} | <strong>Profondeur:</strong> {config['depth']}</p>
        </div>""")

            # Résultats par URL
            for base_url, url_results in all_results.items():
                f.write(f"""
        <div class="scan-section">
            <h2>🌐 Résultats pour {base_url}</h2>""")
                
                for scan_type, scan_result in url_results.items():
                    config = scan_result['config']
                    f.write(f"""
            <div class="scan-type">
                <h3>🔍 {config['name']} - {scan_result['status']}</h3>
                <p>{config['description']}</p>
                <p><strong>URLs trouvées:</strong> {len(scan_result['found_urls'])} | 
                   <strong>Config:</strong> {config['threads']} threads, profondeur {config['depth']}</p>""")
                    
                    if scan_result['status_codes']:
                        f.write('<p><strong>Codes de statut:</strong> ')
                        for code, count in sorted(scan_result['status_codes'].items()):
                            f.write(f'<span class="status-code code-{code}">{code}: {count}</span> ')
                        f.write('</p>')
                    
                    # Classer les URLs par criticité
                    critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'debug', 'phpmyadmin']
                    interesting_keywords = ['upload', 'api', 'panel', 'dashboard', 'test', 'dev', 'staging', 'auth']
                    
                    critical_urls = []
                    interesting_urls = []
                    redirect_urls = []
                    other_urls = []
                    
                    for url_data in scan_result['found_urls']:
                        url_lower = url_data['url'].lower()
                        status = url_data['status']
                        
                        if any(keyword in url_lower for keyword in critical_keywords):
                            critical_urls.append(url_data)
                        elif any(keyword in url_lower for keyword in interesting_keywords):
                            interesting_urls.append(url_data)
                        elif status in ['301', '302', '307', '308']:
                            redirect_urls.append(url_data)
                        else:
                            other_urls.append(url_data)
                    
                    # Afficher les URLs critiques
                    if critical_urls:
                        f.write('<h4>🚨 URLs Critiques</h4>')
                        for url_data in critical_urls:
                            status_class = f"code-{url_data['status']}"
                            size_info = f"({url_data['size']} bytes)" if url_data.get('size') else ""
                            f.write(f'''
                            <div class="url-result url-critical">
                                <span class="status-code {status_class}">{url_data['status']}</span>
                                <span class="url-text">🔴 {url_data['url']}</span>
                                <span class="size-info">{size_info}</span>
                            </div>''')
                    
                    # Afficher les URLs intéressantes
                    if interesting_urls:
                        f.write('<h4>⚠️ URLs Intéressantes</h4>')
                        for url_data in interesting_urls:
                            status_class = f"code-{url_data['status']}"
                            size_info = f"({url_data['size']} bytes)" if url_data.get('size') else ""
                            f.write(f'''
                            <div class="url-result url-interesting">
                                <span class="status-code {status_class}">{url_data['status']}</span>
                                <span class="url-text">🟡 {url_data['url']}</span>
                                <span class="size-info">{size_info}</span>
                            </div>''')
                    
                    # Afficher les redirections
                    if redirect_urls:
                        f.write('<h4>🔄 Redirections</h4>')
                        for url_data in redirect_urls:
                            status_class = f"code-{url_data['status']}"
                            size_info = f"({url_data['size']} bytes)" if url_data.get('size') else ""
                            f.write(f'''
                            <div class="url-result url-redirect">
                                <span class="status-code {status_class}">{url_data['status']}</span>
                                <span class="url-text">🔵 {url_data['url']}</span>
                                <span class="size-info">{size_info}</span>
                            </div>''')
                    
                    # Afficher les autres URLs (limité pour éviter un rapport trop long)
                    if other_urls:
                        f.write(f'<h4>📄 Autres URLs ({len(other_urls)})</h4>')
                        for url_data in other_urls[:25]:  # Limiter à 25 pour la lisibilité
                            status_class = f"code-{url_data['status']}"
                            size_info = f"({url_data['size']} bytes)" if url_data.get('size') else ""
                            f.write(f'''
                            <div class="url-result">
                                <span class="status-code {status_class}">{url_data['status']}</span>
                                <span class="url-text">📄 {url_data['url']}</span>
                                <span class="size-info">{size_info}</span>
                            </div>''')
                        if len(other_urls) > 25:
                            f.write(f'<p><em>... et {len(other_urls)-25} autres URLs</em></p>')
                    
                    if scan_result['errors']:
                        f.write(f'<details><summary>Erreurs/Avertissements</summary><pre>{scan_result["errors"]}</pre></details>')
                    
                    f.write('</div>')
                
                f.write('</div>')

            f.write(f"""
        <h2>🛡️ Analyse de Sécurité et Recommandations</h2>
        <div class="error">
            <h3>🚨 Actions Urgentes</h3>
            <ul>
                <li><strong>URLs Critiques:</strong> Sécurisez immédiatement les interfaces d'administration</li>
                <li><strong>Fichiers de Backup:</strong> Supprimez les sauvegardes accessibles publiquement</li>
                <li><strong>Fichiers de Config:</strong> Protégez les fichiers de configuration exposés</li>
                <li><strong>Codes 500/503:</strong> Corrigez les erreurs serveur qui révèlent des informations</li>
            </ul>
        </div>
        
        <div class="warning">
            <h3>⚠️ Investigations Recommandées</h3>
            <ul>
                <li><strong>URLs Intéressantes:</strong> Examinez manuellement chaque endpoint découvert</li>
                <li><strong>Redirections:</strong> Vérifiez les destinations et la logique de redirection</li>
                <li><strong>Codes 401/403:</strong> Testez l'authentification et les permissions</li>
                <li><strong>Tailles de fichiers:</strong> Analysez les fichiers volumineux pour du contenu sensible</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🎯 Méthodologie Multi-passes Feroxbuster</h3>
            <p>Ce scan utilise <strong>5 passes spécialisées</strong> pour une découverte optimale :</p>
            <ul>
                <li><strong>Pass 1 - Répertoires:</strong> Structure de base (50 threads, profondeur 3)</li>
                <li><strong>Pass 2 - Fichiers Web:</strong> Contenu public (80 threads, profondeur 2)</li>
                <li><strong>Pass 3 - Administration:</strong> Interfaces admin (60 threads, profondeur 2)</li>
                <li><strong>Pass 4 - Backups:</strong> Sauvegardes (40 threads, profondeur 1)</li>
                <li><strong>Pass 5 - Configuration:</strong> Fichiers de config (30 threads, profondeur 2)</li>
            </ul>
        </div>
        
        <div class="success">
            <h3>🚀 Avantages du Scan Feroxbuster Avancé</h3>
            <ul>
                <li><strong>Intelligence adaptative:</strong> Auto-tuning selon la réactivité du serveur</li>
                <li><strong>Collection de mots:</strong> Amélioration dynamique des wordlists</li>
                <li><strong>Performance optimisée:</strong> Threads et profondeur adaptés par type</li>
                <li><strong>Classification automatique:</strong> Tri par criticité et type de contenu</li>
                <li><strong>Analyse de taille:</strong> Information sur la taille des fichiers découverts</li>
                <li><strong>Récursion contrôlée:</strong> Exploration intelligente sans spirale infinie</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>📊 Guide d'Interprétation des Résultats</h3>
            <ul>
                <li><strong>Code 200/204:</strong> Contenu accessible - examiner en priorité</li>
                <li><strong>Code 301/302:</strong> Redirections - suivre les destinations</li>
                <li><strong>Code 401:</strong> Authentification requise - tester les credentials</li>
                <li><strong>Code 403:</strong> Interdit mais existant - vérifier les permissions</li>
                <li><strong>Code 405:</strong> Méthode non autorisée - tester POST/PUT/DELETE</li>
                <li><strong>Code 500/503:</strong> Erreurs serveur - peuvent révéler des informations</li>
            </ul>
        </div>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport complet généré: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return

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