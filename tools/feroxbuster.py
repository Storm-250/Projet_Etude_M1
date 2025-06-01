import subprocess, sys, os

def run_ferox(target, timestamp):
    output_file = f"reports/feroxbuster_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "feroxbuster", "-u", target, "-w", "/usr/share/wordlists/dirb/common.txt"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur Feroxbuster : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_ferox(sys.argv[1], sys.argv[2])
