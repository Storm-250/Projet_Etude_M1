import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file
import os

if len(sys.argv) < 2:
    print("Usage: nmap.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_file = f"rapport/nmap_{date}"

# Lance nmap
nmap_result = subprocess.run(["nmap", "-sV", target], capture_output=True, text=True).stdout
nmap_txt = f"{base_file}.txt"
with open(nmap_txt, "w") as f:
    f.write(nmap_result)

# Recherche vulnérabilités via searchsploit
searchsploit_result = subprocess.run(["searchsploit", "--nmap", nmap_txt], capture_output=True, text=True).stdout

html_path = f"{base_file}.html"
with open(html_path, "w") as f:
    f.write("<h1>Résultat Nmap</h1><pre>")
    f.write(nmap_result)
    f.write("</pre><h1>Vulnérabilités détectées (searchsploit)</h1><pre>")
    f.write(searchsploit_result)
    f.write("</pre>")

encrypt_file(html_path)
