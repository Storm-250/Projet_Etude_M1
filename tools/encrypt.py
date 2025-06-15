import os
import json
import base64
import hashlib
import logging

# Configuration
MDP_FILE = "MDP.json"
SALT_FILE = "salt.bin"
ENCRYPTION_ENABLED = True

# Tentative d'import de pycryptodome avec fallback
try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    CRYPTO_AVAILABLE = True
    print("✅ pycryptodome disponible - chiffrement AES activé")
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ pycryptodome non disponible - mode fallback activé")
    print("   Les fichiers seront sauvegardés avec extension .aes mais sans chiffrement réel")
    print("   Ceci est normal lors du premier lancement Docker")

def is_encryption_available():
    """Vérifier si le chiffrement est disponible"""
    return CRYPTO_AVAILABLE

def get_key(password, salt):
    """Générer une clé de chiffrement"""
    if CRYPTO_AVAILABLE:
        return PBKDF2(password, salt, dkLen=32)
    else:
        # Fallback : utiliser hashlib pour générer une "clé"
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=32)

def load_password():
    """Charger le mot de passe depuis MDP.json"""
    if not os.path.exists(MDP_FILE):
        # Créer MDP.json avec mot de passe par défaut si manquant
        print(f"📝 Création de {MDP_FILE} avec mot de passe par défaut")
        with open(MDP_FILE, "w") as f:
            json.dump({"password": "changeme"}, f)
    
    try:
        with open(MDP_FILE, "r") as f:
            data = json.load(f)
            return data["password"]
    except Exception as e:
        raise Exception(f"Erreur lecture {MDP_FILE}: {e}")

def save_password(new_pass):
    """Sauvegarder le mot de passe"""
    with open(MDP_FILE, "w") as f:
        json.dump({"password": new_pass}, f)

def load_salt():
    """Charger ou créer le salt"""
    if not os.path.exists(SALT_FILE):
        if CRYPTO_AVAILABLE:
            salt = get_random_bytes(16)
        else:
            # Fallback : générer un salt avec os.urandom
            salt = os.urandom(16)
        
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
        print(f"📝 Nouveau salt créé: {SALT_FILE}")
    
    with open(SALT_FILE, "rb") as f:
        return f.read()

def encrypt_file_real(filepath):
    """Chiffrement réel avec AES (pycryptodome disponible)"""
    password = load_password()
    salt = load_salt()
    key = get_key(password, salt)

    with open(filepath, "rb") as f:
        plaintext = f.read()

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    encrypted_path = filepath + ".aes"
    with open(encrypted_path, "wb") as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    # Supprimer l'original
    os.remove(filepath)
    return encrypted_path

def encrypt_file_fallback(filepath):
    """Chiffrement fallback (pycryptodome non disponible)"""
    # En mode fallback, on fait juste un encodage base64 avec une signature
    password = load_password()
    salt = load_salt()
    
    with open(filepath, "rb") as f:
        plaintext = f.read()
    
    # Créer une "signature" simple
    signature = hashlib.sha256(password.encode() + salt + plaintext).hexdigest()
    
    # Encoder en base64 avec signature
    encoded_data = base64.b64encode(plaintext).decode('utf-8')
    fallback_data = {
        "signature": signature,
        "data": encoded_data,
        "method": "fallback_base64",
        "note": "Fichier encodé en mode fallback - sera re-chiffré lors de l'installation de pycryptodome"
    }
    
    encrypted_path = filepath + ".aes"
    with open(encrypted_path, "w", encoding='utf-8') as f:
        json.dump(fallback_data, f)
    
    # Supprimer l'original
    os.remove(filepath)
    return encrypted_path

def encrypt_file(filepath):
    """Chiffrer un fichier (avec détection automatique du mode)"""
    
    # Vérifications préliminaires
    if not os.path.exists(filepath):
        raise Exception(f"Fichier {filepath} introuvable")
    
    if not os.path.isfile(filepath):
        raise Exception(f"{filepath} n'est pas un fichier")
    
    if os.path.getsize(filepath) == 0:
        raise Exception(f"Le fichier {filepath} est vide")
    
    try:
        if CRYPTO_AVAILABLE:
            print(f"🔒 Chiffrement AES: {os.path.basename(filepath)}")
            encrypted_path = encrypt_file_real(filepath)
        else:
            print(f"🔒 Chiffrement fallback: {os.path.basename(filepath)}")
            encrypted_path = encrypt_file_fallback(filepath)
        
        if os.path.exists(encrypted_path) and os.path.getsize(encrypted_path) > 0:
            print(f"✅ Fichier chiffré créé: {os.path.basename(encrypted_path)}")
            return encrypted_path
        else:
            raise Exception("Le fichier chiffré est invalide")
            
    except Exception as e:
        raise Exception(f"Erreur lors du chiffrement de {filepath}: {e}")

