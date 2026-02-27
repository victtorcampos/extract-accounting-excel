# ── Stage 1: Build React ──────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Instala dependências primeiro (cache layer)
COPY frontend/package*.json ./
RUN npm ci

# Copia código e gera build de produção
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Backend Python + Frontend dist ───────────────────────────────────
FROM python:3.12-slim AS runtime

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    FRONTEND_DIR=/app/frontend

WORKDIR /app

# Instala dependências Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend
COPY backend/ ./

# Copia build do React do stage anterior
COPY --from=frontend-build /frontend/dist ./frontend/

# Cria pasta de dados (será sobreposta pelo volume em produção)
RUN mkdir -p /app/data

EXPOSE 8111

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8111"]
