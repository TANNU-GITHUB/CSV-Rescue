FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN useradd -m -u 10001 appuser
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app ./app
COPY backend/benchmarks ./benchmarks
COPY --from=web /web/dist ./static
ENV STATIC_DIR=/srv/static DATA_DIR=/data
RUN mkdir -p /data && chown -R appuser:appuser /data
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD ["python","-m","app.healthcheck"]
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
