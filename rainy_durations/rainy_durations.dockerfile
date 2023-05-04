FROM ubuntu:20.04

RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika

ENTRYPOINT [ "python3", "/app/rainy_durations/main.py" ]