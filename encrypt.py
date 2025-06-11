from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import os
import json
from base64 import b64encode, b64decode

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
    password = load_password()
    salt = load_salt()
    key = get_key(password, salt)

    with open(filepath, "rb") as f:
        plaintext = f.read()

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    with open(filepath + ".aes", "wb") as f:
        [f.write(x) for x in (cipher.nonce, tag, ciphertext)]

    os.remove(filepath)

def decrypt_file(filepath_encrypted, output_file):
    password = load_password()
    salt = load_salt()
    key = get_key(password, salt)

    with open(filepath_encrypted, "rb") as f:
        nonce, tag, ciphertext = [f.read(x) for x in (16, 16, -1)]

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)

    with open(output_file, "wb") as f:
        f.write(plaintext)

def change_password(old_pass, new_pass):
    salt = load_salt()
    key_old = get_key(old_pass, salt)
    key_new = get_key(new_pass, salt)

    for file in os.listdir("rapport"):
        if file.endswith(".html.aes"):
            path = os.path.join("rapport", file)
            try:
                with open(path, "rb") as f:
                    nonce, tag, ciphertext = [f.read(x) for x in (16, 16, -1)]
                cipher_old = AES.new(key_old, AES.MODE_GCM, nonce=nonce)
                plaintext = cipher_old.decrypt_and_verify(ciphertext, tag)
                cipher_new = AES.new(key_new, AES.MODE_GCM)
                new_ciphertext, new_tag = cipher_new.encrypt_and_digest(plaintext)
                with open(path, "wb") as f:
                    [f.write(x) for x in (cipher_new.nonce, new_tag, new_ciphertext)]
            except Exception as e:
                raise Exception(f"Erreur avec le fichier {file} : {e}")

    save_password(new_pass)
