FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY taximetro/ taximetro/
COPY web/ web/
COPY config.json ./

EXPOSE 5000

# Un solo worker: el taxímetro en curso vive en la memoria del proceso.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "taximetro.api:create_app()"]
