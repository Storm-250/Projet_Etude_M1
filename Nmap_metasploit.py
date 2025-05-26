import subprocess
import sys
import time

def start_postgresql():
    print("[*] Démarrage de PostgreSQL...")
    subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)

def check_db_connection():
    print("[*] Vérification de la connexion à la base de données Metasploit...")
    result = subprocess.run(
        ["msfconsole", "-q", "-x", "db_status; exit"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output = result.stdout
    if "Connected to" in output:
        print("[+] Base de données Metasploit connectée.")
        return True
    else:
        print("[!] Base non connectée.")
        return False

def reinit_msfdb():
    print("[*] Réinitialisation de la base Metasploit...")
    subprocess.run(["sudo", "msfdb", "reinit"], check=True)
    time.sleep(3)  # Laisse le temps à la base de démarrer

def run_nmap_scan(target_ip, output_file="scan.xml"):
    print(f"[*] Scan Nmap sur {target_ip}...")
    subprocess.run(["nmap", "-sS", "-sV", "-T4", "-oX", output_file, target_ip], check=True)
    print(f"[+] Résultats enregistrés dans {output_file}")

def import_to_metasploit(xml_file):
    print(f"[*] Importation de {xml_file} dans Metasploit...")
    commands = f"db_import {xml_file}; hosts; services; exit"
    subprocess.run(["msfconsole", "-q", "-x", commands])

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 auto_nmap_msf.py <IP/CIDR>")
        sys.exit(1)

    target_ip = sys.argv[1]
    xml_file = "scan.xml"

    start_postgresql()

    if not check_db_connection():
        reinit_msfdb()
        if not check_db_connection():
            print("[!] Impossible de connecter à la base Metasploit. Abandon.")
            sys.exit(1)

    run_nmap_scan(target_ip, xml_file)
    import_to_metasploit(xml_file)

if __name__ == "__main__":
    main()
