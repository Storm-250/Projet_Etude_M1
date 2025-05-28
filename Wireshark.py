import subprocess

# Commande pour capturer 30 secondes sur l'interface 1 et sauvegarder dans capture.pcap
commande = [
    'tshark',        # Utilise tshark (doit être installé)
    '-i', '1',       # Interface réseau (à adapter selon ta config, ex: 'eth0', 'Wi-Fi')
    '-a', 'duration:30',  # Capture pendant 30 secondes
    '-w', 'capture.pcap'  # Sauvegarde le fichier ici
]

try:
    print("Capture démarrée pendant 30 secondes...")
    subprocess.run(commande, check=True)
    print("Capture terminée. Fichier sauvegardé : capture.pcap")
except subprocess.CalledProcessError as e:
    print(f"Erreur pendant la capture : {e}")
