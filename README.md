# A Lightweight Explainable CNN Model for Potato Plant Disease Detection

## Overview

This project presents a deep learning solution for the automated classification
of potato leaf conditions. A **custom explainable lightweight CNN** is trained
on a seven-class dataset and served through the FastAPI + React application.

The application is a FastAPI + React client/server stack. The CNN predicts the
leaf condition, **Grad-CAM** heatmaps show exactly where the model looked, and
an AI assistant powered by OpenRouter provides practical disease information,
causes, solutions, and chat guidance.

## Key features

* **Multi-class classification:** classifies bacterial, fungal, healthy,
  nematode, pest, Phytophthora, and viral categories.
* **Lightweight architecture:** the proposed custom CNN has only **0.65M
  parameters** (vs. ~24M in ResNet50), making it suitable for edge deployment.
* **Explainable AI:** Grad-CAM heatmaps highlight the infected leaf regions
  the model focused on, with an estimated attention severity.
* **Single and batch analysis:** predict one image or up to 12 at once, with
  per-image results and CSV export.
* **Camera capture:** take the leaf photo directly in the browser.
* **PDF report:** downloadable report with prediction, Grad-CAM overlay,
  top-3 probabilities, and disease guidance.
* **AI guidance and chat:** OpenRouter-generated disease information with an
  automatic fallback to built-in guidance when the service is unavailable.

## Model status

The training notebook is configured for the current seven-class dataset. Test
metrics will be recorded after the new Kaggle training run; metrics from the
previous three-class experiment are intentionally not presented as current
results.

## Dataset

The repository contains a class-organized potato leaf dataset for the current
seven-class training experiment.

* **Total images:** 3,076
* **Classes:** 7 (`Bacteria`, `Fungi`, `Healthy`, `Nematode`, `Pest`,
  `Phytopthora`, and `Virus`)
* **Augmentation:** rotation, zoom, flip (on-the-fly)

## Architecture

| Service | Purpose | Port |
| :--- | :--- | :--- |
| `potato-disease-frontend` | React SPA (Vite, TypeScript, shadcn/ui, TanStack Query) served by nginx | 80 (host 8080) |
| `potato-disease-backend` | FastAPI: prediction, Grad-CAM, PDF reports, OpenRouter chat | 8000 |

TensorFlow/Keras inference stays in the Python backend because the existing
`.keras` model and the Grad-CAM pipeline depend on the Python ML ecosystem.

```
backend/    FastAPI app (routes, services, schemas, config)
frontend/   React SPA (Vite, TypeScript, shadcn/ui, TanStack Query)
dataset/    class-organized images used by the training notebook
```

API endpoints:

| Method | Path | Purpose |
| :--- | :--- | :--- |
| GET | `/health`, `/health/ready` | Liveness / model readiness |
| POST | `/api/predict` | Single-image prediction + Grad-CAM |
| POST | `/api/predict/batch` | Batch prediction (max `MAX_BATCH_FILES`) |
| POST | `/api/report` | PDF report for one image |
| POST | `/api/chat` | Disease-aware streaming chat assistant |

## Local development

Run the full stack in Docker (frontend on http://localhost:8080, API proxied
same-origin through nginx):

```bash
cp .env.example .env   # then fill in OPENROUTER_API_KEY (optional)
docker compose up -d --build
```

Or run the pieces separately:

```bash
# FastAPI backend (http://localhost:8000)
docker compose up -d potato-disease-backend

# React dev server (http://localhost:5173)
cd frontend && bun install && bun run dev
```

The frontend reads the API base URL from `VITE_API_BASE_URL` at build time.
When unset it calls the API same-origin via `/api`, which works with the
nginx proxy in the full-Docker setup and with the Traefik routing described
below.

## Production deployment with Docker and Traefik

The production setup assumes Traefik is already running on the server and
uses an external Docker network named `proxy` with a certificate resolver
named `letsencrypt`.

Routing uses a single domain so the browser talks to the API same-origin:

* `https://potato.example.com/` → React frontend
* `https://potato.example.com/api/...` → FastAPI backend (rate-limited)

1. **Prepare the production override**
   ```bash
   cp .env.example .env
   cp compose.prod.example.yaml compose.prod.yaml
   ```

2. **Configure environment variables and hostname**

   Edit `.env` and set `OPENROUTER_API_KEY` to your real key. Do not commit
   `.env`.

   Edit `compose.prod.yaml` and replace `potato.example.com` with the DNS
   name that points to the server. For Open Graph link previews (social
   messengers), also add the site URL to `.env`; compose passes it to the
   frontend build automatically:
   ```bash
   VITE_SITE_URL=https://potato.example.com
   ```

3. **Confirm the Traefik network exists**
   ```bash
   docker network inspect proxy
   ```

4. **Build and start the application**
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml up -d --build
   ```

The production override removes the direct host port mappings and exposes the
services only through Traefik over HTTPS. Both local and production Compose
configurations load the backend container environment from `.env`.

Useful commands:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps
docker compose -f compose.yaml -f compose.prod.yaml logs -f potato-disease-backend
docker compose -f compose.yaml -f compose.prod.yaml down
```

Do not commit `compose.prod.yaml` or `.env`; they are ignored because they
contain server-specific hostnames, keys, and deployment configuration.

## OpenRouter-generated guidance

The Disease Information, Causes & Solutions pages, and the chat assistant can
use OpenRouter to generate current guidance from the predicted disease class.
The CNN remains responsible for the prediction, while the built-in disease
information is used automatically if OpenRouter is unavailable, rate-limited,
or not configured.

Set the API key in `.env` without committing it to the repository:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
```

The generated guidance is cached for 24 hours (`GUIDANCE_TTL_SECONDS`) and is
limited to symptoms, causes, actions, and prevention information. It should be
treated as general guidance, not as a definitive diagnosis or a substitute for
local agricultural advice. All predictions and reports in the application
carry the same disclaimer.

## Explainable AI (Grad-CAM)

Grad-CAM was used to validate the model. The heatmaps below show that the
model correctly focuses on the **lesions and spots** on the leaves rather than
the background.

<img
  width="1452"
  height="1489"
  alt="Grad-CAM heatmap on a diseased potato leaf"
  src="https://github.com/jahangirhossain5/A-Lightweight-Explainable-CNN-Model-for-Potato-Plant-Disease-Detection/blob/a263fcbb8dc8b6d593ff9122b454121c99157e1a/Pred-Image.png"
/>

## Contributors

This project was developed by:

* **Jahangir Hossain Sohag** (Team Leader & Lead Developer)
* **Al-Mamun** (Data Engineer)
* **Tarikul Islam Sourav** (AI Analyst)
* **Moniruzzaman** (Technical Writer)
* **Farhana Yeasmin** (Visual Designer)
