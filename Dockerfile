FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /getwords
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Создаем пользователя для запуска приложения (без root)
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "main.py"]