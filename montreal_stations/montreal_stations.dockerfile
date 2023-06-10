FROM python:3.11-slim-bullseye

RUN pip3 install pika
RUN pip3 install haversine

ENTRYPOINT [ "python3", "/app/montreal_stations/main.py" ]