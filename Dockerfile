# ---------- Etapa 1: compila el dashboard (React + TypeScript) ----------
FROM node:22-alpine AS dashboard
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Etapa 2: API, agentes, ontología y lógica difusa ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ontologia/ ontologia/
COPY fuzzy/ fuzzy/
COPY agentes/ agentes/
COPY persistencia/ persistencia/
COPY api/ api/
COPY --from=dashboard /app/frontend/dist frontend/dist

# No ejecutar como administrador dentro del contenedor
RUN useradd --create-home ontoaudit
USER ontoaudit

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/salud')"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]