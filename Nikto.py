import subprocess

target_url = "http://example.com"
command = ["nikto", "-h", target_url]

try:
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    proc.wait(timeout=30)  # Attend 30 secondes max
    output, errors = proc.communicate()
    print(output)
except subprocess.TimeoutExpired:
    print("⏱️ Temps limite atteint, arrêt du scan...")
    proc.kill()  # Termine le processus Nikto
    output, errors = proc.communicate()
    print("Sortie partielle :")
    print(output)
