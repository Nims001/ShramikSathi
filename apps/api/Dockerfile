# FastAPI backend image. Python 3.12 for broad wheel availability.
FROM python:3.12-slim

# tesseract + Nepali language pack for the contract-OCR feature.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-nep libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the embedding model so the first "Analyse with AI" request
# doesn't stall on a model download at runtime. Skip-safe: the model is also
# fetched lazily on first use if this step is skipped.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')" || true

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
