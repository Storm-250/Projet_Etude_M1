import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file

if len(sys.argv) < 2:
    print("Usage: gobuster.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/gobuster_{date}.html"

# Utilisation de gobuster pour brute-force des répertoires
cmd = ["gobuster", "dir", "-u", f"http://{target}", "-w", "/usr/share/wordlists/dirb/common.txt"]
gobuster_result = subprocess.run(cmd, capture_output=True, text=True).stdout

with open(html_path, "w") as f:
    f.write("<h1>Résultat Gobuster</h1><pre>")
    f.write(gobuster_result)
    f.write("</pre>")

encrypt_file(html_path)
