import sys
import requests
from datetime import datetime
from encrypt import encrypt_file

if len(sys.argv) < 2:
    print("Usage: https_test.py <target>")
    sys.exit(1)

target = sys.argv[1]
url = f"https://{target}"
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
html_path = f"rapport/https_test_{date}.html"

try:
    r = requests.get(url, timeout=5)
    content = f"Status Code: {r.status_code}\n\nHeaders:\n{r.headers}"
except Exception as e:
    content = f"Erreur lors de la connexion HTTPS : {e}"

with open(html_path, "w") as f:
    f.write("<h1>Test HTTPS</h1><pre>")
    f.write(content)
    f.write("</pre>")

encrypt_file(html_path)
