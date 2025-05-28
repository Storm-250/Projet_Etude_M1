import subprocess
import argparse

def main():
    # Argument parser pour récupérer l'URL depuis la ligne de commande
    parser = argparse.ArgumentParser(description="Lance feroxbuster sur une URL donnée.")
    parser.add_argument("url", help="URL cible pour le scan avec feroxbuster")
    args = parser.parse_args()

    # Commande feroxbuster
    command = [
        "feroxbuster",
        "--url", args.url,
        "--wordlist", "/usr/share/wordlists/dirb/common.txt",  # adapte selon ton système
        "--threads", "10",
        "--depth", "2",
        "--quiet"
    ]

    try:
        # Exécuter la commande
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Résultats Feroxbuster :\n")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de feroxbuster :")
        print(e.stderr)

if __name__ == "__main__":
    main()
