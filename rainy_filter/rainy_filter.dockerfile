FROM ubuntu:20.04

RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika

# CMD python3 /app/worker/main.py
ENTRYPOINT [ "python3", "/app/rainy_filter/main.py" ]