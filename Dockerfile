# ---------- Frontend build (Alpine) ----------
FROM node:20-alpine AS web-build
WORKDIR /web

# Force Alpine repositories to HTTPS (in case the base image has http)
RUN sed -i -e 's|http://|https://|g' /etc/apk/repositories

COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# ---------- Backend (Debian slim) ----------
FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Switch Debian APT sources to HTTPS before any apt-get
# (covers both deb.debian.org and security.debian.org)
RUN set -eux; \
    sed -i -e 's|http://deb.debian.org|https://deb.debian.org|g' \
           -e 's|http://security.debian.org|https://security.debian.org|g' \
           /etc/apt/sources.list; \
    apt-get update; \
    # ca-certificates for TLS, apt-transport-https is transitional but harmless
    apt-get install -y --no-install-recommends ca-certificates apt-transport-https; \
    # your build deps & OCR/PDF tools
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        build-essential; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/app /app/app
COPY --from=web-build /web/dist /app/static

RUN mkdir -p /app/data /app/uploads
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
