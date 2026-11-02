FROM python:3.12-alpine
LABEL MAINTAINER="PUT YOUR EMAIL HERE"

RUN  pip3 install redis==8.1.0

WORKDIR /srv
COPY    logs.py /srv
CMD [ "python3", "logs.py"]
