# Inputs: /backend build context containing requirements.txt and the backend Python files.
# Outputs: OCI image exposing the FastAPI ASGI service on TCP port 8000.
# Explanation: Installs backend dependencies and starts uvicorn; it does not run migrations or create external services during build.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY . /app/backend
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
