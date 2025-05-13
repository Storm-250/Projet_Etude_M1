FROM nginx:1.10.1-alpine


RUN apt-get update && apt-get install -y metasploit-framework
