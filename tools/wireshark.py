import sys, os

def simulate_wireshark(timestamp):
    output_file = f"reports/wireshark_{timestamp}.txt"
    with open(output_file, "w") as f:
        f.write("Wireshark simulation : capture réseau non disponible dans Docker\n")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(1)
    simulate_wireshark(sys.argv[2])
