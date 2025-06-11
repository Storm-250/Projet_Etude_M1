import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file

if len(sys.argv) < 2:
    print("Usage: sqlmap.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/sqlmap_{date}.html"

# Exemple simple : test GET sur la page cible
sqlmap_cmd = ["sqlmap", "-u", f"http://{target}", "--batch", "--crawl=1"]
sqlmap_result = subprocess.run(sqlmap_cmd, capture_output=True, text=True).stdout

with open(html_path, "w") as f:
    f.write("<h1>Résultat SQLMap</h1><pre>")
    f.write(sqlmap_result)
    f.write("</pre>")

encrypt_file(html_path)
