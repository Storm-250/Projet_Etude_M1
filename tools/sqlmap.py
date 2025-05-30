import sys, subprocess

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/sqlmap_{timestamp}.txt"

with open(report, "w") as f:
    subprocess.run(["sqlmap", "-u", target, "--batch"], stdout=f, stderr=subprocess.STDOUT)
