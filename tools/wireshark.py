from datetime import datetime
from encrypt import encrypt_file

date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"rapport/wireshark_{date}.html"

fake_report = "<html><body><h1>Wireshark Simulation</h1><p>Simulated network traffic report.</p></body></html>"

with open(file_path, "w") as f:
    f.write(fake_report)

encrypt_file(file_path)
