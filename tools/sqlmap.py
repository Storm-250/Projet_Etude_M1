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
    
    print(f"🔍 Scan Gobuster en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Wordlists à essayer (par ordre de préférence)
    wordlists = [
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
        "/usr/share/seclists/Discovery/Web-Content/common.txt",
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
        selected_wordlist = "basic_wordlist.txt"
        basic_dirs = [
            "admin", "administrator", "login", "panel", "dashboard", "control",
            "wp-admin", "phpMyAdmin", "phpmyadmin", "mysql", "sql",
            "backup", "backups", "bak", "old", "test", "temp", "tmp",
            "uploads", "upload", "files", "file", "download", "downloads",
            "images", "img", "pics", "pictures", "assets", "static",
            "js", "css", "scripts", "style", "styles", "javascript",
            "api", "rest", "webservice", "service", "services",
            "config", "configuration", "settings", "setup", "install",
            "private", "secret", "hidden", "internal", "secure",
            "logs", "log", "debug", "error", "errors", "stats"
        ]
        
        with open(selected_wordlist, "w") as f:
            f.write("\n".join(basic_dirs))
        print(f"📝 Wordlist créée: {selected_wordlist}")

    # URLs à tester
    base_urls = [f"http://{target}", f"https://{target}"]
    gobuster_results = {}
    
    for base_url in base_urls:
        print(f"🔍 Test de {base_url}...")
        
        try:
            # Gobuster dir avec options optimisées
            gobuster_cmd = [
                "gobuster", "dir",
                "-u", base_url,
                "-w", selected_wordlist,
                "-t", "20",              # 20 threads
                "-x", "php,html,txt,js,css,xml,json",  # Extensions
                "--timeout", "10s",      # Timeout par requête
                "--quiet",               # Mode silencieux
                "--no-error",            # Pas d'erreurs dans la sortie
                "-k"                     # Ignorer les certificats SSL
            ]
            
            print(f"🚀 Commande: {' '.join(gobuster_cmd)}")
            
            gobuster_result = subprocess.run(
                gobuster_cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minutes max
            )
            
            output = gobuster_result.stdout
            errors = gobuster_result.stderr
            
            # Analyser les résultats
            found_paths = []
            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('==='):
                        found_paths.append(line.strip())
            
            if gobuster_result.returncode == 0:
                status = f"✅ Terminé ({len(found_paths)} chemins trouvés)"
            else:
                status = f"⚠️ Terminé avec erreurs (code {gobuster_result.returncode})"
            
            gobuster_results[base_url] = {
                'status': status,
                'found_paths': found_paths,
                'output': output,
                'errors': errors,
                'returncode': gobuster_result.returncode
            }
            
            print(f"   {status}")
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout pour {base_url}")
            gobuster_results[base_url] = {
                'status': '⏰ Timeout',
                'found_paths': [],
                'output': 'Scan interrompu par timeout',
                'errors': '',
                'returncode': -1
            }
        except FileNotFoundError:
            print(f"   ❌ Gobuster non trouvé")
            gobuster_results[base_url] = {
                'status': '❌ Outil manquant',
                'found_paths': [],
                'output': 'Gobuster non installé',
                'errors': '',
                'returncode': -2
            }
            break  # Pas la peine de continuer
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            gobuster_results[base_url] = {
                'status': f'❌ Erreur: {e}',
                'found_paths': [],
                'output': str(e),
                'errors': '',
                'returncode': -3
            }

    # Générer le rapport HTML
    try:
        total_paths = sum(len(r['found_paths']) for r in gobuster_results.values())
        
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Gobuster - {target}</title>
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
        .path {{ background-color: white; padding: 8px; margin: 5px 0; border-left: 3px solid #17a2b8; border-radius: 0 3px 3px 0; font-family: monospace; }}
        .path-interesting {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .path-sensitive {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .critical-paths {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Rapport Gobuster - Énumération de Répertoires</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Gobuster Directory/File Enumeration<br>
            <strong>📋 Wordlist:</strong> {os.path.basename(selected_wordlist)}<br>
            <strong>🔍 URLs testées:</strong> {len(base_urls)}
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{total_paths}</h3>
                <p>Chemins trouvés</p>
            </div>
            <div class="stat">
                <h3>{len([r for r in gobuster_results.values() if r['returncode'] == 0])}</h3>
                <p>Scans réussis</p>
            </div>
        </div>""")

            if total_paths > 0:
                f.write(f'<div class="success"><strong>✅ {total_paths} répertoires/fichiers découverts</strong></div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucun répertoire découvert</strong> avec la wordlist utilisée.</div>')

            # Identifier les chemins critiques
            critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'debug', 'phpMyAdmin']
            interesting_keywords = ['upload', 'file', 'download', 'api', 'panel', 'dashboard', 'test']
            
            all_critical_paths = []
            all_interesting_paths = []
            
            for url, result in gobuster_results.items():
                for path in result['found_paths']:
                    if any(keyword in path.lower() for keyword in critical_keywords):
                        all_critical_paths.append(f"{url}{path}")
                    elif any(keyword in path.lower() for keyword in interesting_keywords):
                        all_interesting_paths.append(f"{url}{path}")

            if all_critical_paths:
                f.write('<div class="critical-paths">')
                f.write('<h3>🚨 Chemins Critiques Détectés</h3>')
                f.write('<p>Ces chemins peuvent contenir des informations sensibles ou des interfaces d\'administration :</p>')
                for path in all_critical_paths:
                    f.write(f'<div class="path path-sensitive">🔴 {path}</div>')
                f.write('</div>')

            f.write('<h2>📊 Résultats par URL</h2>')
            
            for url, result in gobuster_results.items():
                f.write(f"""
        <div class="url-scan">
            <h3>🌐 URL: {url}</h3>
            <p><strong>Statut:</strong> {result['status']}</p>
            <p><strong>Chemins trouvés:</strong> {len(result['found_paths'])}</p>
            
            {f'<h4>📂 Répertoires et fichiers découverts:</h4>' if result['found_paths'] else ''}""")
                
                for path in result['found_paths']:
                    css_class = "path"
                    if any(keyword in path.lower() for keyword in critical_keywords):
                        css_class += " path-sensitive"
                    elif any(keyword in path.lower() for keyword in interesting_keywords):
                        css_class += " path-interesting"
                    
                    f.write(f'<div class="{css_class}">{path}</div>')
                
                if result['errors']:
                    f.write(f'<details><summary>Erreurs</summary><pre>{result["errors"]}</pre></details>')
                
                f.write('</div>')

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Recommandées</h3>
            <ul>
                <li><strong>Interfaces d'admin:</strong> Protégez les panneaux d'administration par IP ou VPN</li>
                <li><strong>Fichiers sensibles:</strong> Déplacez ou supprimez les fichiers de configuration exposés</li>
                <li><strong>Répertoires de backup:</strong> Sécurisez ou supprimez les répertoires de sauvegarde</li>
                <li><strong>Indexation:</strong> Désactivez l'indexation des répertoires</li>
                <li><strong>Authentification:</strong> Protégez les zones sensibles par authentification</li>
                <li><strong>Permissions:</strong> Vérifiez les permissions des fichiers et dossiers</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Note importante:</strong> Ce scan utilise une wordlist limitée. 
            Des répertoires supplémentaires pourraient exister avec des wordlists plus complètes.
        </div>
        
        <div class="info">
            <h3>🔍 Prochaines étapes recommandées</h3>
            <ul>
                <li>Examiner manuellement chaque répertoire découvert</li>
                <li>Tester l'accès aux interfaces d'administration</li>
                <li>Vérifier la présence de fichiers de configuration</li>
                <li>Analyser les répertoires d'upload pour des vulnérabilités</li>
                <li>Effectuer un scan avec des wordlists plus complètes</li>
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
    if selected_wordlist == "basic_wordlist.txt":
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