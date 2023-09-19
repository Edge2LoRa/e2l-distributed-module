import os
import logging
import time
import math
from rpc_module.__private__ import edge2applicationserver_pb2_grpc
from rpc_module.__private__.edge2applicationserver_pb2 import ResponseMessage

DEBUG = os.getenv('DEBUG', False)
DEBUG = True if DEBUG == '1' else False
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

class Edge2LoRaApplicationServer(edge2applicationserver_pb2_grpc.Edge2ApplicationServerServicer):

    def __init__(self, e2l_module) -> None:
        super().__init__()
        self.e2l_module = e2l_module

    def register_function(self, callback):
        self.data_received_callback = callback

    def store_e2gw_pub_info(self, request, context):
        gw_rpc_endpoint_address = request.gw_ip_addr
        gw_rpc_endpoint_port = request.gw_port

        gw_pub_key_compressed = request.e2gw_pub_key
        ret = self.e2l_module.handle_gw_pub_info(gw_rpc_endpoint_address, gw_rpc_endpoint_port, gw_pub_key_compressed)
        if ret != 0:
            return ResponseMessage(
                status_code=500,
                message=b"Error"
            )
        return ResponseMessage(
            status_code=200,
            message= b"Success"
            )

    def new_data(self, request, context):
        now = math.floor(time.time() * 1000)
        gw_id = request.gw_id
        dev_eui = request.dev_eui
        dev_addr = request.dev_addr
        aggregated_data = request.aggregated_data
        timetag = request.timetag
        delta_time = now - timetag

        self.e2l_module.handle_edge_data(
            gw_id = gw_id,
            dev_eui = dev_eui,
            dev_addr = dev_addr,
            aggregated_data = aggregated_data,
            delta_time = delta_time
        )

        return ResponseMessage(status_code=0, message="OK")
