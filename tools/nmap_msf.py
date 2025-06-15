import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os
import requests
import json
import re

class CVEAnalyzer:
    def __init__(self):
        self.nvd_api = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.vulners_api = "https://vulners.com/api/v3/search/lucene/"
    
    def parse_nmap_services(self, nmap_output):
        """Parse les services depuis la sortie nmap"""
        services = []
        lines = nmap_output.split('\n')
        
        for line in lines:
            if '/tcp' in line and 'open' in line:
                # Pattern pour capturer les infos de service
                pattern = r'(\d+)/(tcp|udp)\s+open\s+(\w+)\s*(.*)?'
                match = re.search(pattern, line)
                if match:
                    port = match.group(1)
                    service = match.group(3)
                    version = match.group(4) if match.group(4) else ""
                    
                    # Nettoyer et extraire la version
                    version_clean = self.extract_version(version)
                    
                    services.append({
                        'port': port,
                        'service': service,
                        'version': version_clean,
                        'raw_version': version
                    })
        
        return services
    
    def extract_version(self, version_string):
        """Extrait proprement le produit et la version"""
        if not version_string:
            return {}
        
        # Patterns pour différents formats
        patterns = [
            r'(\w+)\s+([\d\.]+)',  # Apache 2.4.41
            r'(\w+)/([\d\.]+)',    # nginx/1.18.0
            r'(\w+)\s+httpd\s+([\d\.]+)',  # Apache httpd 2.4.41
            r'OpenSSH\s+([\d\.]+)',  # OpenSSH 7.4
            r'MySQL\s+([\d\.]+)',    # MySQL 5.7.30
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_string, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return {'product': match.group(1), 'version': match.group(2)}
                else:
                    return {'product': 'OpenSSH', 'version': match.group(1)}
        
        return {'product': version_string.split()[0] if version_string.split() else '', 'version': ''}
    
    def search_cves_vulners(self, product, version):
        """Recherche CVE via Vulners API (gratuit)"""
        try:
            query = f"product:{product} AND version:{version}"
            data = {
                "query": query,
                "size": 10,
                "sort": "published",
                "order": "desc"
            }
            
            response = requests.post(self.vulners_api, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                cves = []
                
                for item in result.get('data', {}).get('search', []):
                    if item.get('_source', {}).get('type') == 'cve':
                        source = item['_source']
                        cves.append({
                            'id': source.get('id'),
                            'title': source.get('title'),
                            'cvss': source.get('cvss', {}).get('score', 'N/A'),
                            'published': source.get('published'),
                            'description': source.get('description', '')[:200] + '...'
                        })
                
                return cves
        except Exception as e:
            print(f"Erreur Vulners API: {e}")
        
        return []
    
    def search_cves_simple(self, product, version):
        """Recherche simple via CVE-Search"""
        try:
            url = f"https://cve.circl.lu/api/search/{product}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                cves = response.json()
                relevant_cves = []
                
                for cve in cves[:5]:  # Limiter à 5 résultats
                    relevant_cves.append({
                        'id': cve.get('id'),
                        'summary': cve.get('summary', '')[:200] + '...',
                        'cvss': cve.get('cvss', 'N/A'),
                        'published': cve.get('Published', '')
                    })
                
                return relevant_cves
        except Exception as e:
            print(f"Erreur CVE-Search: {e}")
        
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: nmap_msf.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # IMPORTANT: Utiliser le bon format de nom attendu par l'application web
    # Format attendu: outil_YYYY-MM-DD_HH-MM-SS.html
    html_path = os.path.join(rapports_dir, f"nmap_{date}.html")
    
    print(f"🔍 Scan nmap en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Lance nmap avec scripts de vulnérabilités
    try:
        nmap_result = subprocess.run([
            "nmap", 
            "-sV",  # Version detection
            "-sC",  # Scripts par défaut
            "--script", "vuln",  # Scripts de vulnérabilités
            target
        ], capture_output=True, text=True, timeout=300)
        
        nmap_output = nmap_result.stdout
        
        if nmap_result.returncode != 0:
            print(f"⚠️ Nmap terminé avec le code {nmap_result.returncode}")
            if nmap_result.stderr:
                print(f"Stderr: {nmap_result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: Le scan nmap a pris trop de temps")
        nmap_output = "Scan interrompu par timeout"
    except FileNotFoundError:
        print("❌ Erreur: nmap n'est pas installé")
        nmap_output = "Erreur: nmap non trouvé"
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")
        nmap_output = f"Erreur: {e}"

    print("🔎 Analyse CVE en cours...")

    # Analyser les CVE seulement si nmap a fonctionné
    cve_results = {}
    services = []
    if "Scan interrompu" not in nmap_output and "Erreur:" not in nmap_output:
        analyzer = CVEAnalyzer()
        services = analyzer.parse_nmap_services(nmap_output)
        
        for service in services:
            if service['version'].get('product'):
                product = service['version']['product']
                version = service['version']['version']
                
                print(f"  📡 Analyse {product} {version} (port {service['port']})")
                
                # Essayer d'abord Vulners, puis CVE-Search
                cves = analyzer.search_cves_vulners(product, version)
                if not cves:
                    cves = analyzer.search_cves_simple(product, version)
                
                if cves:
                    cve_results[f"{product}:{service['port']}"] = cves

    # Générer le rapport HTML
    try:
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Nmap + CVE - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .service {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }}
        .cve {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; }}
        .cve-high {{ background-color: #f8d7da; border-left-color: #dc3545; }}
        .severity {{ font-weight: bold; padding: 2px 8px; border-radius: 3px; color: white; }}
        .high {{ background-color: #dc3545; }}
        .medium {{ background-color: #ffc107; color: black; }}
        .low {{ background-color: #28a745; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Rapport de Sécurité Complet</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Services détectés:</strong> {len(services)}<br>
            <strong>🚨 Services avec CVE:</strong> {len(cve_results)}
        </div>
        
        <h2>📊 Résultats Nmap Détaillés</h2>""")

            if "Erreur:" in nmap_output or "Scan interrompu" in nmap_output:
                f.write(f'<div class="error"><strong>Erreur lors du scan:</strong><br><pre>{nmap_output}</pre></div>')
            else:
                f.write(f'<pre>{nmap_output}</pre>')

            f.write('<h2>🔓 Vulnérabilités CVE Identifiées</h2>')

            if not cve_results:
                f.write("""
        <div class="info">
            <strong>✅ Aucune CVE majeure trouvée automatiquement</strong><br>
            Cela ne garantit pas la sécurité. Effectuez des tests manuels supplémentaires.
        </div>""")
            else:
                for service, cves in cve_results.items():
                    f.write(f"""
        <div class="service">
            <h3>🔧 {service}</h3>
            <strong>CVE trouvées:</strong> {len(cves)}
        </div>""")
                    
                    for cve in cves:
                        cvss = cve.get('cvss', 'N/A')
                        severity_class = 'low'
                        if isinstance(cvss, (int, float)):
                            if cvss >= 7.0:
                                severity_class = 'high'
                            elif cvss >= 4.0:
                                severity_class = 'medium'
                        
                        f.write(f"""
            <div class="cve {'cve-high' if severity_class == 'high' else ''}">
                <strong>{cve.get('id', 'N/A')}</strong>
                <span class="severity {severity_class}">CVSS: {cvss}</span><br>
                <em>Publié:</em> {cve.get('published', 'N/A')}<br>
                <p>{cve.get('description', cve.get('summary', cve.get('title', 'Pas de description')))}</p>
            </div>""")

            f.write("""
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport généré: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return

    # Chiffrement
    try:
        # Vérifier que le fichier existe et est lisible
        if not os.path.exists(html_path):
            print(f"❌ Fichier {html_path} non trouvé pour chiffrement")
            return
            
        if not os.path.isfile(html_path):
            print(f"❌ {html_path} n'est pas un fichier")
            return
            
        # Vérifier la taille du fichier
        file_size = os.path.getsize(html_path)
        print(f"📊 Taille du fichier: {file_size} bytes")
        
        if file_size == 0:
            print("⚠️ Le fichier est vide, chiffrement annulé")
            return
            
        # Procéder au chiffrement
        print("🔒 Chiffrement en cours...")
        encrypt_file(html_path)
        
        # Vérifier que le fichier chiffré a été créé
        encrypted_path = html_path + ".aes"
        if os.path.exists(encrypted_path):
            encrypted_size = os.path.getsize(encrypted_path)
            print(f"✅ Fichier chiffré: {encrypted_path} ({encrypted_size} bytes)")
        else:
            print("❌ Le fichier chiffré n'a pas été créé")
        
    except Exception as e:
        print(f"❌ Erreur lors du chiffrement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()