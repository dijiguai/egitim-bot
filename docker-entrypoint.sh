#!/bin/sh
set -e

# Google credentials.json dosyasını environment variable'dan oluştur
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /app/credentials.json
    echo "[startup] credentials.json oluşturuldu."
else
    echo "[startup] UYARI: GOOGLE_CREDENTIALS_JSON tanımlı değil!"
fi

# durum.json yoksa boş oluştur (ilk çalıştırma)
if [ ! -f /app/durum.json ]; then
    echo "{}" > /app/durum.json
    echo "[startup] durum.json oluşturuldu."
fi

# PORT tanımlı değilse 8081 kullan (8080 çakışma riski)
export PORT="${PORT:-8081}"

echo "[startup] Bot başlatılıyor... (PORT=$PORT)"
exec python3 bot.py
