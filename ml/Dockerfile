FROM python:3.7.10

WORKDIR /im

RUN apt-get update && \
        apt-get upgrade -y

COPY requirements.txt .


RUN  echo "export LC_ALL=C.UTF-8" >> /root/.bashrc && \
        . ~/.bashrc

RUN python3 -m pip --no-cache-dir install -r requirements.txt

COPY . .

