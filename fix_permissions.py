#!/usr/bin/env python3

import os
import stat
import shutil
from pathlib import Path

def fix_file_permissions():
    """Corriger les permissions des fichiers critiques"""
    print("🔧 CORRECTION DES PERMISSIONS")
    print("=" * 40)
    
    files_to_fix = [
        "MDP.json",
        "salt.bin",
        "encrypt.py",
        "app.py"
    ]
    
    dirs_to_fix = [
        "rapports",
        "rapport",
        "tools"
    ]
    
    # Corriger les permissions des fichiers
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                # Donner les permissions de lecture/écriture au propriétaire
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                print(f"✅ Permissions corrigées: {file_path}")
            except Exception as e:
                print(f"⚠️ Impossible de corriger {file_path}: {e}")
        else:
            print(f"⏭️ Fichier non trouvé: {file_path}")
    
    # Corriger les permissions des dossiers
    for dir_path in dirs_to_fix:
        if os.path.exists(dir_path):
            try:
                # Permissions complètes pour les dossiers
                os.chmod(dir_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                print(f"✅ Permissions dossier corrigées: {dir_path}")
                
                # Corriger aussi les fichiers dans le dossier
                for file_in_dir in Path(dir_path).glob("*"):
                    if file_in_dir.is_file():
                        try:
                            os.chmod(file_in_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                        except:
                            pass  # Ignorer les erreurs sur les fichiers individuels
                            
            except Exception as e:
                print(f"⚠️ Impossible de corriger {dir_path}: {e}")
        else:
            print(f"⏭️ Dossier non trouvé: {dir_path}")

def recreate_salt_file():
    """Recréer le fichier salt.bin avec les bonnes permissions"""
    print("\n🧂 RECRÉATION DU FICHIER SALT")
    print("=" * 40)
    
    salt_file = "salt.bin"
    
    if os.path.exists(salt_file):
        try:
            # Sauvegarder l'ancien salt
            shutil.copy2(salt_file, salt_file + ".backup")
            print(f"✅ Sauvegarde créée: {salt_file}.backup")
            
            # Supprimer l'ancien fichier problématique
            os.remove(salt_file)
            print(f"✅ Ancien fichier supprimé: {salt_file}")
            
        except Exception as e:
            print(f"⚠️ Erreur suppression: {e}")
    
    # Créer un nouveau fichier salt avec les bonnes permissions
    try:
        salt_data = os.urandom(16)
        
        with open(salt_file, "wb") as f:
            f.write(salt_data)
        
        # Définir les permissions explicitement
        os.chmod(salt_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✅ Nouveau fichier salt créé: {salt_file}")
        print(f"   Taille: {len(salt_data)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création salt: {e}")
        return False

def test_file_access():
    """Tester l'accès aux fichiers critiques"""
    print("\n🧪 TEST D'ACCÈS AUX FICHIERS")
    print("=" * 40)
    
    files_to_test = ["MDP.json", "salt.bin"]
    
    all_ok = True
    for file_path in files_to_test:
        if not os.path.exists(file_path):
            print(f"❌ Fichier manquant: {file_path}")
            all_ok = False
            continue
        
        try:
            # Test lecture
            with open(file_path, "rb") as f:
                data = f.read()
            print(f"✅ Lecture OK: {file_path} ({len(data)} bytes)")
            
            # Test écriture (pour les fichiers qui le permettent)
            if file_path == "salt.bin":
                with open(file_path, "ab") as f:
                    pass  # Juste ouvrir en mode append
                print(f"✅ Écriture OK: {file_path}")
                
        except Exception as e:
            print(f"❌ Erreur accès {file_path}: {e}")
            all_ok = False
    
    return all_ok

def test_encrypt_module():
    """Tester le module encrypt après correction"""
    print("\n🔒 TEST MODULE ENCRYPT APRÈS CORRECTION")
    print("=" * 40)
    
    try:
        # Recharger le module encrypt
        import importlib
        import sys
        if 'encrypt' in sys.modules:
            importlib.reload(sys.modules['encrypt'])
        
        import encrypt
        
        # Créer un fichier de test simple
        os.makedirs("rapports", exist_ok=True)
        test_file = "rapports/test_permissions.html"
        
        test_content = f"""<!DOCTYPE html>
<html><head><title>Test Permissions</title></head>
<body><h1>Test {os.getpid()}</h1></body></html>"""
        
        with open(test_file, "w", encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Fichier test créé: {test_file}")
        
        # Tenter le chiffrement
        encrypt.encrypt_file(test_file)
        
        encrypted_file = test_file + ".aes"
        if os.path.exists(encrypted_file):
            size = os.path.getsize(encrypted_file)
            print(f"✅ Chiffrement réussi: {encrypted_file} ({size} bytes)")
            
            # Test de déchiffrement
            decrypt_file = "rapports/test_decrypt_permissions.html"
            encrypt.decrypt_file(encrypted_file, decrypt_file)
            
            if os.path.exists(decrypt_file):
                print(f"✅ Déchiffrement réussi: {decrypt_file}")
                
                # Nettoyer
                for temp_file in [encrypted_file, decrypt_file]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                return True
            else:
                print("❌ Déchiffrement échoué")
        else:
            print("❌ Chiffrement échoué")
    
    except Exception as e:
        print(f"❌ Erreur test encrypt: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    print("🔧 CORRECTION DES PERMISSIONS ET FICHIERS")
    print("=" * 50)
    
    # Étape 1: Corriger les permissions générales
    fix_file_permissions()
    
    # Étape 2: Recréer le fichier salt
    if not recreate_salt_file():
        print("❌ Impossible de recréer le fichier salt")
        return False
    
    # Étape 3: Tester l'accès
    if not test_file_access():
        print("❌ Tests d'accès échoués")
        return False
    
    # Étape 4: Tester le module encrypt
    if not test_encrypt_module():
        print("❌ Test du module encrypt échoué")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 CORRECTION TERMINÉE AVEC SUCCÈS !")
    print("\n📋 PROCHAINES ÉTAPES:")
    print("1. Relancez la migration: python3 migrate_to_fallback.py")
    print("2. Ou testez directement l'application")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Correction échouée")
        print("🔧 Solutions alternatives:")
        print("   sudo chown $USER:$USER *.bin *.json")
        print("   chmod 644 *.bin *.json")
        exit(1)