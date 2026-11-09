# Task 3 image. CPU-only torch wheel (no CUDA libs) keeps the image under 2 GB.
# The model weights are NOT in the image; the service downloads them from object storage at start-up.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
COPY service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY service/app.py service/model_runner.py service/schema.json /app/
COPY worker/storage.py /app/worker/storage.py

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
