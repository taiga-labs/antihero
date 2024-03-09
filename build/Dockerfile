FROM python:3.10-slim

WORKDIR /antihero_bot

RUN apt-get update && \
    apt-get install -y libpq-dev gcc curl

COPY . /antihero_bot
RUN chown -R 1000:1000 /antihero_bot

RUN pip install -r requirements.txt --no-cache-dir --no-deps

# ENTRYPOINT python runner.py