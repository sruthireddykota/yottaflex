FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md .
COPY data_dictionary.md .

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main", "generate", "--output", "/app/data"]
