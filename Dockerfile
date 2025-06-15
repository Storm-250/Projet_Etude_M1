FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl wget git unzip gnupg \
    hydra nmap gobuster sqlmap \
    net-tools procps \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer Nikto
RUN git clone https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

# Installer Feroxbuster
RUN wget https://github.com/epi052/feroxbuster/releases/download/v2.11.0/feroxbuster_amd64.deb.zip \
    && unzip feroxbuster_amd64.deb.zip \
    && apt-get update && apt-get install -y ./feroxbuster_2.11.0-1_amd64.deb \
    && rm feroxbuster_amd64.deb.zip feroxbuster_2.11.0-1_amd64.deb

# Créer les dossiers nécessaires
WORKDIR /app
RUN mkdir -p tools rapports reports

# Copier les fichiers de requirements d'abord (pour le cache Docker)
COPY requirements.txt /app/

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les autres fichiers
COPY . /app

# Créer les fichiers par défaut s'ils n'existent pas
RUN if [ ! -f MDP.json ]; then echo '{"password": "changeme"}' > MDP.json; fi

# Permissions
RUN chmod +x tools/*.py 2>/dev/null || true

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/login || exit 1

CMD ["python", "app.py"]