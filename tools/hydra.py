import sys, subprocess, os

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/hydra_{timestamp}.txt"
with open(report, "w") as f:
    subprocess.run([
        "hydra", "-l", "admin", "-P", "/usr/share/wordlists/rockyou.txt", f"ssh://{target}"
    ], stdout=f, stderr=subprocess.STDOUT)
