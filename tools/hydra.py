import sys
from datetime import datetime
from encrypt import encrypt_file
import subprocess

if len(sys.argv) < 2:
    print("Usage: hydra.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/hydra_{date}.html"

# Exemple simple : test SSH par défaut (tu peux adapter)
hydra_cmd = ["hydra", "-L", "users.txt", "-P", "passwords.txt", f"ssh://{target}"]
hydra_result = subprocess.run(hydra_cmd, capture_output=True, text=True).stdout

with open(html_path, "w") as f:
    f.write("<h1>Résultat Hydra</h1><pre>")
    f.write(hydra_result)
    f.write("</pre>")

encrypt_file(html_path)
