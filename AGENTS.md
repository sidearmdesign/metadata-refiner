# Repository Guidelines

## Project Structure & Module Organization
- Backend: `app.py` (Flask + Socket.IO), config via `.env`, profiles in `profiles.json`.
- Desktop shell: `main.js` (Electron main process). Packs Flask and static assets with `electron-builder`.
- UI: `templates/index.html` and `static/` (images, resources). Uploads stored under `static/images/`.
- Packaging: `package.json` (Electron scripts), `requirements.txt` (Python deps), `Dockerfile` for web deployment.

## Build, Test, and Development Commands
- Desktop (Electron):
  - `npm install` then `pip install -r requirements.txt`
  - Run: `npm start` (prod-like), `npm run dev` (with DevTools)
  - Build: `npm run build-mac | build-win | build-linux | build-all`
- Web/Backend only:
  - `pip install -r requirements.txt` then `python app.py` (serves at `http://127.0.0.1:5001`)
- Docker:
  - Build: `docker build -t mdr .`
  - Run: `docker run -p 5001:5001 --name=metadata-refiner mdr`

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indent, snake_case for files/functions, add type hints in new code.
- JavaScript: 2‑space indent, camelCase for vars/functions, PascalCase for classes.
- Keep modules small; prefer pure helpers over inlining. Place new Flask routes in `app.py` with clear docstrings.
- No linters configured; format consistently with existing files. Avoid introducing new frameworks unless justified.

## Testing Guidelines
- No automated tests exist yet. For changes, verify:
  - Image upload (valid/invalid, ≤10MB) and preview rendering
  - Metadata generation flow (Socket.IO events, error handling without API key)
  - CSV export path handling (with/without Base Path setting)
- If adding tests, prefer `pytest` for Python (place under `tests/`, name `test_*.py`). Keep fast and deterministic.

## Commit & Pull Request Guidelines
- Commits: short, imperative, scoped where useful. Examples:
  - `feat(ui): add cost estimate toggle`
  - `fix(backend): set category to "Other" when invalid`
- PRs: include purpose, linked issues, steps to reproduce/test, screenshots (UI), and platform tested (Desktop/Web/Docker).

## Security & Configuration Tips
- Never commit secrets. Use `.env` (copy from `.env.example`): `OPENAI_API_KEY`, `SECRET_KEY`.
- Electron spawns Flask on an available port (5001–5099); app binds to `127.0.0.1`.
- Respect profile rules in `profiles.json`; keep categories in sync with the UI.

