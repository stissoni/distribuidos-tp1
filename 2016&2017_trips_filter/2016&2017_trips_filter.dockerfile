FROM python:3.11-slim-bullseye

RUN pip3 install pika

# CMD python3 /app/worker/main.py
ENTRYPOINT [ "python3", "/app/2016&2017_trips_filter/main.py" ]