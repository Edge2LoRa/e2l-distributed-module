import time
import math
from rpc_module.__private__ import edge2applicationserver_pb2_grpc
from rpc_module.__private__.edge2applicationserver_pb2 import NewDataResponse
from rpc_module.__private__.edge2applicationserver_pb2 import ResponseMessage


class Edge2LoRaApplicationServer(edge2applicationserver_pb2_grpc.Edge2ApplicationServerServicer):

    def __init__(self, e2l_module) -> None:
        super().__init__()
        self.e2l_module = e2l_module

    def register_function(self, callback):
        self.data_received_callback = callback

    def store_e2gw_pub_info(self, request, context):
        gw_rpc_endpoint_address = request.gw_ip_addr
        gw_rpc_endpoint_port = request.gw_port
        print("GW_RPC_ENDPOINT_ADDRESS: ", gw_rpc_endpoint_address)
        print("GW_RPC_ENDPOINT_PORT: ", gw_rpc_endpoint_port)

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
        data = request.name
        timetag = request.timetag

        delta = now - timetag

        # self.delta_time_array.append(delta)
        with open("output_files/e2lora_delta_data.txt", "a") as f:
            f.write(f'{delta}\n')

        return NewDataResponse(message="OK")
