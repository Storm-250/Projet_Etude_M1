import sys
from datetime import datetime
from encrypt import encrypt_file
import subprocess

if len(sys.argv) < 2:
    print("Usage: nikto.py <target>")
    sys.exit(1)

target = sys.argv[1]
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/nikto_{date}.html"

nikto_cmd = ["nikto", "-h", target]
nikto_result = subprocess.run(nikto_cmd, capture_output=True, text=True).stdout

with open(html_path, "w") as f:
    f.write("<h1>Résultat Nikto</h1><pre>")
    f.write(nikto_result)
    f.write("</pre>")

encrypt_file(html_path)
