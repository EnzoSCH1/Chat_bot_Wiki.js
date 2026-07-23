FROM python:3.12-slim

# Installation Git (pour cloner le repo)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY app.py .
COPY .env .

# Clone initial du repo Git
RUN git config --global http.sslVerify false && \
    git clone https://oauth2:clées_token_git@gitlab.exemple.com/it-team/wiki.git /tmp/git-cache

# Port
EXPOSE 5001

# Lancement
CMD ["python", "app.py"]
