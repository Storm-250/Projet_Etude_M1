import subprocess, sys, os

def run_nmap(target, timestamp):
    output_file = f"reports/nmap_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "nmap", "-sV", "--script", "vuln", target
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur Nmap : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_nmap(sys.argv[1], sys.argv[2])
