import subprocess, sys, os

def run_zap(target, timestamp):
    output_file = f"reports/zap_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "python3", "/opt/zap/zap-baseline.py", "-t", target, "-r", f"zap_{timestamp}.html"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur ZAP : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_zap(sys.argv[1], sys.argv[2])
