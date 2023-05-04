FROM ubuntu:20.04

RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika
RUN pip3 install haversine

ENTRYPOINT [ "python3", "/app/montreal_stations/main.py" ]