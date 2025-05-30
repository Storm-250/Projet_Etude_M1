FROM python:3.10-slim

# Installer les outils système nécessaires
RUN apt-get update && apt-get install -y \
    nikto \
    hydra \
    nmap \
    curl \
    feroxbuster \
    gobuster \
    wireshark \
    zaproxy \
    sqlmap \
    && rm -rf /var/lib/apt/lists/*

# Installer Flask
RUN pip install flask

# Créer le répertoire de l’application
WORKDIR /app

# Copier le code
COPY . .

# Créer le dossier des rapports au cas où
RUN mkdir -p reports

# Exposer le port Flask
EXPOSE 5000

# Lancer le serveur Flask
CMD ["python", "app.py"]
