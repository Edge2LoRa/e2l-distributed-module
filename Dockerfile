FROM python:3.11.6-alpine3.18

WORKDIR /home

RUN apk update && apk add --no-cache make protobuf-dev g++ python3-dev libffi-dev openssl-dev && mkdir e2l-dm

WORKDIR /home/e2l-dm

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY e2gw_rpc_client/ e2gw_rpc_client/
COPY e2l_module/ e2l_module/
COPY mqtt_module/ mqtt_module/
COPY protos/ protos/
COPY rpc_module/ rpc_module/
COPY main.py main.py
COPY VERSION VERSION
COPY docker.env .env

ENV DEBUG=1

CMD ["python3", "main.py"]
