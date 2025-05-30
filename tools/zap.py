import sys, subprocess

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/zap_{timestamp}.txt"

with open(report, "w") as f:
    subprocess.run(["zap-baseline.py", "-t", target], stdout=f, stderr=subprocess.STDOUT)
