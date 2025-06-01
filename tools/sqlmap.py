import subprocess, sys, os

def run_sqlmap(target, timestamp):
    output_file = f"reports/sqlmap_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "python3", "/opt/sqlmap/sqlmap.py", "-u", target, "--batch"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur SQLmap : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_sqlmap(sys.argv[1], sys.argv[2])
