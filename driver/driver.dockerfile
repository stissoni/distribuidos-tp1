FROM python:3.11-slim-bullseye

RUN pip3 install pika

ENTRYPOINT [ "python3", "/app/driver/main.py" ]