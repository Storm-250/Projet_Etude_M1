FROM ubuntu


RUN apt-get update && apt-get install --no-install-recommends -y \
        python3 \
        curl \
    apt-get clean && clean rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install/sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
