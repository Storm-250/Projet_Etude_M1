import subprocess
import sys
import time
import xml.etree.ElementTree as ET

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
    if "Connected to" in result.stdout:
        print("[+] Base connectée.")
        return True
    print("[!] Base non connectée.")
    return False

def reinit_msfdb():
    print("[*] Réinitialisation de la base Metasploit...")
    subprocess.run(["sudo", "msfdb", "reinit"], check=True)
    time.sleep(3)

def run_nmap_scan(target_ip, output_file="scan.xml"):
    print(f"[*] Scan Nmap en cours sur {target_ip}...")
    subprocess.run(["nmap", "-sS", "-sV", "-T4", "-oX", output_file, target_ip], check=True)
    print(f"[+] Résultats enregistrés dans {output_file}")

def import_to_metasploit(xml_file):
    print(f"[*] Importation dans Metasploit...")
    commands = f"db_import {xml_file}; hosts; services; exit"
    subprocess.run(["msfconsole", "-q", "-x", commands])

def extract_services_from_xml(xml_file):
    print("[*] Extraction des services depuis le scan Nmap...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    services = []
    for host in root.findall("host"):
        addr_elem = host.find("address")
        if addr_elem is None:
            continue
        addr = addr_elem.attrib["addr"]
        ports = host.find("ports")
        if ports is None:
            continue
        for port in ports.findall("port"):
            portid = port.attrib["portid"]
            protocol = port.attrib["protocol"]
            service_elem = port.find("service")
            service_name = service_elem.attrib.get("name", "unknown") if service_elem is not None else "unknown"
            services.append((addr, portid, protocol, service_name))
    return services

def find_possible_exploits(services, output_file="exploits_possibles.txt"):
    print("[*] Recherche d'exploits disponibles dans Metasploit...")
    with open(output_file, "w") as f:
        for ip, port, proto, service in services:
            search_term = service if service != "unknown" else f"port:{port}"
            f.write(f"\n[+] {ip}:{port} ({service})\n")
            f.write("-" * 40 + "\n")

            search_cmd = f"search {search_term}; exit"
            result = subprocess.run(
                ["msfconsole", "-q", "-x", search_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )

            # Extraire uniquement les modules "exploit/"
            lines = result.stdout.splitlines()
            exploits = [line for line in lines if line.strip().startswith("exploit/")]

            if exploits:
                for line in exploits:
                    f.write(line + "\n")
            else:
                f.write("Aucun exploit trouvé pour ce service.\n")
    print(f"[+] Exploits enregistrés dans {output_file}")

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
            print("[!] Connexion à la base échouée. Abandon.")
            sys.exit(1)

    run_nmap_scan(target_ip, xml_file)
    import_to_metasploit(xml_file)

    services = extract_services_from_xml(xml_file)
    find_possible_exploits(services)

if __name__ == "__main__":
    main()
