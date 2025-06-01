# tools/nikto.py
import subprocess
import sys
from datetime import datetime
import os

def run_nikto(target, timestamp):
    output_file = f"reports/nikto_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run(["nikto", "-h", target], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur lors de l'exécution de Nikto : {e}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 nikto.py <target> <timestamp>")
        sys.exit(1)

    target = sys.argv[1]
    timestamp = sys.argv[2]
    os.makedirs("reports", exist_ok=True)
    run_nikto(target, timestamp)
