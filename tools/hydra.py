import sys
import subprocess
import os
import zipfile
from datetime import datetime
from encrypt import encrypt_file

def extract_pass_zip():
    """
    Décompresse automatiquement pass.zip depuis le dossier tools
    """
    pass_zip_path = os.path.join("tools", "pass.zip")
    
    if os.path.exists(pass_zip_path):
        print(f"📦 Décompression de {pass_zip_path}...")
        try:
            with zipfile.ZipFile(pass_zip_path, 'r') as zip_ref:
                # Extraire dans le répertoire courant
                extracted_files = zip_ref.namelist()
                zip_ref.extractall('.')
                
                print(f"✅ Fichiers extraits: {', '.join(extracted_files)}")
                
                # Vérifier que les fichiers ont bien été extraits
                for filename in extracted_files:
                    if os.path.exists(filename):
                        size = os.path.getsize(filename)
                        print(f"   • {filename} ({size} bytes)")
                    else:
                        print(f"   ❌ {filename} non extrait")
                
                return True
                
        except zipfile.BadZipFile:
            print(f"❌ Fichier zip corrompu: {pass_zip_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la décompression: {e}")
    else:
        print(f"⚠️ {pass_zip_path} non trouvé")
    
    return False

def ensure_wordlist_files():
    """
    S'assure que les fichiers de listes de mots de passe existent
    """
    # D'abord essayer de décompresser pass.zip
    extract_pass_zip()
    
    # Définir les fichiers par défaut
    default_users = ["admin", "root", "user", "test", "guest", "administrator"]
    default_passwords = ["admin", "password", "123456", "root", "test", "guest", ""]
    
    # Vérifier/créer users.txt
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f:
            f.write("\n".join(default_users))
        print(f"📝 Fichier users.txt créé avec les utilisateurs par défaut")
    
    # Vérifier/créer passwords.txt ou pass.txt
    password_files = ["passwords.txt", "pass.txt"]
    password_file_exists = any(os.path.exists(pf) for pf in password_files)
    
    if not password_file_exists:
        with open("passwords.txt", "w") as f:
            f.write("\n".join(default_passwords))
        print(f"📝 Fichier passwords.txt créé avec les mots de passe par défaut")

def get_wordlist_files():
    """
    Détermine quels fichiers de listes utiliser
    """
    users_file = "users.txt"
    
    # Priorité à pass.txt puis passwords.txt
    if os.path.exists("pass.txt"):
        passwords_file = "pass.txt"
    elif os.path.exists("passwords.txt"):
        passwords_file = "passwords.txt"
    else:
        passwords_file = "passwords.txt"  # Sera créé par ensure_wordlist_files
    
    return users_file, passwords_file

