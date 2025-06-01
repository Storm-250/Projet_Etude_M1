FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl wget git unzip gnupg \
    hydra nmap gobuster sqlmap \
    && rm -rf /var/lib/apt/lists/*

# Installer Nikto
RUN git clone https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

# Installer Feroxbuster
RUN wget https://github.com/epi052/feroxbuster/releases/download/v2.11.0/feroxbuster_amd64.deb.zip \
    && unzip feroxbuster_amd64.deb.zip \
    && apt-get install -y ./feroxbuster_2.11.0-1_amd64.deb \
    && rm feroxbuster_amd64.deb.zip feroxbuster_2.11.0-1_amd64.deb

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]
