import subprocess, sys, os

def run_https_test(target, timestamp):
    output_file = f"reports/https_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run(["curl", "-Iv", target], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur curl : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_https_test(sys.argv[1], sys.argv[2])
