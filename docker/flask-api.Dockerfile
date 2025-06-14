FROM python:3.9-slim

WORKDIR /app

COPY flask_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "src/app.py"] 