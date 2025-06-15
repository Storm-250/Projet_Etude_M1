from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import os
import json

MDP_FILE = "MDP.json"
SALT_FILE = "salt.bin"

def get_key(password, salt):
    return PBKDF2(password, salt, dkLen=32)

def load_password():
    if not os.path.exists(MDP_FILE):
        raise Exception("Fichier MDP.json manquant.")
    with open(MDP_FILE, "r") as f:
        data = json.load(f)
        return data["password"]

def save_password(new_pass):
    with open(MDP_FILE, "w") as f:
        json.dump({"password": new_pass}, f)

def load_salt():
    if not os.path.exists(SALT_FILE):
        salt = get_random_bytes(16)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
    else:
        with open(SALT_FILE, "rb") as f:
            salt = f.read()
    return salt

def encrypt_file(filepath):
    """Chiffre un fichier et le remplace par sa version chiffrée"""
    
    # Vérifications préliminaires
    if not os.path.exists(filepath):
        raise Exception(f"Fichier {filepath} introuvable")
    
    if not os.path.isfile(filepath):
        raise Exception(f"{filepath} n'est pas un fichier")
    
    if os.path.getsize(filepath) == 0:
        raise Exception(f"Le fichier {filepath} est vide")
    
    try:
        # Charger les paramètres de chiffrement
        password = load_password()
        salt = load_salt()
        key = get_key(password, salt)

        # Lire le fichier
        with open(filepath, "rb") as f:
            plaintext = f.read()

        if len(plaintext) == 0:
            raise Exception("Le contenu du fichier est vide")

        # Chiffrer
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        # Sauvegarder la version chiffrée
        encrypted_path = filepath + ".aes"
        with open(encrypted_path, "wb") as f:
            # Écrire dans l'ordre: nonce, tag, ciphertext
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)

        # Supprimer l'original seulement si le chiffrement a réussi
        if os.path.exists(encrypted_path) and os.path.getsize(encrypted_path) > 0:
            os.remove(filepath)
            print(f"🗑️ Fichier original supprimé: {filepath}")
        else:
            raise Exception("Le fichier chiffré est invalide")
            
    except Exception as e:
        raise Exception(f"Erreur lors du chiffrement de {filepath}: {e}")

def decrypt_file(filepath_encrypted, output_file):
    """Déchiffre un fichier chiffré"""
    
    if not os.path.exists(filepath_encrypted):
        raise Exception(f"Fichier chiffré {filepath_encrypted} introuvable")
    
    try:
        password = load_password()
        salt = load_salt()
        key = get_key(password, salt)

        with open(filepath_encrypted, "rb") as f:
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        if len(nonce) != 16 or len(tag) != 16:
            raise Exception("Format de fichier chiffré invalide")

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        with open(output_file, "wb") as f:
            f.write(plaintext)
            
    except Exception as e:
        raise Exception(f"Erreur lors du déchiffrement: {e}")

def change_password(old_pass, new_pass):
    """Change le mot de passe et rechiffre tous les fichiers"""
    
    # Vérifier l'ancien mot de passe
    current_password = load_password()
    if old_pass != current_password:
        raise Exception("Ancien mot de passe incorrect")
    
    # Créer le dossier rapports s'il n'existe pas
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        return  # Pas de fichiers à rechiffrer
    
    salt = load_salt()
    key_old = get_key(old_pass, salt)
    key_new = get_key(new_pass, salt)

    # Rechiffrer tous les fichiers .aes
    for file in os.listdir(rapports_dir):
        if file.endswith(".aes"):
            path = os.path.join(rapports_dir, file)
            try:
                # Déchiffrer avec l'ancien mot de passe
                with open(path, "rb") as f:
                    nonce = f.read(16)
                    tag = f.read(16)
                    ciphertext = f.read()
                    
                cipher_old = AES.new(key_old, AES.MODE_GCM, nonce=nonce)
                plaintext = cipher_old.decrypt_and_verify(ciphertext, tag)
                
                # Rechiffrer avec le nouveau mot de passe
                cipher_new = AES.new(key_new, AES.MODE_GCM)
                new_ciphertext, new_tag = cipher_new.encrypt_and_digest(plaintext)
                
                # Sauvegarder
                with open(path, "wb") as f:
                    f.write(cipher_new.nonce)
                    f.write(new_tag)
                    f.write(new_ciphertext)
                    
            except Exception as e:
                raise Exception(f"Erreur avec le fichier {file} : {e}")

    # Sauvegarder le nouveau mot de passe
    save_password(new_pass)