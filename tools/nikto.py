import sys, subprocess, os

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/nikto_{timestamp}.txt"
with open(report, "w") as f:
    subprocess.run(["nikto", "-h", target], stdout=f, stderr=subprocess.STDOUT)
