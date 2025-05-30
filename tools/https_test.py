import sys, subprocess

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/https_test_{timestamp}.txt"

with open(report, "w") as f:
    subprocess.run(["curl", "-k", "-I", target], stdout=f, stderr=subprocess.STDOUT)
