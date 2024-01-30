FROM python:3.10-slim

WORKDIR /antihero_bot

RUN apt-get update && \
    apt-get install -y libpq-dev gcc curl

COPY ./ ./
RUN chown -R 1000:1000 ./

RUN pip install -r ./requirements.txt --no-cache-dir --no-deps

# ENTRYPOINT python bot_runner.py