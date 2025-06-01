import subprocess, sys, os

def run_gobuster(target, timestamp):
    output_file = f"reports/gobuster_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "gobuster", "dir", "-u", target, "-w", "/usr/share/wordlists/dirb/common.txt"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur Gobuster : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_gobuster(sys.argv[1], sys.argv[2])
