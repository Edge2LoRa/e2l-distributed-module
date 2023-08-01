import time
import math
from rpc_module.__private__ import edge2applicationserver_pb2_grpc
from rpc_module.__private__.edge2applicationserver_pb2 import NewDataResponse
from rpc_module.__private__.edge2applicationserver_pb2 import ResponseMessage


class Edge2LoRaApplicationServer(edge2applicationserver_pb2_grpc.Edge2ApplicationServerServicer):

    def __init__(self) -> None:
        super().__init__()
        self.e2gw_active_directory = {}

    def register_function(self, callback):
        self.data_received_callback = callback

    def store_e2gw_pub_info(self, request, context):
        ip_address = request.ip_address
        gw_pub_key = request.gw_pub_key
        self.e2gw_active_directory[ip_address] = {
            "pub_key": gw_pub_key,
        }
        print(self.e2gw_active_directory)
        return ResponseMessage(
            status_code=200,
            message="OK"
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
