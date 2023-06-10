FROM python:3.11-slim-bullseye

RUN pip3 install pika
RUN pip3 install haversine

# CMD python3 /app/worker/main.py
ENTRYPOINT [ "python3", "/app/montreal_filter/main.py" ]