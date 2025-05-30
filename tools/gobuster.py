import sys, subprocess

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/gobuster_{timestamp}.txt"

with open(report, "w") as f:
    subprocess.run([
        "gobuster", "dir", "-u", target,
        "-w", "/usr/share/wordlists/dirb/common.txt"
    ], stdout=f, stderr=subprocess.STDOUT)
