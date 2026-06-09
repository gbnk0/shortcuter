FROM node:22-alpine AS ui-build
WORKDIR /src/ui
ARG VITE_APP_VERSION=dev
COPY ui/package*.json ./
RUN npm ci
COPY ui/ ./
RUN VITE_APP_VERSION=$VITE_APP_VERSION npm run build

FROM python:3.13-slim AS runtime
WORKDIR /app
ARG VITE_APP_VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHORTCUTER_VERSION=$VITE_APP_VERSION

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY api/app /app/api/app
COPY shortcuts.example.yaml /app/shortcuts.yaml
COPY --from=ui-build /src/ui/dist /app/ui/dist

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
