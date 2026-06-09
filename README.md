# Shortcuter

Read-only shortcuts dashboard backed by a YAML file. The Docker image serves both the FastAPI backend and the Vue frontend.

## Quick Start

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8000
```

By default, Compose runs with the bundled `shortcuts.example.yaml`.

## Configure

Create your private local config:

```bash
cp shortcuts.example.yaml shortcuts.yaml
```

Then edit `docker-compose.yml` and switch the mounted file:

```yaml
volumes:
  - ./shortcuts.yaml:/shortcuts.yaml:ro
```

`shortcuts.yaml` is ignored by Git.

Minimal YAML:

```yaml
general:
  title: Shortcuter
  subtitle: Internal apps and services
  rubrique: Links
  accent: green
  show_all_tab: true

pages:
  - title: General
    subtitle: Daily quick access
    rubrique: Home
    accent: green
    shortcuts:
      - name: Kibana
        url: https://kibana.example.lan
        group: Monitoring
        description: Dashboards and metrics
        icon: homarr/kibana
```

Icon values can be:

- `auto`
- a Material Design Icons class, such as `mdi-server`
- a Homarr Labs icon, such as `homarr/kibana`
- an image URL

Optional shortcut badge:

```yaml
badge:
  icon: mdi-hammer-wrench
  tooltip: Maintenance in progress
```

## Local Development

API:

```bash
cd api
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

UI:

```bash
cd ui
npm install
VITE_API_URL=http://localhost:8000 npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`.

## Docker Hub Publishing

GitHub Actions publishes the image to Docker Hub on pushes to `main`, on `v*` tags, and from manual workflow runs.

Required GitHub repository secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

Published tags include `latest`, Git tags such as `v0.4.0`, semver aliases such as `0.4.0` and `0.4`, and `sha-...`.
