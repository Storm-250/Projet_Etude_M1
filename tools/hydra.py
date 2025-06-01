import subprocess, sys, os

def run_hydra(target, timestamp):
    output_file = f"reports/hydra_{timestamp}.txt"
    try:
        with open(output_file, "w") as f:
            subprocess.run([
                "hydra", "-L", "user.txt", "-P", "pass.txt", target, "ssh"
            ], stdout=f, stderr=subprocess.STDOUT)
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Erreur Hydra : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    run_hydra(sys.argv[1], sys.argv[2])