def main():
    if len(sys.argv) < 2:
        print("Usage: hydra.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"hydra_{date}.html")
    
    print(f"🔍 Scan Hydra en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # **ÉTAPE CRUCIALE : Décompresser pass.zip automatiquement**
    ensure_wordlist_files()
    
    # Déterminer quels fichiers utiliser
    users_file, passwords_file = get_wordlist_files()
    
    print(f"📋 Utilisation de {users_file} et {passwords_file}")
    
    # Vérifier que les fichiers existent maintenant
    if not os.path.exists(users_file):
        print(f"❌ Fichier {users_file} manquant")
        sys.exit(1)
    
    if not os.path.exists(passwords_file):
        print(f"❌ Fichier {passwords_file} manquant")
        sys.exit(1)
    
    # Afficher les statistiques des fichiers
    users_count = len([line for line in open(users_file, 'r') if line.strip()])
    passwords_count = len([line for line in open(passwords_file, 'r') if line.strip()])
    print(f"📊 {users_count} utilisateurs, {passwords_count} mots de passe")

    # Services à tester
    services_to_test = ["ssh", "ftp", "telnet", "http-get", "https-get"]
    hydra_results = {}

    for service in services_to_test:
        print(f"🔑 Test du service {service}...")
        
        try:
            # Adapter la commande selon le service
            if service in ["http-get", "https-get"]:
                hydra_cmd = ["hydra", "-L", users_file, "-P", passwords_file, 
                           f"{target}", service, "-f", "-t", "4"]
            else:
                hydra_cmd = ["hydra", "-L", users_file, "-P", passwords_file, 
                           f"{service}://{target}", "-f", "-t", "4"]
            
            print(f"🚀 Commande: {' '.join(hydra_cmd)}")
            
            hydra_result = subprocess.run(
                hydra_cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minutes max par service
            )
            
            output = hydra_result.stdout
            errors = hydra_result.stderr
            
            if hydra_result.returncode == 0:
                status = "✅ Succès"
            elif hydra_result.returncode == 1:
                status = "⚠️ Aucun accès trouvé"
            else:
                status = f"❌ Erreur (code {hydra_result.returncode})"
            
            hydra_results[service] = {
                'status': status,
                'output': output,
                'errors': errors,
                'returncode': hydra_result.returncode
            }
            
            print(f"   {status} pour {service}")
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout pour {service}")
            hydra_results[service] = {
                'status': '⏰ Timeout',
                'output': 'Scan interrompu par timeout',
                'errors': '',
                'returncode': -1
            }
        except FileNotFoundError:
            print(f"   ❌ Hydra non trouvé")
            hydra_results[service] = {
                'status': '❌ Outil manquant',
                'output': 'Hydra non installé',
                'errors': '',
                'returncode': -2
            }
            break
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            hydra_results[service] = {
                'status': f'❌ Erreur: {e}',
                'output': str(e),
                'errors': '',
                'returncode': -3
            }

    # Générer le rapport HTML
    try:
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Hydra - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .service {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #6c757d; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
        .credentials {{ background-color: #d1ecf1; padding: 10px; margin: 10px 0; border-left: 4px solid #17a2b8; border-radius: 0 5px 5px 0; font-family: monospace; }}
        .status {{ font-weight: bold; padding: 3px 8px; border-radius: 3px; }}
        .status-success {{ background-color: #28a745; color: white; }}
        .status-warning {{ background-color: #ffc107; color: black; }}
        .status-error {{ background-color: #dc3545; color: white; }}
        .status-timeout {{ background-color: #6c757d; color: white; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔑 Rapport Hydra - Test de Force Brute</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Hydra Password Cracker<br>
            <strong>📋 Services testés:</strong> {len(services_to_test)}<br>
            <strong>📝 Fichiers utilisés:</strong> {users_file} ({users_count} utilisateurs), {passwords_file} ({passwords_count} mots de passe)
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{len(services_to_test)}</h3>
                <p>Services testés</p>
            </div>
            <div class="stat">
                <h3>{users_count}</h3>
                <p>Utilisateurs</p>
            </div>
            <div class="stat">
                <h3>{passwords_count}</h3>
                <p>Mots de passe</p>
            </div>
        </div>""")

            # Compter les résultats
            success_count = sum(1 for r in hydra_results.values() if 'Succès' in r['status'])
            
            if success_count > 0:
                f.write(f'<div class="error"><strong>⚠️ ALERTE SÉCURITÉ:</strong> {success_count} service(s) avec des identifiants faibles détectés!</div>')
            else:
                f.write('<div class="success"><strong>✅ Aucun identifiant faible détecté</strong> sur les services testés.</div>')

            f.write('<h2>📊 Résultats par Service</h2>')
            
            for service, result in hydra_results.items():
                status_class = "status-error"
                if "Succès" in result['status']:
                    status_class = "status-success"
                elif "Aucun accès" in result['status']:
                    status_class = "status-warning"
                elif "Timeout" in result['status']:
                    status_class = "status-timeout"
                
                f.write(f"""
        <div class="service">
            <h3>🔌 Service: {service.upper()}</h3>
            <span class="status {status_class}">{result['status']}</span>
            
            {f'<div class="credentials"><strong>⚠️ IDENTIFIANTS TROUVÉS:</strong><br><pre>{result["output"]}</pre></div>' if "Succès" in result['status'] else ''}
            
            {f'<details><summary>Voir la sortie complète</summary><pre>{result["output"]}</pre></details>' if result['output'] and "Succès" not in result['status'] else ''}
            
            {f'<details><summary>Erreurs</summary><pre>{result["errors"]}</pre></details>' if result['errors'] else ''}
        </div>""")

            f.write("""
        <h2>🛡️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Recommandées</h3>
            <ul>
                <li><strong>Politique de mots de passe:</strong> Imposez des mots de passe complexes (12+ caractères, majuscules, minuscules, chiffres, symboles)</li>
                <li><strong>Authentification multi-facteurs:</strong> Activez le 2FA sur tous les services critiques</li>
                <li><strong>Limitation des tentatives:</strong> Configurez fail2ban ou des limites de connexion</li>
                <li><strong>Surveillance:</strong> Monitorez les tentatives de connexion suspectes dans les logs</li>
                <li><strong>Comptes par défaut:</strong> Désactivez ou renommez tous les comptes par défaut</li>
                <li><strong>Services exposés:</strong> Limitez l'exposition des services non nécessaires (firewall, VPN)</li>
                <li><strong>Mise à jour:</strong> Maintenez les services à jour pour corriger les vulnérabilités</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Note importante:</strong> Ce test utilise une liste de mots de passe courante. 
            Un attaquant réel pourrait utiliser des dictionnaires plus complets (millions d'entrées) et des techniques plus sophistiquées.
        </div>
        
        <div class="info">
            <h3>🔍 Méthodologie du Test</h3>
            <ul>
                <li><strong>Utilisateurs testés:</strong> Comptes communs et administrateurs</li>
                <li><strong>Mots de passe testés:</strong> Mots de passe faibles et par défaut</li>
                <li><strong>Services ciblés:</strong> SSH, FTP, Telnet, HTTP/HTTPS</li>
                <li><strong>Limitation:</strong> 4 threads pour éviter la surcharge du serveur</li>
                <li><strong>Timeout:</strong> 5 minutes maximum par service</li>
            </ul>
        </div>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport généré: {html_path}")
        
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