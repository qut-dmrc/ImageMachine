FROM ubuntu:18.04

WORKDIR /im

RUN apt-get update -y && \
        apt-get install -y python3.7 --version && \
        apt-get install -y python3-pip

COPY requirements.txt .

RUN export LC_ALL=C.UTF-8 && \
        . ~/.bashrc && \
        pip3 install --upgrade pip && \
        pip3 --no-cache-dir install -r requirements.txt

COPY . .

