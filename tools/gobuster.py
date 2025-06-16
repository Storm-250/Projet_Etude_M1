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
    gobuster_results = {}
    
    for base_url in base_urls:
        print(f"🔍 Test de {base_url}...")
        
        try:
            # Gobuster dir avec options optimisées pour common.txt
            gobuster_cmd = [
                "gobuster", "dir",
                "-u", base_url,
                "-w", selected_wordlist,
                "-t", "30",              # 30 threads (optimisé pour common.txt)
                "-x", "php,html,txt,js,css,xml,json,bak,old,tmp",  # Extensions
                "--timeout", "15s",      # Timeout augmenté
                "--quiet",               # Mode silencieux
                "--no-error",            # Pas d'erreurs dans la sortie
                "-k",                    # Ignorer les certificats SSL
                "--wildcard"             # Détecter les wildcards
            ]
            
            print(f"🚀 Commande: {' '.join(gobuster_cmd)}")
            
            gobuster_result = subprocess.run(
                gobuster_cmd, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10 minutes max pour common.txt
            )
            
            output = gobuster_result.stdout
            errors = gobuster_result.stderr
            
            # Analyser les résultats
            found_paths = []
            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('===') and not line.startswith('Gobuster'):
                        # Format gobuster: /path (Status: 200) [Size: 1234]
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
                'status': '⏰ Timeout (> 10 min)',
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
        .path {{ background-color: white; padding: 10px; margin: 5px 0; border-left: 3px solid #17a2b8; border-radius: 0 3px 3px 0; font-family: monospace; font-size: 13px; }}
        .path-interesting {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .path-sensitive {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .path-success {{ border-left-color: #28a745; background-color: #d4edda; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .critical-paths {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .wordlist-info {{ background-color: #e7f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 15px 0; border-radius: 0 3px 3px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Rapport Gobuster - Énumération de Répertoires</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Gobuster Directory/File Enumeration<br>
            <strong>🔍 URLs testées:</strong> {len(base_urls)}
        </div>
        
        <div class="wordlist-info">
            <strong>📋 Wordlist utilisée:</strong> {wordlist_info}<br>
            <strong>🎯 Stratégie:</strong> Scan optimisé avec common.txt local pour une détection efficace des répertoires courants
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
                f.write(f'<div class="success"><strong>✅ {total_paths} répertoires/fichiers découverts</strong> avec common.txt local</div>')
            else:
                f.write('<div class="warning"><strong>⚠️ Aucun répertoire découvert</strong> avec common.txt local. Le site pourrait avoir une structure non-standard ou être bien sécurisé.</div>')

            # Identifier les chemins critiques (optimisé pour common.txt)
            critical_keywords = ['admin', 'login', 'password', 'config', 'backup', 'private', 'secret', 'debug', 'phpmyadmin', 'mysql']
            interesting_keywords = ['upload', 'file', 'download', 'api', 'panel', 'dashboard', 'test', 'temp', 'dev']
            success_keywords = ['robots.txt', 'sitemap.xml', '.htaccess', 'phpinfo', 'info.php']
            
            all_critical_paths = []
            all_interesting_paths = []
            all_success_paths = []
            
            for url, result in gobuster_results.items():
                for path in result['found_paths']:
                    path_lower = path.lower()
                    if any(keyword in path_lower for keyword in critical_keywords):
                        all_critical_paths.append(f"{url}{path}")
                    elif any(keyword in path_lower for keyword in interesting_keywords):
                        all_interesting_paths.append(f"{url}{path}")
                    elif any(keyword in path_lower for keyword in success_keywords):
                        all_success_paths.append(f"{url}{path}")

            if all_critical_paths:
                f.write('<div class="critical-paths">')
                f.write('<h3>🚨 Chemins Critiques Détectés</h3>')
                f.write('<p>Ces chemins peuvent contenir des informations sensibles ou des interfaces d\'administration :</p>')
                for path in all_critical_paths:
                    f.write(f'<div class="path path-sensitive">🔴 {path}</div>')
                f.write('</div>')

            if all_interesting_paths:
                f.write('<div class="warning">')
                f.write('<h3>⚠️ Chemins Intéressants</h3>')
                f.write('<p>Ces chemins méritent une investigation manuelle :</p>')
                for path in all_interesting_paths:
                    f.write(f'<div class="path path-interesting">🟡 {path}</div>')
                f.write('</div>')

            if all_success_paths:
                f.write('<div class="success">')
                f.write('<h3>✅ Fichiers d\'Information Standard</h3>')
                f.write('<p>Fichiers informatifs découverts :</p>')
                for path in all_success_paths:
                    f.write(f'<div class="path path-success">🟢 {path}</div>')
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
                    path_lower = path.lower()
                    
                    if any(keyword in path_lower for keyword in critical_keywords):
                        css_class += " path-sensitive"
                    elif any(keyword in path_lower for keyword in interesting_keywords):
                        css_class += " path-interesting"
                    elif any(keyword in path_lower for keyword in success_keywords):
                        css_class += " path-success"
                    
                    f.write(f'<div class="{css_class}">{path}</div>')
                
                if result['errors']:
                    f.write(f'<details><summary>Erreurs</summary><pre>{result["errors"]}</pre></details>')
                
                f.write('</div>')

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Recommandées pour common.txt</h3>
            <ul>
                <li><strong>Interfaces d'admin:</strong> Protégez les panneaux d'administration par IP, VPN ou authentification forte</li>
                <li><strong>Fichiers sensibles:</strong> Déplacez ou supprimez les fichiers de configuration exposés</li>
                <li><strong>Répertoires de backup:</strong> Sécurisez ou supprimez les répertoires de sauvegarde</li>
                <li><strong>Indexation:</strong> Désactivez l'indexation des répertoires avec .htaccess ou configuration serveur</li>
                <li><strong>Authentification:</strong> Protégez les zones sensibles par authentification</li>
                <li><strong>Permissions:</strong> Vérifiez les permissions des fichiers et dossiers découverts</li>
                <li><strong>Fichiers info:</strong> Supprimez phpinfo.php et autres fichiers d'information en production</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>📋 À propos de common.txt</h3>
            <p><strong>common.txt</strong> contient environ 4600 répertoires et fichiers couramment trouvés sur les serveurs web. 
            Cette wordlist est optimisée pour découvrir rapidement les éléments les plus fréquents sans surcharger le serveur cible.</p>
            <ul>
                <li><strong>Avantages:</strong> Rapide, efficace, couvre 80% des cas courants</li>
                <li><strong>Couverture:</strong> Interfaces admin, fichiers de config, répertoires standards</li>
                <li><strong>Temps:</strong> Scan généralement terminé en quelques minutes</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Note importante:</strong> Ce scan utilise common.txt local (~4600 entrées). 
            Pour une énumération plus exhaustive, considérez l'utilisation de wordlists plus complètes.
        </div>
        
        <div class="info">
            <h3>🔍 Prochaines étapes recommandées</h3>
            <ul>
                <li>Examiner manuellement chaque répertoire découvert dans un navigateur</li>
                <li>Tester l'accès aux interfaces d'administration avec des credentials par défaut</li>
                <li>Vérifier la présence de fichiers de sauvegarde dans les répertoires découverts</li>
                <li>Analyser les répertoires d'upload pour des vulnérabilités de téléchargement</li>
                <li>Si peu de résultats : essayer une wordlist plus complète ou spécialisée</li>
                <li>Combiner avec d'autres techniques : scan de ports, analyse des technologies</li>
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