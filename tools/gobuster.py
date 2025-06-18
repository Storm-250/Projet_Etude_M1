import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: gobuster.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"gobuster_{date}.html")
    
    print(f"🔍 Scan Gobuster COMPLET (Directory + File) sur {target}...")
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

    # Vérifier la disponibilité de gobuster
    try:
        subprocess.run(["gobuster", "--help"], capture_output=True, text=True, timeout=5)
        print("✅ Gobuster disponible")
    except FileNotFoundError:
        print("❌ Gobuster non trouvé. Vérifiez l'installation Docker.")
        sys.exit(1)

    # URLs à tester
    base_urls = [f"http://{target}", f"https://{target}"]
    
    # Types de scan à effectuer pour une découverte complète
    scan_types = {
        'directories': {
            'name': 'Répertoires',
            'extensions': None,  # Pas d'extensions pour les répertoires
            'description': 'Scan des répertoires et dossiers'
        },
        'common_files': {
            'name': 'Fichiers Courants',
            'extensions': 'php,html,htm,txt,xml,js,css',
            'description': 'Fichiers web standards et pages courantes'
        },
        'admin_files': {
            'name': 'Administration',
            'extensions': 'php,asp,aspx,jsp,cgi,pl,py',
            'description': 'Interfaces et scripts d\'administration'
        },
        'config_files': {
            'name': 'Configuration',
            'extensions': 'conf,config,cfg,ini,bak,old,log',
            'description': 'Fichiers de configuration et logs'
        }
    }
    
    all_results = {}
    
    for base_url in base_urls:
        print(f"\n🌐 === Scan de {base_url} ===")
        all_results[base_url] = {}
        
        for scan_type, config in scan_types.items():
            print(f"\n🔍 {config['name']}: {config['description']}...")
            
            try:
                # Construction de la commande gobuster avec configuration optimisée
                gobuster_cmd = [
                    "gobuster", "dir",
                    "-u", base_url,
                    "-w", selected_wordlist,
                    "-t", "10",                # 10 threads (standard Gobuster)
                    "--timeout", "10s",        # 10s timeout (standard)
                    "-k",                      # Ignorer les certificats SSL
                    "--no-error",              # Pas d'erreurs dans la sortie
                    "--wildcard",              # Détecter les wildcards
                    "-s", "200,204,301,302,307,308,401,403,405,500"  # Status codes intéressants
                ]
                
                # Ajouter les extensions si c'est un scan de fichiers
                if config['extensions']:
                    gobuster_cmd.extend(["-x", config['extensions']])
                
                print(f"🚀 Commande: {' '.join(gobuster_cmd)}")
                
                gobuster_result = subprocess.run(
                    gobuster_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=600  # 10 minutes max par scan
                )
                
                output = gobuster_result.stdout
                errors = gobuster_result.stderr
                
                # Analyser les résultats - Parser le format Gobuster standard
                found_items = []
                status_codes = {}
                
                if output:
                    import re
                    lines = output.strip().split('\n')
                    for line in lines:
                        # Format Gobuster: /path (Status: 200) [Size: 1234] [--> redirect]
                        if '(Status:' in line and (line.startswith('/') or line.startswith('.')):
                            # Extraire les informations
                            match = re.match(r'^([^\s]+)\s+\(Status:\s+(\d+)\)\s+\[Size:\s+(\d+)\](?:\s+\[-->\s+([^\]]+)\])?', line.strip())
                            if match:
                                path, status, size, redirect = match.groups()
                                
                                # Compter les codes de statut
                                status_codes[status] = status_codes.get(status, 0) + 1
                                
                                found_items.append({
                                    'path': path,
                                    'status': status,
                                    'size': size,
                                    'redirect': redirect,
                                    'full_line': line.strip()
                                })
                            else:
                                # Format de fallback pour les lignes non-standard
                                if any(code in line for code in ['200', '301', '302', '401', '403', '405', '500']):
                                    found_items.append({
                                        'path': 'Unknown',
                                        'status': 'unknown',
                                        'size': '0',
                                        'redirect': None,
                                        'full_line': line.strip()
                                    })
                
                if gobuster_result.returncode == 0:
                    status = f"✅ Terminé ({len(found_items)} éléments trouvés)"
                else:
                    status = f"⚠️ Terminé avec erreurs (code {gobuster_result.returncode})"
                
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': status,
                    'found_items': found_items,
                    'status_codes': status_codes,
                    'output': output,
                    'errors': errors,
                    'returncode': gobuster_result.returncode
                }
                
                print(f"   {status}")
                if status_codes:
                    status_summary = ", ".join([f"{code}: {count}" for code, count in sorted(status_codes.items())])
                    print(f"   📊 Codes de statut: {status_summary}")
                
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Timeout pour {scan_type}")
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': '⏰ Timeout (> 10 min)',
                    'found_items': [],
                    'status_codes': {},
                    'output': 'Scan interrompu par timeout',
                    'errors': '',
                    'returncode': -1
                }
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                all_results[base_url][scan_type] = {
                    'config': config,
                    'status': f'❌ Erreur: {e}',
                    'found_items': [],
                    'status_codes': {},
                    'output': str(e),
                    'errors': '',
                    'returncode': -3
                }

    # Générer le rapport HTML avec le style graphique actuel
    try:
        total_items = sum(len(scan_result['found_items']) 
                         for url_results in all_results.values() 
                         for scan_result in url_results.values())
        
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Gobuster Complet - {target}</title>
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
        .gobuster-output {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 13px; white-space: pre-wrap; margin: 15px 0; }}
        .found-item {{ background-color: #f8f9fa; padding: 8px 12px; margin: 5px 0; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 13px; }}
        .item-critical {{ border-left: 3px solid #dc3545; background-color: #f8d7da; }}
        .item-interesting {{ border-left: 3px solid #ffc107; background-color: #fff3cd; }}
        .item-success {{ border-left: 3px solid #28a745; background-color: #d4edda; }}
        .item-redirect {{ border-left: 3px solid #17a2b8; background-color: #d1ecf1; }}
        .item-forbidden {{ border-left: 3px solid #fd7e14; background-color: #fde8d7; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .scan-overview {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .status-badge {{ padding: 3px 8px; border-radius: 3px; color: white; font-size: 11px; font-weight: bold; margin-right: 8px; }}
        .status-200 {{ background-color: #28a745; }}
        .status-301, .status-302, .status-307, .status-308 {{ background-color: #17a2b8; }}
        .status-401 {{ background-color: #fd7e14; }}
        .status-403 {{ background-color: #ffc107; color: black; }}
        .status-405 {{ background-color: #e83e8c; }}
        .status-500 {{ background-color: #dc3545; }}
        .path-text {{ font-weight: bold; color: #2c3e50; }}
        .size-text {{ color: #6c757d; font-size: 11px; }}
        .redirect-text {{ color: #17a2b8; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Rapport Gobuster Complet - Directory & File Bruteforcing</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Gobuster v3.6 Directory & File Enumeration<br>
            <strong>🔍 URLs testées:</strong> {len(base_urls)}<br>
            <strong>🎯 Types de scan:</strong> {len(scan_types)} (Répertoires, Fichiers, Admin, Config)<br>
            <strong>🐳 Environnement:</strong> Docker Container
        </div>
        
        <div class="scan-overview">
            <strong>📋 Wordlist utilisée:</strong> {wordlist_info}<br>
            <strong>📂 Chemin:</strong> {selected_wordlist}<br>
            <strong>🎯 Stratégie:</strong> Scan multi-passes pour découverte complète<br>
            <strong>⚡ Configuration:</strong> 10 threads, timeout 10s (standard Gobuster)
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{total_items}</h3>
                <p>Éléments trouvés</p>
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

            # Compter les types d'éléments trouvés
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

            if total_items > 0:
                f.write(f'<div class="success"><strong>✅ {total_items} éléments découverts</strong> via scan multi-passes Gobuster</div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucun élément découvert</strong>. Le site pourrait être bien sécurisé ou avoir une structure non-standard.</div>')

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
                <p><strong>Éléments trouvés:</strong> {len(scan_result['found_items'])}</p>""")
                    
                    if scan_result['status_codes']:
                        f.write('<p><strong>Codes de statut:</strong> ')
                        for code, count in sorted(scan_result['status_codes'].items()):
                            f.write(f'<span class="status-badge status-{code}">{code}: {count}</span> ')
                        f.write('</p>')
                    
                    # Afficher la sortie brute de Gobuster (première partie)
                    if scan_result['output'] and scan_result['returncode'] == 0:
                        f.write('<h4>📋 Sortie Gobuster:</h4>')
                        # Afficher les premiers résultats dans le style terminal
                        output_preview = '\n'.join(scan_result['output'].split('\n')[:10])
                        f.write(f'<div class="gobuster-output">{output_preview}</div>')
                    
                    # Classer les éléments trouvés par type
                    critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'wp-admin']
                    interesting_keywords = ['wp-content', 'wp-includes', 'xmlrpc', 'upload', 'api', 'panel', 'dashboard']
                    
                    critical_items = []
                    interesting_items = []
                    forbidden_items = []
                    redirect_items = []
                    success_items = []
                    
                    for item in scan_result['found_items']:
                        path_lower = item['path'].lower()
                        status = item['status']
                        
                        if any(keyword in path_lower for keyword in critical_keywords):
                            critical_items.append(item)
                        elif any(keyword in path_lower for keyword in interesting_keywords):
                            interesting_items.append(item)
                        elif status == '403':
                            forbidden_items.append(item)
                        elif status in ['301', '302', '307', '308']:
                            redirect_items.append(item)
                        elif status in ['200', '204']:
                            success_items.append(item)
                    
                    # Afficher les éléments critiques
                    if critical_items:
                        f.write('<h4>🚨 Éléments Critiques</h4>')
                        for item in critical_items:
                            redirect_info = f" [--> {item['redirect']}]" if item['redirect'] else ""
                            f.write(f'''<div class="found-item item-critical">
                                <span class="status-badge status-{item['status']}">{item['status']}</span>
                                <span class="path-text">{item['path']}</span>
                                <span class="size-text">[Size: {item['size']}]</span>
                                <span class="redirect-text">{redirect_info}</span>
                            </div>''')
                    
                    # Afficher les éléments intéressants
                    if interesting_items:
                        f.write('<h4>⚠️ Éléments Intéressants</h4>')
                        for item in interesting_items:
                            redirect_info = f" [--> {item['redirect']}]" if item['redirect'] else ""
                            f.write(f'''<div class="found-item item-interesting">
                                <span class="status-badge status-{item['status']}">{item['status']}</span>
                                <span class="path-text">{item['path']}</span>
                                <span class="size-text">[Size: {item['size']}]</span>
                                <span class="redirect-text">{redirect_info}</span>
                            </div>''')
                    
                    # Afficher les accès interdits
                    if forbidden_items:
                        f.write('<h4>🚫 Accès Interdits (403)</h4>')
                        for item in forbidden_items:
                            f.write(f'''<div class="found-item item-forbidden">
                                <span class="status-badge status-{item['status']}">{item['status']}</span>
                                <span class="path-text">{item['path']}</span>
                                <span class="size-text">[Size: {item['size']}]</span>
                            </div>''')
                    
                    # Afficher les redirections
                    if redirect_items:
                        f.write('<h4>🔄 Redirections</h4>')
                        for item in redirect_items:
                            redirect_info = f" [--> {item['redirect']}]" if item['redirect'] else ""
                            f.write(f'''<div class="found-item item-redirect">
                                <span class="status-badge status-{item['status']}">{item['status']}</span>
                                <span class="path-text">{item['path']}</span>
                                <span class="size-text">[Size: {item['size']}]</span>
                                <span class="redirect-text">{redirect_info}</span>
                            </div>''')
                    
                    # Afficher les succès
                    if success_items:
                        f.write('<h4>✅ Accès Réussis (200)</h4>')
                        for item in success_items:
                            f.write(f'''<div class="found-item item-success">
                                <span class="status-badge status-{item['status']}">{item['status']}</span>
                                <span class="path-text">{item['path']}</span>
                                <span class="size-text">[Size: {item['size']}]</span>
                            </div>''')
                    
                    if scan_result['errors']:
                        f.write(f'<details><summary>Erreurs/Debug</summary><div class="gobuster-output">{scan_result["errors"]}</div></details>')
                    
                    f.write('</div>')
                
                f.write('</div>')

            f.write(f"""
        <h2>🛡️ Analyse de Sécurité</h2>
        <div class="error">
            <h3>🚨 Priorités de Sécurisation</h3>
            <ul>
                <li><strong>wp-admin (Status 301):</strong> Interface d'administration WordPress - sécuriser l'accès</li>
                <li><strong>xmlrpc.php (Status 405):</strong> Endpoint XML-RPC - désactiver si non utilisé</li>
                <li><strong>Fichiers .hta* (Status 403):</strong> Fichiers de configuration Apache - vérifier la protection</li>
                <li><strong>wp-content/wp-includes:</strong> Répertoires WordPress - contrôler l'indexation</li>
            </ul>
        </div>
        
        <div class="warning">
            <h3>⚠️ Recommandations WordPress</h3>
            <ul>
                <li><strong>Sécuriser wp-admin:</strong> Restriction par IP, authentification forte</li>
                <li><strong>Désactiver XML-RPC:</strong> Prévenir les attaques de brute force</li>
                <li><strong>Masquer la version:</strong> Supprimer les meta generator</li>
                <li><strong>Fichiers sensibles:</strong> Protéger wp-config.php et .htaccess</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🎯 Méthodologie Gobuster Multi-passes</h3>
            <p>Ce scan utilise <strong>4 passes spécialisées</strong> :</p>
            <ul>
                <li><strong>Pass 1 - Répertoires:</strong> Structure de base et dossiers</li>
                <li><strong>Pass 2 - Fichiers Courants:</strong> Pages web et scripts standards</li>
                <li><strong>Pass 3 - Administration:</strong> Interfaces d'admin et panneaux</li>
                <li><strong>Pass 4 - Configuration:</strong> Fichiers de config et logs</li>
            </ul>
        </div>
        
        <div class="success">
            <h3>🔍 Interprétation des Codes de Statut</h3>
            <ul>
                <li><strong>200 (OK):</strong> Contenu accessible - examiner en priorité</li>
                <li><strong>301/302 (Redirect):</strong> Redirection - suivre la destination</li>
                <li><strong>401 (Unauthorized):</strong> Authentification requise</li>
                <li><strong>403 (Forbidden):</strong> Accès interdit mais fichier existant</li>
                <li><strong>405 (Method Not Allowed):</strong> Méthode non autorisée - tester POST/PUT</li>
                <li><strong>500 (Internal Error):</strong> Erreur serveur - peut révéler des infos</li>
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