FROM python:3.11-slim
WORKDIR /app

ARG SERVICE_PATH
ENV SERVICE_PATH=${SERVICE_PATH}

COPY ${SERVICE_PATH}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ${SERVICE_PATH}/app ./app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]

