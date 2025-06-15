#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_current_files():
    """Sauvegarder les fichiers actuels"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_encrypt_{timestamp}"
    
    print(f"📦 Création de la sauvegarde: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Sauvegarder encrypt.py actuel
    if os.path.exists("encrypt.py"):
        shutil.copy2("encrypt.py", f"{backup_dir}/encrypt_old.py")
        print("✅ encrypt.py sauvegardé")
    
    return backup_dir

def test_new_encrypt():
    """Tester le nouveau module encrypt"""
    print("\n🔧 Test du nouveau module encrypt...")
    
    try:
        # Recharger le module
        import importlib
        if 'encrypt' in globals():
            importlib.reload(encrypt)
        else:
            import encrypt
        
        # Tester les fonctions de base
        status = encrypt.get_encryption_status()
        print("✅ Module encrypt chargé")
        
        print("📊 Statut du chiffrement:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Tester le chargement du mot de passe
        password = encrypt.load_password()
        print(f"✅ Mot de passe chargé: '{password}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test module: {e}")
        return False

def encrypt_existing_html_files():
    """Chiffrer les fichiers HTML existants avec le nouveau système"""
    print("\n🔒 Chiffrement des fichiers HTML existants...")
    
    try:
        import encrypt
        
        encrypted_count = 0
        
        # Chercher dans rapport et rapports
        for folder in ["rapport", "rapports"]:
            if not os.path.exists(folder):
                continue
                
            html_files = list(Path(folder).glob("*.html"))
            if not html_files:
                continue
                
            print(f"\n📁 Traitement du dossier {folder}/:")
            
            for html_file in html_files:
                aes_file = str(html_file) + ".aes"
                
                # Ignorer si déjà chiffré
                if os.path.exists(aes_file):
                    print(f"   ⏭️ {html_file.name} déjà chiffré")
                    continue
                
                try:
                    print(f"   🔒 Chiffrement: {html_file.name}")
                    encrypt.encrypt_file(str(html_file))
                    
                    if os.path.exists(aes_file):
                        size = os.path.getsize(aes_file)
                        print(f"   ✅ Succès: {html_file.name}.aes ({size} bytes)")
                        encrypted_count += 1
                    else:
                        print(f"   ❌ Échec: {html_file.name}")
                        
                except Exception as e:
                    print(f"   ❌ Erreur {html_file.name}: {e}")
        
        print(f"\n✅ {encrypted_count} fichiers chiffrés")
        return encrypted_count > 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def verify_encryption_works():
    """Vérifier que le chiffrement/déchiffrement fonctionne"""
    print("\n🧪 Test complet chiffrement/déchiffrement...")
    
    try:
        import encrypt
        
        # Créer un fichier de test
        test_content = f"""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Test de chiffrement</h1>
    <p>Date: {datetime.now()}</p>
    <p>Mode: {encrypt.get_encryption_status()['encryption_method']}</p>
</body>
</html>"""
        
        os.makedirs("rapports", exist_ok=True)
        test_file = "rapports/test_encrypt_fallback.html"
        
        # Écrire le fichier test
        with open(test_file, "w", encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Fichier test créé: {test_file}")
        
        # Chiffrer
        encrypt.encrypt_file(test_file)
        
        encrypted_file = test_file + ".aes"
        if not os.path.exists(encrypted_file):
            print("❌ Fichier chiffré non créé")
            return False
        
        print(f"✅ Chiffrement réussi: {encrypted_file}")
        
        # Déchiffrer
        decrypt_file = "rapports/test_decrypt_fallback.html"
        encrypt.decrypt_file(encrypted_file, decrypt_file)
        
        if not os.path.exists(decrypt_file):
            print("❌ Déchiffrement échoué")
            return False
        
        # Vérifier le contenu
        with open(decrypt_file, "r", encoding='utf-8') as f:
            decrypted_content = f.read()
        
        if "Test de chiffrement" in decrypted_content:
            print("✅ Déchiffrement vérifié - contenu correct")
        else:
            print("❌ Contenu déchiffré incorrect")
            return False
        
        # Nettoyer
        for temp_file in [encrypted_file, decrypt_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def show_final_status():
    """Afficher le statut final"""
    print("\n📊 STATUT FINAL:")
    print("=" * 40)
    
    # Compter les fichiers
    for folder in ["rapport", "rapports"]:
        if os.path.exists(folder):
            files = list(Path(folder).glob("*"))
            aes_files = [f for f in files if f.name.endswith('.aes')]
            html_files = [f for f in files if f.name.endswith('.html')]
            
            print(f"\n📁 {folder}/:")
            print(f"   Total: {len(files)} fichiers")
            print(f"   HTML: {len(html_files)} fichiers")
            print(f"   AES:  {len(aes_files)} fichiers")
            
            if aes_files:
                print("   Fichiers chiffrés récents:")
                for aes_file in sorted(aes_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    size = aes_file.stat().st_size
                    mtime = datetime.fromtimestamp(aes_file.stat().st_mtime)
                    print(f"     - {aes_file.name} ({size} bytes, {mtime.strftime('%H:%M:%S')})")

def main():
    print("🔄 MIGRATION VERS ENCRYPT.PY AVEC FALLBACK")
    print("=" * 50)
    
    # Étape 1: Sauvegarde
    backup_dir = backup_current_files()
    
    # Étape 2: Test du nouveau module
    print("\n1️⃣ Test du nouveau module encrypt...")
    if not test_new_encrypt():
        print("❌ Échec du test - arrêt de la migration")
        return False
    
    # Étape 3: Test fonctionnel
    print("\n2️⃣ Test fonctionnel...")
    if not verify_encryption_works():
        print("❌ Test fonctionnel échoué")
        return False
    
    # Étape 4: Chiffrement des fichiers existants
    print("\n3️⃣ Chiffrement des fichiers existants...")
    encrypt_existing_html_files()
    
    # Étape 5: Statut final
    print("\n4️⃣ Vérification finale...")
    show_final_status()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
    print("\n📋 AVANTAGES DU NOUVEAU SYSTÈME:")
    print("✅ Fonctionne avec ou sans pycryptodome")
    print("✅ Mode fallback pour Docker sans crypto")
    print("✅ Migration automatique lors de l'installation de crypto")
    print("✅ Messages informatifs sur le mode utilisé")
    print("\n🔄 PROCHAINES ÉTAPES:")
    print("1. Redémarrez votre application")
    print("2. Les rapports devraient maintenant être visibles")
    print("3. Les nouveaux scans fonctionneront immédiatement")
    print(f"\n💾 Sauvegarde créée: {backup_dir}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Migration échouée")
        exit(1)