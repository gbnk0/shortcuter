# Raccourcis

Application Vue.js + FastAPI en lecture seule pour afficher des raccourcis declares dans un YAML.

## YAML

Modifier les raccourcis dans:

```text
api/shortcuts.yaml
```

Ce fichier est volontairement ignore par Git. Pour demarrer depuis un exemple:

```bash
cp api/shortcuts.example.yaml api/shortcuts.yaml
```

Format:

```yaml
general:
  title: General
  subtitle: Applications et services internes
  rubrique: General
  accent: green
  download-icons: true
  show_all_tab: true
  all_tab_accent: slate

pages:
  - title: General
    subtitle: Applications et services internes
    rubrique: General
    accent: green
    shortcuts:
      - name: Kibana
        url: https://kibana.example.lan
        group: Monitoring
        description: Dashboards et metriques
        icon: homarr/kibana

  - title: Infra
    subtitle: Services d'infrastructure
    rubrique: Exploitation
    accent: blue
    shortcuts: []
```

`icon` accepte:

- `auto` ou champ absent: detection automatique via HTML/manifest, avec fallback `https://host/favicon.ico`;
- une classe Material Design Icons, par exemple `mdi-server`;
- une icone Homarr Labs live, par exemple `homarr/kibana`;
- une URL d'image, par exemple `https://assets.example.lan/icon.png`.

Un raccourci peut afficher une petite icone superposee avec tooltip:

```yaml
badge:
  icon: mdi-hammer-wrench
  tooltip: Maintenance en cours
```

Les `id` ne se declarent pas dans le YAML: l'API genere des identifiants stables pour les pages et les raccourcis.

Les raccourcis se declarent directement dans `pages[].shortcuts`.

`accent` accepte une couleur nommee: `green`, `blue`, `orange`, `purple`, `pink`, `red`, `cyan`, `yellow`, `slate`. Les valeurs hex comme `#16807a` restent acceptees.

En mode `auto`, l'API ignore la validation TLS des certificats pour recuperer les icones, choisit la plus grande taille declaree, puis stocke l'image dans `api/icon-cache`. Le front utilise ensuite l'icone locale servie par l'API au lieu de la recuperer a chaque affichage.

Avec `general.download-icons: true`, l'API telecharge au demarrage les icones Homarr Labs en cache local dans `api/icon-cache`. Le demarrage HTTP reste disponible pendant le telechargement; les icones basculent vers `/icons/...` au fur et a mesure du cache.

Avec `general.show_all_tab: true`, l'UI ajoute un onglet `Tous` qui affiche les raccourcis de toutes les pages.

`general.all_tab_accent` permet de choisir la couleur de l'onglet `Tous`; si absent, il reprend `general.accent`.

## API

```bash
cd raccourcis/api
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Le projet utilise les versions epinglees de FastAPI/Pydantic dans `requirements.txt`.
Sur macOS avec Homebrew, utiliser `python3.13`: Python 3.14 est trop recent pour
ces dependances.

Endpoints:

- `GET /health`
- `GET /shortcuts`
- `GET /builtin-icons`

Routes UI:

- `/page/<id-genere>` pour une page de raccourcis;
- `/icons` pour les icones disponibles.

## Docker

L'image Docker sert l'API et le build Vue sur le port `8000`.

```bash
docker build -t raccourcis .
docker run --rm -p 8000:8000 \
  -v "$PWD/api/shortcuts.yaml:/app/api/shortcuts.yaml:ro" \
  -v raccourcis-icon-cache:/app/api/icon-cache \
  raccourcis
```

Un compose d'exemple est fourni:

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

Sans montage de `api/shortcuts.yaml`, l'image utilise `api/shortcuts.example.yaml` comme configuration par defaut.

## UI

```bash
cd raccourcis/ui
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Le front appelle directement l'API sur le meme host en port `8000`.

Exemple: si la page est ouverte sur `http://localhost:5173`, les appels API partent vers `http://localhost:8000`.

Pour forcer une autre adresse API:

```bash
VITE_API_URL=http://api.example.lan:8000 npm run dev -- --host 0.0.0.0 --port 5173
```
