#!/usr/bin/env python3

import os
import json
from datetime import datetime

def check_encrypt_files():
    """Vérifier les fichiers nécessaires au chiffrement"""
    print("=== DIAGNOSTIC CHIFFREMENT ===")
    
    # Vérifier MDP.json
    if os.path.exists("MDP.json"):
        try:
            with open("MDP.json", "r") as f:
                data = json.load(f)
                password = data.get("password")
                print(f"✅ MDP.json existe, mot de passe: '{password}'")
        except Exception as e:
            print(f"❌ Erreur lecture MDP.json: {e}")
            return False
    else:
        print("❌ MDP.json manquant - création...")
        try:
            with open("MDP.json", "w") as f:
                json.dump({"password": "changeme"}, f)
            print("✅ MDP.json créé avec mot de passe par défaut")
        except Exception as e:
            print(f"❌ Impossible de créer MDP.json: {e}")
            return False
    
    # Vérifier salt.bin
    if os.path.exists("salt.bin"):
        size = os.path.getsize("salt.bin")
        print(f"✅ salt.bin existe ({size} bytes)")
    else:
        print("⚠️ salt.bin manquant (sera créé automatiquement)")
    
    return True

def test_encrypt_module():
    """Tester le module de chiffrement"""
    print("\n=== TEST MODULE ENCRYPT ===")
    
    try:
        from encrypt import encrypt_file, decrypt_file, load_password
        print("✅ Module encrypt importé")
        
        # Test du mot de passe
        password = load_password()
        print(f"✅ Mot de passe chargé: '{password}'")
        
        return True
    except ImportError as e:
        print(f"❌ Impossible d'importer encrypt: {e}")
    except Exception as e:
        print(f"❌ Erreur module encrypt: {e}")
    
    return False

def encrypt_existing_file():
    """Chiffrer le fichier HTML existant"""
    print("\n=== CHIFFREMENT FICHIER EXISTANT ===")
    
    # Chercher le fichier HTML non chiffré
    rapports_dir = "rapports"
    html_files = []
    
    if os.path.exists(rapports_dir):
        for file in os.listdir(rapports_dir):
            if file.endswith(".html") and not os.path.exists(os.path.join(rapports_dir, file + ".aes")):
                html_files.append(file)
    
    if not html_files:
        print("❌ Aucun fichier HTML non chiffré trouvé")
        return
    
    print(f"📄 Fichiers HTML trouvés: {html_files}")
    
    try:
        from encrypt import encrypt_file
        
        for html_file in html_files:
            file_path = os.path.join(rapports_dir, html_file)
            print(f"\n🔒 Chiffrement de {file_path}...")
            
            # Vérifier le fichier
            if not os.path.exists(file_path):
                print(f"❌ Fichier non trouvé: {file_path}")
                continue
            
            size = os.path.getsize(file_path)
            print(f"📊 Taille fichier: {size} bytes")
            
            if size == 0:
                print("❌ Fichier vide")
                continue
            
            # Chiffrer
            try:
                encrypt_file(file_path)
                
                # Vérifier le résultat
                encrypted_path = file_path + ".aes"
                if os.path.exists(encrypted_path):
                    encrypted_size = os.path.getsize(encrypted_path)
                    print(f"✅ Fichier chiffré: {encrypted_path} ({encrypted_size} bytes)")
                else:
                    print(f"❌ Fichier chiffré non créé: {encrypted_path}")
                    
            except Exception as e:
                print(f"❌ Erreur chiffrement: {e}")
                import traceback
                print(traceback.format_exc())
    
    except ImportError:
        print("❌ Module encrypt non disponible")

