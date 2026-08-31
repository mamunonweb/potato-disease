# Project contribution guide

## Project purpose

This project detects potato leaf diseases with an explainable Keras/TensorFlow
CNN and provides practical disease information, causes, solutions, and chat
assistance.

## Target architecture

The application is being migrated from its original Streamlit interface to a
client/server application:

- `backend/`: FastAPI services, model inference, Grad-CAM, PDF generation, and
  server-side LLM integration.
- `frontend/`: React, TypeScript, Vite, shadcn/ui, and TanStack Query.
- TensorFlow/Keras remains in Python because the existing `.keras` model and
  explainability pipeline depend on the Python ML ecosystem.
- Bun is intended for frontend package management and scripts. It may be used
  for future JavaScript services only when that does not require moving the
  TensorFlow inference workload out of Python.

During migration, keep the existing Streamlit application working until the
FastAPI/React replacement has been verified. Do not remove or disable the old
entry point as part of an unrelated change.

## Development conventions

- Keep API routes, business logic, model logic, and presentation code in
  separate modules.
- Validate uploaded files by type and size before processing them.
- Keep model loading lazy and cached so the model is loaded once per worker.
- Do not expose API keys, stack traces, filesystem paths, or internal model
  details in API responses.
- Keep prediction and guidance responses explicit about confidence and about
  the fact that agricultural guidance is not a definitive diagnosis.
- Use environment variables for secrets and deployment-specific settings.
- Keep `.env` local and uncommitted; update `.env.example` when a new setting
  is introduced.
- Pin runtime dependencies and update lockfiles when package versions change.
- Prefer small, focused changes with tests or a reproducible verification step.

## Container and deployment rules

- The production deployment uses Docker Compose and joins the existing external
  Traefik network named `proxy`.
- The application should not create or manage the shared Traefik instance.
- Keep server-specific hostnames, certificate settings, and secrets out of the
  repository.
- Preserve health-check endpoints for both the backend and frontend/service
  stack.

## Git and naming

- Use descriptive branch and commit names supplied by the project owner or
  agreed for the specific task.
- Never add references, attribution, branding, or naming associated with
  Codex, OpenAI, or ChatGPT to this project.
- Before committing, inspect the diff and confirm that secrets and generated
  build artifacts are not included.

## Useful verification

At minimum, verify changed areas with the relevant formatter, type checker,
tests, or container build. For API changes, check the health endpoint and one
representative prediction request. For frontend changes, run the production
build and confirm the API URL is configurable through the environment.
