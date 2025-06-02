import subprocess, sys, os
import zipfile

def extract_pass_file():
    zip_path = os.path.join('tools', 'pass.zip')       # chemin du ZIP
    extract_path = os.path.join('tools', 'pass.txt')       # chemin du fichier extrait

    if not os.path.exists(extract_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('tools')                # extrait dans le même dossier
                print("✅ 'pass.txt' extrait avec succès.")
        except zipfile.BadZipFile:
            print("❌ Erreur : Le fichier ZIP est corrompu ou invalide.")
    else:
        print("ℹ️ 'pass.txt' déjà présent, extraction non nécessaire.")

extract_pass_file()

def run_ferox(target, timestamp):
    output_file = f"reports/feroxbuster_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "feroxbuster", "-u", target, "-w", "pass.txt"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur Feroxbuster : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_ferox(sys.argv[1], sys.argv[2])
