# Deployment

## Frontend

Build static assets:

```bash
npm run build
```

The compiled app is emitted to:

```text
frontend/dist
```

Deploy it to any static host. Configure `VITE_API_BASE_URL` if the API is hosted elsewhere.

## Backend

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python main.py
```

Production example:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Keep the `data/processed` directory beside the deployed backend unless you configure a custom data path.
