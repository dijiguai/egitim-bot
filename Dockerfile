FROM python:3.11-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Önce sadece requirements — layer cache için
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kaynak kodu kopyala
COPY . .

# credentials.json'ı environment variable'dan oluşturacak startup scripti
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Port (Flask panel için) — 8081 kullanıyoruz, 8080 çakışma riski olmasın
EXPOSE 8081

ENTRYPOINT ["/docker-entrypoint.sh"]