def create_corrected_nmap_script():
    """Créer une version corrigée du script nmap avec debug"""
    print("\n=== CRÉATION SCRIPT NMAP CORRIGÉ ===")
    
    script_content = '''import sys
import subprocess
from datetime import datetime
import os

def main():
    print("🔍 NMAP AVEC DEBUG CHIFFREMENT")
    
    if len(sys.argv) < 2:
        print("❌ Usage: nmap_msf.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Créer le dossier rapports
    rapports_dir = "rapports"
    os.makedirs(rapports_dir, exist_ok=True)
    
    html_path = os.path.join(rapports_dir, f"nmap_{date}.html")
    print(f"📄 Fichier de sortie: {html_path}")

    # Nmap simple pour test
    try:
        print("🚀 Lancement nmap...")
        nmap_result = subprocess.run([
            "nmap", "-sV", "-F", target
        ], capture_output=True, text=True, timeout=60)
        
        nmap_output = nmap_result.stdout if nmap_result.stdout else "Pas de sortie nmap"
        print(f"✅ Nmap terminé, {len(nmap_output)} caractères")
        
    except Exception as e:
        print(f"❌ Erreur nmap: {e}")
        nmap_output = f"Erreur nmap: {e}"

    # Générer HTML
    try:
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Nmap - {target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #007bff; color: white; padding: 20px; }}
        pre {{ background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Rapport Nmap</h1>
        <p>Cible: {target} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <h2>Résultats</h2>
    <pre>{nmap_output}</pre>
</body>
</html>"""

        with open(html_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML créé: {os.path.getsize(html_path)} bytes")
        
    except Exception as e:
        print(f"❌ Erreur HTML: {e}")
        return

    # Chiffrement avec debug détaillé
    try:
        print("🔒 Import module encrypt...")
        from encrypt import encrypt_file
        print("✅ Module importé")
        
        print("🔍 Vérifications pré-chiffrement...")
        print(f"   - Fichier existe: {os.path.exists(html_path)}")
        print(f"   - Est un fichier: {os.path.isfile(html_path)}")
        print(f"   - Taille: {os.path.getsize(html_path)} bytes")
        
        if not os.path.exists(html_path):
            print("❌ Fichier HTML non trouvé")
            return
            
        if os.path.getsize(html_path) == 0:
            print("❌ Fichier HTML vide")
            return
        
        print("🔒 Début chiffrement...")
        encrypt_file(html_path)
        print("✅ encrypt_file() terminé")
        
        # Vérifier le résultat
        encrypted_path = html_path + ".aes"
        print(f"🔍 Vérification fichier chiffré: {encrypted_path}")
        
        if os.path.exists(encrypted_path):
            size = os.path.getsize(encrypted_path)
            print(f"✅ SUCCÈS ! Fichier chiffré créé: {size} bytes")
        else:
            print("❌ ÉCHEC ! Fichier chiffré non créé")
            
        # Vérifier si l'original a été supprimé
        if os.path.exists(html_path):
            print("⚠️ Fichier original encore présent")
        else:
            print("✅ Fichier original supprimé")
        
    except Exception as e:
        print(f"❌ Erreur chiffrement: {e}")
        import traceback
        print("Traceback complet:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
'''
    
    try:
        with open("tools/nmap_msf_debug.py", "w") as f:
            f.write(script_content)
        print("✅ Script debug créé: tools/nmap_msf_debug.py")
    except Exception as e:
        print(f"❌ Erreur création script: {e}")

def main():
    print("🔧 DIAGNOSTIC ET CORRECTION CHIFFREMENT")
    print("=" * 50)
    
    # Vérifications
    if not check_encrypt_files():
        print("❌ Fichiers de chiffrement non valides")
        return
    
    if not test_encrypt_module():
        print("❌ Module encrypt non fonctionnel")
        return
    
    # Chiffrer le fichier existant
    encrypt_existing_file()
    
    # Créer script debug
    create_corrected_nmap_script()
    
    print("\n" + "=" * 50)
    print("🎯 ACTIONS RECOMMANDÉES:")
    print("1. Testez: python3 tools/nmap_msf_debug.py 127.0.0.1")
    print("2. Vérifiez: ls -la rapports/")
    print("3. Rechargez l'interface web")

if __name__ == "__main__":
    main()
