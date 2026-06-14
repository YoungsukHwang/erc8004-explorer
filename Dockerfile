# Streamlit on Cloud Run.
# Cloud Run injects $PORT (default 8080). We bind Streamlit to it.

FROM python:3.12-slim

WORKDIR /app

# Install deps first so the layer caches across code edits
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app/ ./app/

ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080

# Cloud Run sends SIGTERM on shutdown; streamlit handles it cleanly
CMD streamlit run app/app.py \
    --server.address=0.0.0.0 \
    --server.port=$PORT \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
