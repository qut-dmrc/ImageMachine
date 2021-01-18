# Filename: Dockerfile
FROM node:12.18.3

WORKDIR /viz

EXPOSE 8080

COPY ["package*.json", "/viz/"]

RUN npm install

COPY . .