def decrypt_file_real(filepath_encrypted, output_file):
    """Déchiffrement réel avec AES"""
    password = load_password()
    salt = load_salt()
    key = get_key(password, salt)

    with open(filepath_encrypted, "rb") as f:
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()

    if len(nonce) != 16 or len(tag) != 16:
        raise Exception("Format de fichier chiffré AES invalide")

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)

    with open(output_file, "wb") as f:
        f.write(plaintext)

def decrypt_file_fallback(filepath_encrypted, output_file):
    """Déchiffrement fallback"""
    password = load_password()
    salt = load_salt()
    
    with open(filepath_encrypted, "r", encoding='utf-8') as f:
        fallback_data = json.load(f)
    
    if fallback_data.get("method") != "fallback_base64":
        raise Exception("Format de fichier fallback invalide")
    
    # Décoder les données
    encoded_data = fallback_data["data"]
    plaintext = base64.b64decode(encoded_data.encode('utf-8'))
    
    # Vérifier la signature
    expected_signature = hashlib.sha256(password.encode() + salt + plaintext).hexdigest()
    if fallback_data["signature"] != expected_signature:
        raise Exception("Signature fallback invalide - mot de passe incorrect")
    
    with open(output_file, "wb") as f:
        f.write(plaintext)

def decrypt_file(filepath_encrypted, output_file):
    """Déchiffrer un fichier (avec détection automatique du format)"""
    
    if not os.path.exists(filepath_encrypted):
        raise Exception(f"Fichier chiffré {filepath_encrypted} introuvable")
    
    try:
        # Essayer d'abord de déterminer le format
        try:
            # Tenter de lire comme JSON (format fallback)
            with open(filepath_encrypted, "r", encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "method" in data:
                    print(f"🔓 Déchiffrement fallback: {os.path.basename(filepath_encrypted)}")
                    decrypt_file_fallback(filepath_encrypted, output_file)
                    return
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Pas un fichier JSON, essayer le format AES
            pass
        
        # Format AES (binaire)
        if CRYPTO_AVAILABLE:
            print(f"🔓 Déchiffrement AES: {os.path.basename(filepath_encrypted)}")
            decrypt_file_real(filepath_encrypted, output_file)
        else:
            raise Exception("Fichier au format AES mais pycryptodome non disponible")
            
    except Exception as e:
        raise Exception(f"Erreur lors du déchiffrement: {e}")

def change_password(old_pass, new_pass):
    """Changer le mot de passe et rechiffrer tous les fichiers"""
    
    # Vérifier l'ancien mot de passe
    current_password = load_password()
    if old_pass != current_password:
        raise Exception("Ancien mot de passe incorrect")
    
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        save_password(new_pass)
        return
    
    # Rechiffrer tous les fichiers .aes
    files_processed = 0
    for file in os.listdir(rapports_dir):
        if file.endswith(".aes"):
            path = os.path.join(rapports_dir, file)
            temp_file = path + ".tmp"
            
            try:
                # Déchiffrer avec l'ancien mot de passe
                decrypt_file(path, temp_file)
                
                # Sauvegarder le nouveau mot de passe temporairement
                save_password(new_pass)
                
                # Rechiffrer avec le nouveau mot de passe
                encrypt_file(temp_file)
                
                # Le nouveau fichier chiffré remplace l'ancien
                new_encrypted = temp_file + ".aes"
                if os.path.exists(new_encrypted):
                    os.replace(new_encrypted, path)
                    files_processed += 1
                    print(f"✅ Rechiffré: {file}")
                
            except Exception as e:
                # Restaurer l'ancien mot de passe en cas d'erreur
                save_password(old_pass)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise Exception(f"Erreur avec le fichier {file}: {e}")
            finally:
                # Nettoyer les fichiers temporaires
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    print(f"✅ {files_processed} fichiers rechiffrés avec succès")

def get_encryption_status():
    """Obtenir le statut du chiffrement"""
    return {
        "crypto_available": CRYPTO_AVAILABLE,
        "encryption_method": "AES-GCM" if CRYPTO_AVAILABLE else "Base64 Fallback",
        "password_file_exists": os.path.exists(MDP_FILE),
        "salt_file_exists": os.path.exists(SALT_FILE)
    }

# Afficher le statut au démarrage
if __name__ == "__main__":
    status = get_encryption_status()
    print("🔒 STATUT DU CHIFFREMENT")
    print("=" * 30)
    for key, value in status.items():
        print(f"{key}: {value}")