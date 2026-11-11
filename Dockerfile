FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 \
    USER_DB_PATH=/data/users.sqlite3
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && install -d -o 10001 -g 10001 /data
COPY app ./app
USER 10001:10001
EXPOSE 5001
CMD ["python", "-m", "app.main"]
