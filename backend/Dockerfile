FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# TensorFlow is large and rarely changes: keep it in its own cached layer
# so app-dependency or code changes do not reinstall it.
COPY backend/requirements.tf.txt /app/backend/requirements.tf.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /app/backend/requirements.tf.txt

COPY backend/requirements.txt /app/backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /app/backend/requirements.txt

COPY backend /app/backend
COPY explainable_cnn_model.keras /app/explainable_cnn_model.keras

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
