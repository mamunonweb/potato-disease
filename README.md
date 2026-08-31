# 🌿 A Lightweight Explainable CNN Model for Potato Plant Disease Detection


## 📜 Overview
This project presents a Deep Learning-based solution for the automated detection of plant diseases. We developed a **Custom Explainable Lightweight CNN** and compared its performance against industry-standard Transfer Learning models (**ResNet50** and **MobileNetV2**) on the **🌱 Potato Plant Diseases Data 🍂** (3 classes).

To ensure trust and transparency, we integrated **Explainable AI (Grad-CAM)** to visualize the decision-making process. The final model is deployed as a user-friendly **Streamlit Web Application**.

## 🚀 Live Demo
Check out the live web application here:
https://a-lightweight-explainable-cnn-model-for-potato-plant-disease-d.streamlit.app/


## ✨ Key Features
* **Multi-Class Classification:** Detects 3 different disease classes across potato crop species.
* **Lightweight Architecture:** Proposed Custom CNN has only **0.65M parameters** (vs. 24M in ResNet50), making it suitable for mobile/edge deployment.
* **High Accuracy:** Achieved **98.71% test accuracy** with the Custom CNN.
* **Explainable AI (XAI):** Uses **Grad-CAM** heatmaps to highlight infected leaf regions, verifying the model's focus.
* **Interactive Web App:** Built with Streamlit for real-time inference.

## 📊 Model Comparison

| Model | Test Accuracy | Test Loss | Parameters | Remarks |
| :--- | :--- | :--- | :--- | :--- |
| **Custom CNN** | **98.71%** | **0.7809** | **~0.65 M** | **Best Trade-off (Lightweight & Accurate)** |
| ResNet50 | 98.67% | 0.7833 | ~24 M | High computational cost |
| MobileNetV2 | 96.19% | 0.8603 | ~2.6 M | Standard lightweight baseline |

## 🛠️ Tech Stack
* **Deep Learning:** TensorFlow, Keras
* **Data Processing:** NumPy, Pandas, OpenCV
* **Visualization:** Matplotlib, Seaborn
* **Web Framework:** Streamlit
* **Deployment:** Streamlit Cloud

## 📂 Dataset
The dataset used is the **🌱 Potato Plant Diseases Data 🍂**, originally collected by Hafiz Nouman, Pakistan.
* **Total Images:** 2,305
* **Classes:** 3 (Disease + Healthy)
* **Augmentation:** Rotation, Zoom, Flip (On-the-fly)

## ⚙️ Installation & Usage

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/jahangirhossain5/A-Lightweight-Explainable-CNN-Model-for-Potato-Plant-Disease-Detection
    cd your-repo-name
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App Locally**
    ```bash
    streamlit run app.py
    ```

### React + FastAPI stack (in migration)

```bash
# FastAPI backend in Docker (serves http://localhost:8000)
docker compose up -d potato-disease-backend

# React frontend dev server (serves http://localhost:5173)
cd frontend && bun install && bun run dev
```

The full stack (including the nginx-served frontend on
http://localhost:8080) can also run entirely in Docker:

```bash
docker compose up -d --build
```

## 🚢 Production Deployment with Docker and Traefik

The stack runs as three Compose services:

| Service | Purpose | Port |
| :--- | :--- | :--- |
| `potato-disease-frontend` | React SPA served by nginx | 80 |
| `potato-disease-backend` | FastAPI (prediction, Grad-CAM, chat) | 8000 |
| `potato-disease-app` | Legacy Streamlit app (until the new stack is verified) | 8501 |

The production setup assumes that Traefik is already running on the server and
that it uses an external Docker network named `proxy` with a certificate
resolver named `letsencrypt`.

Routing uses a single domain so the browser talks to the API same-origin:

* `https://potato.example.com/` → React frontend
* `https://potato.example.com/api/...` → FastAPI backend
* `https://potato-streamlit.example.com/` → legacy Streamlit app

1. **Prepare the production override**
   ```bash
   cp .env.example .env
   cp compose.prod.example.yaml compose.prod.yaml
   ```

2. **Configure environment variables and hostnames**

   Edit `.env` and set `OPENROUTER_API_KEY` to your real key. Do not commit
   `.env`.

   Edit `compose.prod.yaml` and replace `potato.example.com` and
   `potato-streamlit.example.com` with DNS names that point to the server.
   Make sure the hostnames are publicly resolvable and that Traefik can issue
   certificates for them.

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
configurations load their container environment from `.env`. The frontend
image bakes the API base URL at build time; with the default build argument
it calls the API same-origin via `/api`, which matches the Traefik routing.

Useful commands:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps
docker compose -f compose.yaml -f compose.prod.yaml logs -f potato-disease-backend
docker compose -f compose.yaml -f compose.prod.yaml down
```

Do not commit `compose.prod.yaml`; it is ignored because it contains the
server-specific hostnames and deployment configuration.

### OpenRouter-generated guidance

The Disease Information and Causes & Solutions pages can use OpenRouter to
generate current guidance from the predicted disease class. The CNN remains
responsible for the prediction, while the built-in disease information is used
automatically if OpenRouter is unavailable, rate-limited, or not configured.

Set the API key in `.env` without committing it to the repository:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
```

The generated guidance is cached for 24 hours and is limited to symptoms,
causes, actions, and prevention information. It should be treated as general
guidance, not as a definitive diagnosis or a substitute for local agricultural
advice.

Use **🔐 Check OpenRouter key** in the application sidebar to verify that the
configured key is accepted and active. The key itself is never displayed.

Useful commands:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps
docker compose -f compose.yaml -f compose.prod.yaml logs -f potato-disease-app
docker compose -f compose.yaml -f compose.prod.yaml down
```

Do not commit `compose.prod.yaml`; it is ignored because it contains the
server-specific hostname and deployment configuration.

## 🧠 Explainable AI (Grad-CAM)
We used **Grad-CAM** to validate our model. The heatmaps below show that the model correctly focuses on the **lesions and spots** on the leaves rather than the background.

*<img width="1452" height="1489" alt="download" src="https://github.com/jahangirhossain5/A-Lightweight-Explainable-CNN-Model-for-Potato-Plant-Disease-Detection/blob/a263fcbb8dc8b6d593ff9122b454121c99157e1a/Pred-Image.png" />*


## 👥 Contributors
This project was developed by:
* **Jahangir Hossain Sohag** (Team Leader & Lead Developer)
* **Al-Mamun** (Data Engineer)
* **Tarikul Islam Sourav** (AI Analyst)
* **Moniruzzaman** (Technical Writer)
* **Farhana Yeasmin** (Visual Designer)

---
