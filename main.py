import os, sys
import time
import math
import logging
from dateutil.parser import isoparse
from concurrent import futures


import grpc
from rpc_module import edge2applicationserver_pb2_grpc
from rpc_module import Edge2LoRaApplicationServer

from mqtt_module import MQTTModule
import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec

DEBUG = os.getenv('DEBUG', False)
DEBUG = True if DEBUG == '1' else False
if DEBUG:
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def check_env_vars():
    env_vars = [
        'MQTT_USERNAME', 'MQTT_PASSWORD', 'MQTT_HOST', 'MQTT_PORT',
        'MQTT_TOPIC'
    ]
    for var in env_vars:
        if os.getenv(var) is None:
            log.error(f"{var} not set")
            exit(1)
        if "_PORT" in var:
            if not os.getenv(var).isnumeric():
                log.error(f"{var} must be numeric")
                exit(1)
            if int(os.getenv(var)) < 0 or int(os.getenv(var)) > 65535:
                log.error(f"{var} must be between 0 and 65535")
                exit(1)
    return True


def subscribe_callback(client, userdata, message):
    now = math.floor(time.time() * 1000)
    log.debug(f"Received message from topic: {message.topic}")
    payload_str = message.payload.decode('utf-8')
    payload = json.loads(payload_str)
    with open("output_files/data_size.txt", "a") as f:
        f.write(f'{len(payload_str)}\n')
    print(now)
    up_msg = payload.get("uplink_message")
    rx_metadata = up_msg.get("rx_metadata")[0]
    print(rx_metadata)
    gw_rx_time = rx_metadata.get("received_at")
    gw_rx_timetag = math.floor(isoparse(gw_rx_time).timestamp() * 1000)
    delta = now - gw_rx_timetag
    with open("output_files/legacy_delta_data.txt", "a") as f:
        f.write(f'{delta}\n')
    print(gw_rx_time)
    print(gw_rx_timetag)
    print(now)
    return None
    log.debug(f"Payload keys: {list(payload.keys())}")
    end_devices_infos = payload.get('end_device_ids')
    dev_eui = end_devices_infos.get('dev_eui')
    dev_addr = end_devices_infos.get('dev_addr')
    log.info(f"Dev EUI: {dev_eui}")
    log.info(f"Dev Addr: {dev_addr}")
    message = payload.get('uplink_message')
    frame_payload = message.get('frm_payload')
    # from base64 to string
    temperature = base64.b64decode(frame_payload)
    # temperature = temperature.decode('utf-8')
    log.info(f"Temperature: {temperature}")
    log.debug(f"Message keys: {message.keys()}")
    correlation_ids = payload.get('correlation_ids')
    log.debug(f"Correlation ids: {correlation_ids}")


def edge_callback(data):
    log.debug(f"Received data: {data}")
    return data


if __name__ == '__main__':
    log.info('Starting...')
    check_env_vars()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    edge2applicationserver_pb2_grpc.add_Edge2ApplicationServerServicer_to_server(
        Edge2LoRaApplicationServer(), server
        )
    server.add_insecure_port('[::]:50051')
    server.start()
    log.info('Started RPC server')

    log.debug("Connecting to MQTT broker...")
    mqqt_client = MQTTModule(username=os.getenv('MQTT_USERNAME'),
                             password=os.getenv('MQTT_PASSWORD'),
                             host=os.getenv('MQTT_HOST'),
                             port=int(os.getenv('MQTT_PORT')))
    log.debug("Connected to MQTT broker")

    topic = os.getenv('MQTT_TOPIC')
    log.debug(f"Subscribing to MQTT topic {topic}...")
    mqqt_client.subscribe_to_topic(topic=topic, callback=subscribe_callback)
    log.debug(f"Subscribed to MQTT topic {topic}")

    log.debug("Waiting for messages...")
    mqqt_client.wait_for_message()

    log.warning('Done, should never reach this point!')
