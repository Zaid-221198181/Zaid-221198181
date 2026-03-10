# Marketplace Backend

FastAPI backend for the Seller & Buyer marketplace apps.

## Local Development
```bash
cd marketplace-backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Deploy to Render
1. Push to GitHub
2. Go to https://render.com → New → Blueprint
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and set up everything

## API Docs
Visit `/docs` for interactive Swagger UI.
