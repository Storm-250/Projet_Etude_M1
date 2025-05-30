import sys, subprocess, os

target, timestamp = sys.argv[1], sys.argv[2]
xml_file = f"scan_{timestamp}.xml"
report = f"reports/nmap_{timestamp}.txt"

subprocess.run(["nmap", "-sV", "-oX", xml_file, target])
with open(report, "w") as f:
    f.write(f"Nmap scan saved as {xml_file}. Import into Metasploit using:\n")
    f.write(f"msfconsole > db_import {xml_file}\n")
