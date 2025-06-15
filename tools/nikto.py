import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: nikto.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"nikto_{date}.html")
    
    print(f"🔍 Scan Nikto en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Exécuter Nikto
    try:
        nikto_cmd = ["nikto", "-h", target, "-Format", "txt"]
        print(f"🚀 Commande: {' '.join(nikto_cmd)}")
        
        nikto_result = subprocess.run(
            nikto_cmd, 
            capture_output=True, 
            text=True, 
            timeout=600  # 10 minutes max
        )
        
        nikto_output = nikto_result.stdout
        nikto_errors = nikto_result.stderr
        
        if nikto_result.returncode != 0:
            print(f"⚠️ Nikto terminé avec le code {nikto_result.returncode}")
            if nikto_errors:
                print(f"Stderr: {nikto_errors}")
        
        # Si pas de sortie, utiliser les erreurs
        if not nikto_output.strip() and nikto_errors:
            nikto_output = f"Erreurs Nikto:\n{nikto_errors}"
        elif not nikto_output.strip():
            nikto_output = "Aucun résultat retourné par Nikto"
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: Le scan Nikto a pris trop de temps")
        nikto_output = "Scan interrompu par timeout (10 minutes)"
    except FileNotFoundError:
        print("❌ Erreur: nikto n'est pas installé")
        nikto_output = "Erreur: nikto non trouvé"
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")
        nikto_output = f"Erreur: {e}"

    # Générer le rapport HTML
    try:
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Nikto - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
        .vulnerability {{ background-color: #f8d7da; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; border-radius: 0 5px 5px 0; }}
        .info-item {{ background-color: #d1ecf1; padding: 10px; margin: 10px 0; border-left: 4px solid #17a2b8; border-radius: 0 5px 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐛 Rapport Nikto - Analyse de Vulnérabilités Web</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Outil:</strong> Nikto Web Scanner
        </div>
        
        <h2>📊 Résultats du Scan</h2>""")

            # Analyser et formater les résultats
            if "Erreur:" in nikto_output or "Scan interrompu" in nikto_output:
                f.write(f'<div class="error"><strong>Erreur lors du scan:</strong><br><pre>{nikto_output}</pre></div>')
            else:
                # Essayer de parser les résultats Nikto
                lines = nikto_output.split('\n')
                vulnerabilities = []
                info_items = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Nikto'):
                        if any(keyword in line.lower() for keyword in ['vulnerable', 'security', 'risk', 'exposure', 'exploit']):
                            vulnerabilities.append(line)
                        elif line and len(line) > 10:
                            info_items.append(line)
                
                if vulnerabilities:
                    f.write('<h3>🚨 Vulnérabilités Détectées</h3>')
                    for vuln in vulnerabilities:
                        f.write(f'<div class="vulnerability">{vuln}</div>')
                
                if info_items:
                    f.write('<h3>ℹ️ Informations du Serveur</h3>')
                    for item in info_items[:10]:  # Limiter à 10 items
                        f.write(f'<div class="info-item">{item}</div>')
                
                f.write('<h3>📄 Sortie Complète</h3>')
                f.write(f'<pre>{nikto_output}</pre>')

            f.write("""
        <div class="info">
            <h3>💡 Recommandations</h3>
            <ul>
                <li>Vérifiez et corrigez les vulnérabilités identifiées</li>
                <li>Mettez à jour les composants web obsolètes</li>
                <li>Configurez correctement les en-têtes de sécurité</li>
                <li>Effectuez des tests complémentaires avec d'autres outils</li>
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