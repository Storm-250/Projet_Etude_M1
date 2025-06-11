import sys
import subprocess
from datetime import datetime
from encrypt import encrypt_file

if len(sys.argv) < 2:
    print("Usage: feroxbuster.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/feroxbuster_{date}.html"

cmd = ["feroxbuster", "-u", f"http://{target}", "-w", "/usr/share/seclists/Discovery/Web-Content/common.txt"]
ferox_result = subprocess.run(cmd, capture_output=True, text=True).stdout

with open(html_path, "w") as f:
    f.write("<h1>Résultat Feroxbuster</h1><pre>")
    f.write(ferox_result)
    f.write("</pre>")

encrypt_file(html_path)
