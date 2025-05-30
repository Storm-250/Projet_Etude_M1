import sys, time, subprocess, os

target, timestamp = sys.argv[1], sys.argv[2]
report = f"reports/wireshark_{timestamp}.txt"
with open(report, "w") as f:
    f.write("Wireshark doit être lancé manuellement pour capturer le trafic réseau.\n")
subprocess.Popen(["wireshark"])
